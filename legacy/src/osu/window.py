import cv2
import math
import numpy as np
import torch
import win32gui
from mss import mss

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class OsuWindow():
    def __init__(self, windowed=False):
        self.__windowed = windowed
        self.__getOsuWindow()
        self.__sct = mss()

    def Update(self):
        self.__getOsuWindow()

    def GrabScreen(self, downscale_multiplier=5, downscale_to: tuple[int, int] | None = None):
        bounding_box = {'top': self.y, 'left': self.x,
                        'width': self.width, 'height': self.height}
        sct_img = self.__sct.grab(bounding_box)
        grayed = cv2.cvtColor(np.array(sct_img), cv2.COLOR_BGR2GRAY)

        downscale = downscale_to
        if downscale_to is None:
            downscale = (math.floor(self.playground_width / downscale_multiplier),
                         math.floor(self.playground_height / downscale_multiplier))
        resized = cv2.resize(grayed, downscale)

        output = np.expand_dims(np.asarray(resized, dtype=int) / 255, axis=-1)
        return sct_img, grayed, resized, output

    def GrabPlayground(self, downscale_multiplier=5, downscale_to: tuple[int, int] | None = None):
        bounding_box = {'top': self.playground_y, 'left': self.playground_x,
                        'width': self.playground_width, 'height': self.playground_height}
        sct_img = self.__sct.grab(bounding_box)
        grayed = cv2.cvtColor(np.array(sct_img), cv2.COLOR_BGR2GRAY)

        downscale = downscale_to
        if downscale_to is None:
            downscale = (self.playground_width // downscale_multiplier + 1,
                         self.playground_height // downscale_multiplier + 1)
        resized = cv2.resize(grayed, downscale)

        output = np.expand_dims(np.asarray(resized, dtype=int) / 255, axis=-1)
        output = torch.tensor(output, device=device)
        return sct_img, grayed, resized, output

    def __getOsuWindow(self):
        self.__WINDOWED_Y_OFFSET = 0
        self.__WINDOWED_X_OFFSET = 0

        if self.__windowed:
            self.__WINDOWED_Y_OFFSET = 27
            self.__WINDOWED_X_OFFSET = 7

        self.__hwnd = win32gui.FindWindow(None, "osu! (development)")
        self.__rect = win32gui.GetWindowRect(self.__hwnd)
        self.x = self.__rect[0] + self.__WINDOWED_X_OFFSET
        self.y = self.__rect[1] + self.__WINDOWED_Y_OFFSET
        self.width = self.__rect[2] - self.x - self.__WINDOWED_X_OFFSET
        self.height = self.__rect[3] - self.y - self.__WINDOWED_Y_OFFSET

        self.playground_x = self.x + 311
        self.playground_y = self.y + 32
        self.playground_width = self.width - 311 * 2
        self.playground_height = self.height - 28

        if self.__windowed:
            self.width += 2
            self.height += 24

    def __del__(self):
        self.__sct.close()
