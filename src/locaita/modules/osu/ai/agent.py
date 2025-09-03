
import os
import yaml
import torch
import datetime
from pathlib import Path
from typing import TypedDict
import torch.utils.tensorboard
from abc import ABC, abstractmethod

from locaita.log.logger import Logger
from locaita.modules.osu.ai.environment import Environment
from locaita.modules.osu.context import Context
from locaita.modules.osu.ai.network import OsuNetwork
from locaita.modules.osu.ai.memory import ReplayBuffer

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class Hyperparameters(TypedDict):
    learning_rate: float  # alpha
    discount_rate: float  # gamma

    steps_to_sync: int
    min_experience: int

    memory_capacity: int
    batch_size: int
    gradient_clipping_norm: float

    tensorboard_events_path: str
    weights_path: str
    memory_path: str


class BaseAgent:
    def __init__(self, inference: bool, hyperparameter_set: str):
        Logger.Info("Initizalizing base agent")

        self.hyperparameter_set = hyperparameter_set
        self.inference = inference
        with open('src/locaita/modules/osu/ai/hyperparameters.yml', 'r') as file:
            all_hyperparameter_sets = yaml.safe_load(file)
            self.hyperparams: Hyperparameters = all_hyperparameter_sets[hyperparameter_set]

        Path(self.hyperparams["tensorboard_events_path"]).mkdir(
            parents=True, exist_ok=True)
        Path(self.hyperparams["weights_path"]).mkdir(
            parents=True, exist_ok=True)
        Path(self.hyperparams["memory_path"]).mkdir(
            parents=True, exist_ok=True)

        date = datetime.datetime.now()
        self.date = date.strftime("%d-%m-%Y")

        self.memory: ReplayBuffer
        self.optimizer: torch.optim.Optimizer
        self.network: torch.nn.Module
        self.summary_writer: torch.utils.tensorboard.SummaryWriter

        self.version = 0
        while os.path.exists(f"{os.path.join(self.hyperparams['weights_path'],
                                self.__get_file("pt"))}"):
            self.version += 1

        if inference:
            self.version -= 1
        else:
            self.summary_writer = torch.utils.tensorboard.SummaryWriter(
                self.hyperparams["tensorboard_events_path"])

    def __get_file(self, extension: str):
        return f"osu-{self.hyperparameter_set}-{self.date}-{self.LastVersion}.{extension}"

    def FormatVersion(self, version: int):
        return f"{version:06d}"

    def ChangeVersion(self, version: int):
        self.version = version

    @property
    def LastVersion(self):
        return self.FormatVersion(self.version)

    def Save(self):
        Logger.Info(f"Saving data version {self.LastVersion}")
        torch.save({
            "opt": self.optimizer.state_dict(),
            "model": self.network.state_dict()
        }, os.path.join(self.hyperparams['weights_path'], self.__get_file("pt")))
        self.memory.Save(os.path.join(
            self.hyperparams['memory_path'], self.__get_file("pck")))
        Logger.Info(f"Data successfully saved")

    def ReplaceTarget(self):
        if hasattr(self, "target_network") and type(self.target_network) == torch.nn.Module:
            self.target_network.load_state_dict(self.network.state_dict())

    def Load(self):
        self.version -= 1
        Logger.Info(f"Loading saved data version {self.LastVersion}")
        state = torch.load(os.path.join(
            self.hyperparams['weights_path'], self.__get_file("pt")), weights_only=True)
        self.network.load_state_dict(state["model"])

        if not self.inference:
            self.optimizer.load_state_dict(state["opt"])
            self.memory = ReplayBuffer.Load(os.path.join(
                self.hyperparams['memory_path'], self.__get_file("pck")))
            self.ReplaceTarget()

        Logger.Info(f"Data successfully loaded")
        self.version += 1


class DDQN(BaseAgent):
    def __init__(self, ctx: Context, env: Environment, inference: bool):
        super().__init__(inference, "DDQN")
        self.env = env
        self.ctx = ctx

        Logger.Info("Initizalizing DDQN agent")
        (width,
         height) = ctx.ScreenCTX.WindowProperties["downscaled_play_area"]
        self.network = OsuNetwork(
            width, height, 1, env.action_space.n, env.control_space).to(device)

        if not inference:
            self.memory = ReplayBuffer(self.hyperparams["memory_capacity"])
            self.optimizer = torch.optim.Adam(
                self.network.parameters(), lr=self.hyperparams["learning_rate"])
            self.target_network = OsuNetwork(
                width, height, 1, env.action_space.n, env.control_space).to(device)
            self.ReplaceTarget()
            self.step = 0

            self.network.train()
            self.target_network.train()
        else:
            self.Load()
            self.network.eval()

        Logger.Info("DDQN agent successfully initialized")

    def SelectAction(self, state, controls_state):
        action: torch.Tensor = self.network(state, controls_state).detach()
        _, action = torch.max(action, 1)
        return action

    def Loss(self, input, target):
        return torch.clamp(torch.nn.functional.mse_loss(input, target), 0, 1.0)

    def Optimize(self):
        if len(self.memory) < self.hyperparams["min_experience"]:
            return
        state, action, reward, new_state, control_state, new_control_state = self.memory.Sample(
            self.hyperparams["batch_size"])

        state = torch.tensor(state, device=device)
        action = torch.tensor(action, device=device)
        reward = torch.tensor(reward, device=device)
        new_state = torch.tensor(new_state, device=device)
        control_state = torch.tensor(control_state, device=device)
        new_control_state = torch.tensor(new_control_state, device=device)

        s = self.network(state, control_state)
        state_action_values = torch.stack(
            [s[i, action[i]] for i in range(self.hyperparams["batch_size"])])
        next_state_values = self.target_network(
            new_state, new_control_state).detach().max(1)[0]
        expected_state_action_values = reward + \
            self.hyperparams["discount_rate"] * next_state_values
        loss = self.Loss(state_action_values, expected_state_action_values)

        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            self.network.parameters(), self.hyperparams["gradient_clipping_norm"])
        self.optimizer.step()

        with torch.no_grad():
            self.tensorboard.add_scalar(
                "loss", torch.mean(loss), self.step)
            self.tensorboard.add_scalar(
                "rewards", torch.mean(reward), self.step)
            self.step += 1
