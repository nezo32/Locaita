import time
import pyautogui
from threading import Thread
from typing import Literal, NamedTuple
from pyclick.humancurve import HumanCurve
from pynput.mouse import Controller, Button
from pyclick.humanclicker import HumanClicker

MouseButtonsState = NamedTuple("MouseButtonsState", [
    ("left", bool), ("right", bool)])


class MouseManager:
    def __init__(self):
        self.__humanClicker = HumanClicker()
        self.__mouse = Controller()

        self.__thread = None
        self.__leftButton = False
        self.__rightButton = False

    def __getCurve(self, x, y, target_points=10):
        return HumanCurve(pyautogui.position(), (x, y), targetPoints=target_points)

    @property
    def ButtonsState(self) -> MouseButtonsState:
        return self.__leftButton, self.__rightButton

    @property
    def MousePosition(self):
        return pyautogui.position()

    def ResetButtons(self):
        self.MouseClick(0)

    def MouseClick(self, click: float):
        if click < 0.25:
            self.__mouse.release(Button.left)
            self.__mouse.release(Button.right)
            self.__leftButton, self.__rightButton = False, False
        elif click < 0.5:
            self.__mouse.press(Button.left)
            self.__mouse.release(Button.right)
            self.__leftButton, self.__rightButton = True, False
        elif click < 0.75:
            self.__mouse.release(Button.left)
            self.__mouse.press(Button.right)
            self.__leftButton, self.__rightButton = False, True
        else:
            self.__mouse.press(Button.left)
            self.__mouse.press(Button.right)
            self.__leftButton, self.__rightButton = True, True

    def MoveClick(self, x, y, click):
        self.MouseClick(click)
        self.MouseMove(x, y)

    def MouseMove(self, x, y, t=0.05):
        time.sleep(0.005)
        self.__thread = Thread(target=self.__mouseMoveThread, args=[x, y, t])
        self.__thread.start()

    def __mouseMoveThread(self, x, y, t):
        self.__humanClicker.move((x, y), t, self.__getCurve(x, y))
