
import torch
import pyautogui
import numpy as np
from time import sleep
import gymnasium as gym

from locaita.log.logger import Logger
from locaita.modules.osu.context import Context
from locaita.modules.osu.states import PlayerState
from locaita.modules.osu.manager.mouse import MouseManager
from locaita.modules.osu.manager.beatmap import BeatmapManager, ModsHotkeys

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class Environment(gym.Env):
    def __init__(self, ctx: Context):
        self.ctx = ctx
        self.beatmap_manager = BeatmapManager(ctx)
        self.mouse_manager = MouseManager

    def __wait_for_state(self, state: PlayerState):
        retries = 0
        while self.ctx.GameCTX.GameState["state"] != state:
            if (retries // 4) > 10:
                Logger.Error(f"Wait for state {state} timeout")
                raise Exception(f"Wait for state {state} timeout")
            sleep(0.25)
            retries += 1

    def reset(self):
        self.beatmap_manager.ToBeatmapList()
        self.beatmap_manager.ClearMods()
        self.beatmap_manager.SelectMods([ModsHotkeys.NF])
        self.beatmap_manager.SearchMaps(stars={"s_from": 1, "s_to": 2, "full_range": True},
                                        length={"s_from": 90, "s_to": 180, "full_range": False})
        self.beatmap_manager.ShuffleMaps()
        self.beatmap_manager.EnterMap()
        self.__wait_for_state(PlayerState.PLAYING)
        sleep(1)
        self.beatmap_manager.SkipMapBegining()
