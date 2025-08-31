import os
import re
import cv2
import mss
import threading
import contextlib
import numpy as np
from time import sleep, time
from abc import ABC, abstractmethod
from typing import TypedDict, override
from log.logger import Logger
from utils.threads import ThreadedClass
from locaita.polyfills.desktop import getWindowsWithTitle


class WindowPropertiesMonitor(TypedDict):
    width: int
    height: int
    top: int
    left: int


class WindowProperties(TypedDict):
    downscaled_play_area: tuple[int, int]
    play_area: WindowPropertiesMonitor


class Screen:
    class ScreenTaker(ABC):
        def __init__(self, downscale_multiplier=5):
            super().__init__()
            self.downscale_multiplier = downscale_multiplier
            self.offset_top, self.offset_left, self.offset_cut_bottom = 0, 0, 0

            self.__initializeOffsets()

        @property
        @abstractmethod
        def Data(self):
            pass

        def __initializeOffsets(self):
            offsets = os.getenv("OSU_WINDOW_OFFSET", "0,0")
            if not bool(re.match(r'\d+,\d+(,\d+)?', offsets)):
                raise Exception(f"Invalid window offset format: {offsets}")
            offsets = [int(offset) for offset in offsets.split(",")]

            if len(offsets) == 2:
                self.offset_top, self.offset_left = offsets
            elif len(offsets) == 3:
                self.offset_top, self.offset_left, self.offset_cut_bottom = offsets

        def __get_playfield_rect(self, win_w: int, win_h: int, win_x: int = 0, win_y: int = 0, scale: float = 0.90):
            ar_window = win_w / win_h
            ar_playfield = 4 / 3

            if ar_window >= ar_playfield:
                pf_h = win_h * scale
                pf_w = pf_h * ar_playfield
                pf_x = win_x + (win_w - pf_w) / 2
                pf_y = win_y + (win_h - pf_h) / 2
            else:
                pf_w = win_w * scale
                pf_h = pf_w * 3 / 4
                pf_x = win_x + (win_w - pf_w) / 2
                pf_y = win_y + (win_h - pf_h) / 2

            return int(pf_w), int(pf_h), int(pf_x), int(pf_y)

        def GetWindowProperties(self) -> WindowProperties:
            window = getWindowsWithTitle("osu!")[0]
            windowed = not window.isMinimized and not window.isMaximized

            width, height, top, left = \
                window.width + (- self.offset_left * 2 if windowed else 0), \
                window.height + (- self.offset_top - self.offset_cut_bottom if windowed else 0), \
                window.top + self.offset_top, \
                window.left + self.offset_left

            play_area_width, play_area_height, play_area_left, play_area_top = self.__get_playfield_rect(
                width, height, left, top)

            downscaled_width, downscaled_height = (
                play_area_width // self.downscale_multiplier, play_area_height // self.downscale_multiplier)

            return {
                "play_area": {
                    "top": play_area_top,
                    "left": play_area_left,
                    "width": play_area_width,
                    "height": play_area_height
                },
                "downscaled_play_area": (downscaled_width, downscaled_height)
            }

        def TransformImage(self, window: WindowProperties, image) -> np.ndarray:
            # To grayscale
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            # Scale down
            image = cv2.resize(image, window["downscaled_play_area"],
                               interpolation=cv2.INTER_AREA)
            # Normalization
            image = np.expand_dims(np.asarray(image, dtype=int) / 255, axis=-1)
            Logger.Debug(f"Tranformed image shape: {image.shape}")

    class Grab(ScreenTaker):
        def __init__(self, downscale_multiplier=5):
            super().__init__(downscale_multiplier)
            self.sct = mss.mss()

        @property
        def Data(self):
            window = self.GetWindowProperties()
            return self.TransformImage(window,
                                       np.array(self.sct.grab(window["play_area"])))

        def Stop(self):
            self.sct.close()
            cv2.destroyAllWindows()

    class Capture(ThreadedClass, ScreenTaker):
        def __init__(self, fps=60):
            super().__init__()

            self.fps = fps
            self.frame_delta = 1 / fps

            self.ready_lock = threading.Lock()
            self.is_ready = False
            self.__thread_data: np.ndarray

        @property
        def Data(self):
            with self.lock:
                return self.__thread_data

        def _ThreadTarget(self):
            with mss.mss() as sct:
                with self.ready_lock:
                    self.is_ready = True
                next_frame = time()
                while not self.cancellation_token.IsCancelled():
                    next_frame += self.frame_delta
                    window = self.GetWindowProperties()
                    image = self.TransformImage(window,
                                                np.array(sct.grab(window["play_area"])))
                    with self.lock:
                        self.__thread_data = image

                    wait_ms = max(int((next_frame - time()) * 1000), 1)
                    if (cv2.waitKey(wait_ms) % 256) == ord('\\'):
                        break

        def _ThreadStart(self):
            pass

        def _ThreadStop(self):
            self.cancellation_token.Cancel()
            cv2.destroyAllWindows()


class ScreenContext(contextlib.AbstractContextManager["ScreenContext"]):
    def __init__(self):
        self.__st: Screen.Grab | Screen.Capture = Screen.Grab()

    @property
    def ScreenData(self):
        return self.__st.Data

    @override
    def __enter__(self):
        if type(self.__st) is not Screen.Capture:
            return

        self.__st.Start()
        retries = 0
        while not self.__st.is_ready and retries < 10:
            sleep(1)

        return super().__enter__()

    @override
    def __exit__(self, exc_type, exc_value, traceback):
        self.__st.Stop()
