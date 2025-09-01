from enum import Enum
import pyautogui as py
from time import sleep
from locaita.log.logger import Logger
from typing import Optional, TypedDict
from pynput.keyboard import Controller, Key
from locaita.modules.osu.states import PlayerState
from locaita.modules.osu.context.game import GameContext
from locaita.modules.osu.context.screen import ScreenContext


class RangeSearch(TypedDict):
    s_from: int
    s_to: int


class ModsHotkeys(Enum):
    EZ = "q"
    NF = "w"
    HF = "e"
    DC = "r"

    HR = "a"
    DT = "f"
    NC = "g"
    HD = "h"
    FL = "j"


def ActivateOsuWindow(func):
    def wrapper(*args, **kwargs):
        self: BeatmapManager = args[0]
        window = self.sCTX.Window
        if hasattr(window, "activate"):
            window.activate()
        return func(*args, **kwargs)
    return wrapper


def CheckState(check_state: PlayerState):
    def decorator(function):
        def wrapper(*args, **kwargs):
            self: BeatmapManager = args[0]
            state = self.gCTX.GameState["state"]
            if state != check_state:
                Logger.Error(
                    f'Invalid player state: {state.name}. Expected: {check_state.name}')
                raise Exception("Invalid player state")
            return function(*args, **kwargs)
        return wrapper
    return decorator


class BeatmapManager:
    def __init__(self, sCTX: ScreenContext, gCTX: GameContext):
        self.controller = Controller()
        self.sCTX = sCTX
        self.gCTX = gCTX

    def __click(self, x=None, y=None, clicks=1, interval=0.5):
        for _ in range(clicks):
            py.mouseDown(x, y)
            sleep(0.05)
            py.mouseUp()
            sleep(interval)

    def __timeout(self):
        sleep(0.2)

    def __press_button(self, button: Key):
        self.controller.press(button)
        self.__timeout()
        self.controller.release(button)

    def __getRange(self, key: str, range: Optional[RangeSearch] = None, with_floats=False):
        if range == None:
            return ""
        return f"{key}>{range['s_from']}{".01" if with_floats else ""} {key}<{range["s_to"]}{".99" if with_floats else ""}"

    @ActivateOsuWindow
    @CheckState(PlayerState.SONG_SELECT)
    def SearchMaps(self, raw_search: Optional[str] = None, stars: Optional[RangeSearch] = None, length: Optional[RangeSearch] = None):
        search = raw_search if raw_search != None else f"{self.__getRange("stars", stars, True)} {self.__getRange("length", length)}"
        Logger.Info(f'Searching maps with: {search}')

        # Clearing search input
        self.controller.type("a")
        self.__press_button(Key.esc)

        self.__timeout()
        self.controller.type(search)

    @ActivateOsuWindow
    @CheckState(PlayerState.SONG_SELECT)
    def ShuffleMaps(self):
        Logger.Info(f'Shuffle maps')
        self.__timeout()

    @ActivateOsuWindow
    @CheckState(PlayerState.SONG_SELECT)
    def EnterMap(self):
        Logger.Info(f'Entering the map')
        self.__press_button(Key.enter)

    @ActivateOsuWindow
    @CheckState(PlayerState.SONG_SELECT)
    def SwitchOpenMods(self):
        self.__press_button(Key.f1)
        self.__timeout()

    @ActivateOsuWindow
    @CheckState(PlayerState.SONG_SELECT)
    def ClearMods(self):
        Logger.Info(f'Clearing all mods')
        self.SwitchOpenMods()
        self.__press_button(Key.tab)
        self.__timeout()
        self.__press_button(Key.backspace)
        self.__timeout()
        self.SwitchOpenMods()

    @ActivateOsuWindow
    @CheckState(PlayerState.SONG_SELECT)
    def SelectMods(self, mods: list[ModsHotkeys]):
        m = []
        for mod in mods:
            m.append(mod.name)
        Logger.Info(f"Selecting mods: {", ".join(m)}")

        self.SwitchOpenMods()
        self.__press_button(Key.tab)

        for mod in mods:
            self.controller.type(mod.value)
            self.__timeout()

        self.SwitchOpenMods()

    @ActivateOsuWindow
    def ToBeatmapList(self):
        Logger.Info("Moving to beatmap list")
        window = self.sCTX.WindowProperties["window"]
        x = window["left"] + window["width"] // 2
        y = window["top"] + window["height"] // 2

        state = self.gCTX.GameState["state"]
        if state == PlayerState.SONG_SELECT:
            Logger.Info("Already on beatmap list. Skipping")
            self.__click(x, y, clicks=1, interval=0.2)
            return
        elif state == PlayerState.RESULT_SCREEN:
            self.__click(x, y, clicks=1, interval=0.2)
            self.__press_button(Key.esc)
            return
        elif state != PlayerState.MAIN_MENU:
            Logger.Error("Not on main menu or result screen")
            raise Exception("Unable to move to beatmap list")

        self.__click(x, y, clicks=4, interval=0.2)
