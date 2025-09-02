from enum import Enum
from PIL import Image
import pyautogui as py
from time import sleep
from typing import Optional, TypedDict
from pynput.keyboard import Controller, Key

from locaita.log.logger import Logger
from locaita.modules.osu.context import Context
from locaita.modules.osu.states import PlayerState


class RangeSearch(TypedDict):
    s_from: int | float
    s_to: int | float
    full_range: bool


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
        window = self.ctx.ScreenCTX.Window
        if hasattr(window, "activate"):
            window.activate()
        return func(*args, **kwargs)
    return wrapper


def CheckState(check_state: PlayerState):
    def decorator(function):
        def wrapper(*args, **kwargs):
            self: BeatmapManager = args[0]
            state = self.ctx.GameCTX.GameState["state"]
            if state != check_state:
                Logger.Error(
                    f'Invalid player state: {state.name}. Expected: {check_state.name}')
                raise Exception("Invalid player state")
            return function(*args, **kwargs)
        return wrapper
    return decorator


class BeatmapManager:
    def __init__(self, ctx: Context):
        self.controller = Controller()
        self.ctx = ctx
        self.skipImage = Image.open(
            "src/locaita/modules/osu/manager/images/skip.jpg")

    def __click(self, x=None, y=None, clicks=1, interval=0.5):
        for _ in range(clicks):
            py.mouseDown(x, y)
            sleep(0.05)
            py.mouseUp()
            sleep(interval)

    def __timeout(self, timeout=0.3):
        sleep(timeout)

    def __press_button(self, button: Key):
        self.controller.press(button)
        self.__timeout()
        self.controller.release(button)

    def __getRange(self, key: str, range: Optional[RangeSearch] = None):
        if range == None:
            return ""
        return f"{key}>{range['s_from']}{".01" if range['full_range'] == True else ""} {key}<{range["s_to"]}{".99" if range['full_range'] == True else ""}"

    @ActivateOsuWindow
    @CheckState(PlayerState.PLAYING)
    def SkipMapBegining(self):
        try:
            box = py.locateOnScreen(self.skipImage, confidence=0.8)
            if box != None:
                self.__press_button(Key.space)
        except:
            pass

    @ActivateOsuWindow
    @CheckState(PlayerState.SONG_SELECT)
    def SearchMaps(self, raw_search: Optional[str] = None, **kwargs: RangeSearch):
        """
        Useful range filters: ar, cs, od, hp, stars, length

        https://osu.ppy.sh/wiki/en/Beatmap_search
        """
        kwargs_search = []
        for key, value in kwargs.items():
            kwargs_search.append(self.__getRange(key, value))
        search = raw_search if raw_search != None else f"{" ".join(kwargs_search)}"
        Logger.Info(f'Searching maps with: {search}')

        # Clearing search input
        self.controller.type("a")
        self.__press_button(Key.esc)
        self.__timeout()

        self.controller.type(search)
        self.__timeout(2)

    @ActivateOsuWindow
    @CheckState(PlayerState.SONG_SELECT)
    def ShuffleMaps(self):
        Logger.Info(f'Shuffle maps')
        self.__press_button(Key.f2)
        self.__timeout(2)

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
        window = self.ctx.ScreenCTX.WindowProperties["window"]
        x = window["left"] + window["width"] // 2
        y = window["top"] + window["height"] // 2

        state = self.ctx.GameCTX.GameState["state"]
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

        self.__click(x, y, clicks=4, interval=0.4)
