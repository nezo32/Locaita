import psutil
import numpy as np
from time import sleep

from osu.memory import OsuMemory
from osu.routines import OsuRoutines
from osu.window import OsuWindow

class OsuManager():
    def __init__(self, windowed = False):
        self.__findAttemptCount = 0
        while "osu!.exe" not in (i.name() for i in psutil.process_iter()):
            if (self.__findAttemptCount >= 5):
                raise Exception("Osu! process wasn't found!")
            self.__findAttemptCount += 1
            print(f"... cannot find osu! Attempt {self.__findAttemptCount} ...")
            sleep(10)
        
        self.Memory = OsuMemory()
        self.Window = OsuWindow(windowed)
        self.Routines = OsuRoutines()
    
    def __del__(self):
        del self.Routines
        del self.Window
        del self.Memory