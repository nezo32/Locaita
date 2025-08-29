import time
import numpy as np
import torch
import pyautogui
from utils import helper
from utils.mouse_manager import MouseManager
from osu.manager import OsuManager
import gymnasium as gym

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class OsuEnv(gym.Env):
    def __init__(self, mouse_manager: MouseManager, osu_manager: OsuManager, star_rating: int,
                 width: int, height: int, depth: int,
                 discrete_width: int, discrete_height: int, discrete_factor: int
                 ):
        super().__init__()
        self.mouse_manager = mouse_manager
        self.osu_manager = osu_manager
        self.star_rating = star_rating

        self.action_space = gym.spaces.Discrete(
            discrete_height * discrete_width * discrete_factor)
        self.observation_space = gym.spaces.Box(
            low=0, high=1, shape=(discrete_height, discrete_width, depth))

        self.width = width
        self.height = height
        self.discrete_width = discrete_width
        self.discrete_height = discrete_height
        self.discrete_factor = discrete_factor

        self.previous_accuracy: torch.Tensor | None = None
        self.previous_score: torch.Tensor | None = None
        self.history: torch.Tensor | None = None

    def reset(self):
        helper.move_to_songs()
        time.sleep(0.5)
        helper.find_maps(self.star_rating)
        helper.reset_mods()
        helper.enable_mods()
        helper.launch_random_beatmap()

        x, y = pyautogui.center((0, 0, 1920, 1080))
        self.mouse_manager.MouseMove(x, y, 0)
        self.mouse_manager.Reset()
        self.previous_accuracy = 100.0

        _, _, _, state = self.osu_manager.Window.GrabPlayground(
            self.discrete_factor)
        self.history = torch.cat([state])
        _, _, _, state = self.osu_manager.Window.GrabPlayground(
            self.discrete_factor)
        self.history = torch.cat((self.history, state), 0)
        self.previous_score = torch.tensor(0.0, device=device)
        self.previous_accuracy = torch.tensor(100.0, device=device)

        return torch.tensor([[0.5, 0.5, 0.0, 0.0]], device=device), self.history.unsqueeze(0)

    def step(self, action, steps):
        new_controls_state = self.perform_action(action, self.hc)
        for i in range(len(self.history)-1):
            self.history[i] = self.history[i+1]
        # TODO: maybe try threading every actions that can be if i need to win some time.
        time.sleep(0.025)
        hits = self.osu_manager.Memory.GetHitsData()
        score, acc = hits["score"], hits["accuracy"]
        if (steps < 15 and score == -1) or (score - self.previous_score > 5 * (self.previous_score + 100)):
            score = self.previous_score
        if steps < 15 and acc == -1:
            acc = self.previous_accuracy
        done = (score == -1)
        if self.history[-1, 1, 1] > 0.0834 and steps > 25:
            done = True
            reward = torch.tensor(-1.0, device=device)
        else:
            reward = self.get_reward(score, acc)  # TODO: remove step?
        self.previous_accuracy = acc
        self.previous_score = score

        return self.history.unsqueeze(0), new_controls_state, reward, done

    def observe(self, steps, dt=1/(9.0*3)):  # Obsoltete
        time.sleep(dt)
        x, y = pyautogui.position()
        left, right = self.mouse_manager.GetButtonsState()
        controls_state = torch.tensor(
            [[left, right, x / self.width, y / self.height]], device=device)
        for i in range(len(self.history)-1):
            self.history[i] = self.history[i+1]
        # TODO: maybe try threading every actions that can be if i need to win some time.
        _, _, _, img = self.osu_manager.Window.GrabPlayground(
            self.discrete_factor)
        self.history[-1] = img
        hits = self.osu_manager.Memory.GetHitsData()
        score, acc = hits["score"], hits["accuracy"]
        if (steps < 15 and score == -1) or (score - self.previous_score > 5 * (self.previous_score + 100)):
            score = self.previous_score
        if steps < 15 and acc == -1:
            acc = self.previous_accuracy
        done = (score == -1)
        if self.history[-1, 1, 1] > 0.0834 and steps > 25:
            done = True
            reward = torch.tensor(-1.0, device=device)
        else:
            reward = self.get_reward(score, acc)  # TODO: remove step?
        self.previous_accuracy = acc
        self.previous_score = score

        if left and right:
            v = 3
        elif right:
            v = 2
        elif left:
            v = 1
        else:
            v = 0

        action = torch.tensor(v * (self.discrete_width * self.discrete_height) + int((y/self.height) *
                              self.discrete_height) * self.discrete_width + int((x / self.width) * self.discrete_width), device=device)
        return action, self.history.unsqueeze(0), controls_state, reward, done

    def perform_action(self, action):
        click, xy = divmod(
            action.item(), self.discrete_width * self.discrete_height)
        y_disc, x_disc = divmod(xy, self.discrete_width)
        self.mouse_manager.MouseClick(click)
        x = x_disc * self.discrete_factor + 145
        y = y_disc * self.discrete_factor + 54 + 26

        self.mouse_manager.MouseMove(x, y)
        left, right = self.mouse_manager.GetButtonsState()
        return torch.tensor([[left, right, x / self.width, y / self.height]], device=device)

    def calculate_reward(self, score, acc):
        if acc > self.previous_accuracy:
            bonus = torch.tensor(0.3, device=device)
        elif acc < self.previous_accuracy:
            bonus = torch.tensor(-0.3, device=device)
        else:
            bonus = torch.tensor(0.1, device=device)
        return torch.clamp(0.1*torch.log10(max((score - self.previous_score),
                                           torch.tensor(1.0, device=device))) + bonus, -1, 1)
