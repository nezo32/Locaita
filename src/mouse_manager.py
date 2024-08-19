from threading import Thread
import pyautogui
from pyclick.humancurve import HumanCurve
from pyclick.humanclicker import HumanClicker

def mouseMoveThread(x, y, t, curve, clicker: HumanClicker):
    clicker.move((x, y), t, curve)

class MouseManager():
    def __init__(self):
        self.__humanClicker = HumanClicker()
        self.thread: Thread | None = None
        
        self.__leftButton = 0.0
        self.__rightButton = 0.0
    
    def __getCurve(self, x, y, target_points = 10):
        return HumanCurve(pyautogui.position(), (x, y), targetPoints=target_points)
    
    def GetButtonsState(self):
        return self.__leftButton, self.__rightButton

    def GetMousePosition(self):
        return pyautogui.position()
    
    def Reset(self):
        self.MouseClick(0)
    
    def MouseClick(self, click):
        if click == 0:
            pyautogui.mouseUp(button="left")
            pyautogui.mouseUp(button="right")
            self.__leftButton, self.__rightButton = 0.0, 0.0
        elif click == 1:
            pyautogui.mouseDown(button="left")
            pyautogui.mouseUp(button="right")
            self.__leftButton, self.__rightButton = 1.0, 0.0
        elif click == 2:
            pyautogui.mouseUp(button="left")
            pyautogui.mouseDown(button="right")
            self.__leftButton, self.__rightButton = 0.0, 1.0        
    
    def MouseMove(self, x, y, t = 0.05):
        curve = self.__getCurve(x, y)
        if self.thread is not None:
            self.thread.join()
        self.thread = Thread(target=mouseMoveThread, args=[x, y, t, curve, self.__humanClicker])
        self.thread.start()
    
    def __del__(self):
        if self.thread is not None:
            self.thread.join()
        del self.__humanClicker
        