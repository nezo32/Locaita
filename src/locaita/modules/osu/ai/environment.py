
import torch
from time import sleep
from gymnasium import spaces

from locaita.log.logger import Logger
from locaita.modules.osu.context import Context
from locaita.modules.osu.states import PlayerState
from locaita.modules.osu.manager.mouse import MouseManager
from locaita.modules.osu.manager.beatmap import BeatmapManager, ModsHotkeys


class Environment:
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

        self.control_space = 4
        self.action_space = spaces.Box(low=0, high=1, shape=(3, ))

        self.previous_score = torch.tensor(0, dtype=torch.float32)
        self.previous_accuracy = torch.tensor(100, dtype=torch.float32)

    def __wait_for_state(self, state: PlayerState):
        retries = 0
        while self.ctx.GameCTX.GameState["state"] != state:
            if (retries // 4) > 10:
                Logger.Error(f"Wait for state {state} timeout")
                raise Exception(f"Wait for state {state} timeout")
            sleep(0.25)
            retries += 1

    def PerformAction(self, action: torch.Tensor):
        x, y, click = action[0].tolist()

        self.mouse_manager.MoveClick(
            int(x * self.playarea["width"] + self.playarea["left"]), int(y * self.playarea["height"] + self.playarea["top"]), click)

        left, right = self.mouse_manager.ButtonsState
        return torch.tensor([[left, right, x, y]], dtype=torch.float32)

    def RandomAction(self):
        return torch.tensor([self.action_space.sample()])

    def Step(self, action: torch.Tensor):
        new_controls = self.PerformAction(action)
        sleep(0.025)
        state = self.ctx.ScreenCTX.ScreenData
        data = self.ctx.GameCTX.GameState
        score, accuracy = torch.tensor(
            data["score"], dtype=torch.float32), torch.tensor(data["accuracy"], dtype=torch.float32)
        reward = self.GetReward(score, accuracy)
        self.previous_accuracy, self.previous_score = accuracy, score
        return torch.from_numpy(state).unsqueeze_(0), new_controls, reward

    def Reset(self):
        self.mouse_manager.ResetButtons()
        self.beatmap_manager.ToBeatmapList()
        """ UNSTABLE """
        """ self.beatmap_manager.ClearMods()
        self.beatmap_manager.SelectMods([ModsHotkeys.NF]) """
        self.beatmap_manager.SearchMaps(stars={"s_from": 1, "s_to": 3, "full_range": True},
                                        length={"s_from": 0, "s_to": 150, "full_range": False})
        self.beatmap_manager.ShuffleMaps()
        self.beatmap_manager.EnterMap()
        self.__wait_for_state(PlayerState.PLAYING)
        sleep(1)
        self.beatmap_manager.SkipMapBegining()

        self.previous_score = torch.tensor(0)
        self.previous_accuracy = torch.tensor(100.0)
        return torch.from_numpy(self.ctx.ScreenCTX.ScreenData).unsqueeze_(0), torch.tensor([[0.5, 0.5, 0.0, 0.0]], dtype=torch.float32)

    def ResetAfter(self):
        self.beatmap_manager.BackToBeatmapList()

    def GetReward(self, score: torch.Tensor, accuracy: torch.Tensor):
        delta_score = score - self.previous_score
        score_reward = delta_score / 100_000

        delta_accuracy = accuracy - self.previous_accuracy
        accuracy_reward = delta_accuracy * 1.5

        reward = score_reward + accuracy_reward - 0.1

        return reward.clip(0.0, 1.0)
