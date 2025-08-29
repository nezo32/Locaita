import contextlib
from typing_extensions import override
import psutil
import numpy as np
from time import sleep

from osu.memory import OsuMemory
from osu.routines import OsuRoutines
from osu.window import OsuWindow


class OsuManager(contextlib.AbstractContextManager["OsuManager"]):
    def __init__(self, windowed=False):
        self.__findAttemptCount = 0
        while "osu!.exe" not in (i.name() for i in psutil.process_iter()):
            if (self.__findAttemptCount >= 5):
                raise Exception("Osu! process wasn't found!")
            self.__findAttemptCount += 1
            print(
                f"... cannot find osu! Attempt {self.__findAttemptCount} ...")
            sleep(10)

        sleep(10)

        self.Memory = OsuMemory()
        self.Window = OsuWindow(windowed)
        self.Routines = OsuRoutines()

    @override
    def __enter__(self):
        _ = self.Memory.__enter__()
        return super().__enter__()

    @override
    def __exit__(self, exc_type, exc_value, traceback):
        if hasattr(self, "Routines"):
            del self.Routines
        if hasattr(self, "Window"):
            del self.Window
        if hasattr(self, "Memory"):
            self.Memory.__exit__(exc_type, exc_value, traceback)
