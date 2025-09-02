
import torch
from time import sleep
import gymnasium as gym
from gymnasium import spaces

from locaita.log.logger import Logger
from locaita.modules.osu.context import Context
from locaita.modules.osu.states import PlayerState
from locaita.modules.osu.manager.mouse import MouseManager
from locaita.modules.osu.manager.beatmap import BeatmapManager, ModsHotkeys

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class Environment(gym.Env):
    def __init__(self, ctx: Context):
        self.ctx = ctx
        self.mouse_manager = MouseManager()
        self.beatmap_manager = BeatmapManager(ctx)

        self.properties = ctx.ScreenCTX.WindowProperties
        self.playarea = self.properties["play_area"]

        # swapping width and height in order to have tuple (height, width)
        self.downscaled_playarea = list(
            self.properties["downscaled_play_area"])
        self.downscaled_playarea[0], self.downscaled_playarea[1] = self.downscaled_playarea[1], self.downscaled_playarea[0]
        self.downscaled_playarea = tuple(self.downscaled_playarea)

        self.action_space: spaces.Discrete = spaces.Discrete(
            self.playarea["width"] * self.playarea["height"] * 4)
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(*self.downscaled_playarea, 1))

        self.previous_score = torch.tensor(0, device=device)
        self.previous_accuracy = torch.tensor(100.0, device=device)

    def __wait_for_state(self, state: PlayerState):
        retries = 0
        while self.ctx.GameCTX.GameState["state"] != state:
            if (retries // 4) > 10:
                Logger.Error(f"Wait for state {state} timeout")
                raise Exception(f"Wait for state {state} timeout")
            sleep(0.25)
            retries += 1

    def __perform_action(self, action: torch.Tensor):
        click, xy = divmod(action.item(), int(self.action_space.n // 4))
        y, x = divmod(xy, self.playarea["width"])

        self.mouse_manager.MouseClick(int(click))
        self.mouse_manager.MouseMove(
            int(x + self.playarea["left"]), int(y + self.playarea["top"]))

        left, right = self.mouse_manager.ButtonsState
        return torch.tensor([[left, right, x / self.playarea["width"], y / self.playarea["height"]]])

    def Step(self, action: torch.Tensor):
        new_controls = self.__perform_action(action)
        sleep(0.025)
        state = self.ctx.ScreenCTX.ScreenData
        data = self.ctx.GameCTX.GameState
        score, accuracy = torch.tensor(
            data["score"], device=device), torch.tensor(data["accuracy"], device=device)
        reward = self.GetReward(score, accuracy)
        self.previous_accuracy, self.previous_score = accuracy, score
        return state, new_controls, reward

    def Reset(self):
        self.mouse_manager.ResetButtons()
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

        self.previous_score = torch.tensor(0, device=device)
        self.previous_accuracy = torch.tensor(100.0, device=device)
        return torch.tensor([[0.5, 0.5, 0.0, 0.0]], device=device), torch.tensor(self.ctx.ScreenCTX.ScreenData, device=device)

    def GetReward(self, score, accuracy):
        if accuracy > self.previous_accuracy:
            bonus = torch.tensor(0.3, device=device)
        elif accuracy < self.previous_accuracy:
            bonus = torch.tensor(-0.3, device=device)
        else:
            bonus = torch.tensor(0.1, device=device)
        return torch.clamp(0.1*torch.log10(max((score - self.previous_score),
                                           torch.tensor(1.0, device=device))) + bonus, -1, 1)
