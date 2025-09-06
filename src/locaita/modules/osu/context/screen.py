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

from locaita.log.logger import Logger
from locaita.utils.threads import ThreadedClass
from locaita.polyfills.desktop import getWindowsWithTitle


class WindowPropertiesMonitor(TypedDict):
    width: int
    height: int
    top: int
    left: int


class WindowProperties(TypedDict):
    downscaled_play_area: tuple[int, int]
    play_area: WindowPropertiesMonitor
    window: WindowPropertiesMonitor
    downscale_multiplier: int


class Screen:
    class ScreenTaker(ABC):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.offset_top, self.offset_left, self.offset_cut_bottom = 0, 0, 0
            is_preview_setted = os.getenv(
                "OSU_WINDOW_PREVIEW", "NONE") == "SHOW"
            self.ShowPreview = self.__preview if is_preview_setted else self.__empty
            if is_preview_setted:
                Logger.Info("Preview will be displayed")
            self.__initializeOffsets()

        @property
        @abstractmethod
        def Data(self):
            pass

        def __empty(self, *args, **kwargs):
            pass

        def __preview(self, image):
            cv2.imshow("Preview", image)

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

        def GetWindow(self):
            return getWindowsWithTitle("osu!")[0]

        def GetWindowProperties(self) -> WindowProperties:
            window = self.GetWindow()
            windowed = not window.isMinimized and not window.isMaximized

            width, height, top, left = \
                window.width + (- self.offset_left * 2 if windowed else 0), \
                window.height + (- self.offset_top - self.offset_cut_bottom if windowed else 0), \
                window.top + self.offset_top, \
                window.left + self.offset_left

            play_area_width, play_area_height, play_area_left, play_area_top = self.__get_playfield_rect(
                width, height, left, top)

            downscaled_width, downscaled_height = (173, 130)
            self.downscale_multiplier = play_area_width // (
                downscaled_width - 1)

            return {
                "window": {
                    "width": width,
                    "height": height,
                    "top": top,
                    "left": left
                },
                "play_area": {
                    "width": play_area_width,
                    "height": play_area_height,
                    "top": play_area_top,
                    "left": play_area_left
                },
                "downscale_multiplier": self.downscale_multiplier,
                "downscaled_play_area": (downscaled_width, downscaled_height)
            }

        def TransformImage(self, window: WindowProperties, image) -> np.ndarray:
            # To grayscale
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            # Scale down
            image = cv2.resize(image, window["downscaled_play_area"],
                               interpolation=cv2.INTER_AREA)
            # Normalization
            image = np.expand_dims(np.asarray(image, dtype=int) / 255, axis=0)
            Logger.Debug(f"Tranformed image shape: {image.shape}")
            return image

    class Grab(ScreenTaker):
        def __init__(self):
            super().__init__()
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
            super().__init__(name="ScreenCapture")

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
                while not self.cancellation_token.is_set():
                    next_frame += self.frame_delta
                    window = self.GetWindowProperties()
                    image = np.array(sct.grab(window["play_area"]))
                    self.ShowPreview(image)
                    image = self.TransformImage(window, image)
                    with self.lock:
                        self.__thread_data = image

                    wait_ms = max(int((next_frame - time()) * 1000), 1)
                    cv2.waitKey(wait_ms)

        def _ThreadStart(self):
            pass

        def _ThreadStop(self):
            sleep(0.5)
            cv2.destroyAllWindows()


class ScreenContext(contextlib.AbstractContextManager["ScreenContext"]):
    def __init__(self):
        self.__st: Screen.Grab | Screen.Capture = Screen.Grab()

    @property
    def ScreenData(self):
        return np.float32(self.__st.Data)

    @property
    def WindowProperties(self):
        return self.__st.GetWindowProperties()

    @property
    def Window(self):
        return self.__st.GetWindow()

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
