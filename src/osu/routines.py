import pyautogui
from time import sleep
from PIL import Image
from threading import Thread, Event

GLOBAL_THREADS_TERMINATE = Event()

def detectActualStart(event: Event, img):
    global GLOBAL_THREADS_TERMINATE
    while(True):
        if GLOBAL_THREADS_TERMINATE.is_set():
            break
        try:
            pyautogui.locateOnScreen(img, confidence=0.95)
            event.set()
        finally:
            continue

# TODO: locate caption on capturing screen
def detectFailedThread(event: Event, img):
    global GLOBAL_THREADS_TERMINATE
    while(True):
        if GLOBAL_THREADS_TERMINATE.is_set():
            break
        
        try:
            pyautogui.locateOnScreen(img, confidence=0.7)
            event.set()
            sleep(0.5)
        except Exception:
            event.clear()
            sleep(0.5)

class OsuRoutines():
    def __init__(self):
        self.FAIL_IS_DETECTED = Event()
        self.ACTUAL_START = Event()
        
        self.__failedImage = Image.open('status/failed.png')
        self.__timerImage = Image.open('status/timer.png')
        
        self.threads = [ \
            Thread(target=detectFailedThread, args=[self.FAIL_IS_DETECTED, self.__failedImage]), \
            Thread(target=detectActualStart, args=[self.ACTUAL_START, self.__timerImage]), \
        ]
        for thread in self.threads:
            thread.start()
    
    def __del__(self):
        GLOBAL_THREADS_TERMINATE.set()
        for thread in self.threads:
            thread.join()