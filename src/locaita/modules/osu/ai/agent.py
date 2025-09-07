
import os
import math
import yaml
import torch
import datetime
from pathlib import Path
from torch.optim import Adam
from typing import TypedDict
from torchviz import make_dot
import torch.utils.tensorboard

from locaita.log.logger import Logger
from locaita.modules.osu.context import Context
from locaita.modules.osu.ai.memory import ReplayBuffer
from locaita.modules.osu.ai.environment import Environment
from locaita.modules.osu.ai.network import PolicyNetwork, QvalueNetwork, ValueNetwork

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class Hyperparameters(TypedDict):
    learning_rate: float  # alpha
    reward_gamma: float
    reward_scale: float
    alpha: float

    min_experience: int
    learn_loops: int

    memory_capacity: int
    batch_size: int

    tensorboard_events_path: str
    weights_path: str
    memory_path: str


class BaseAgent:
    def __init__(self, inference: bool):
        Logger.Info("Initizalizing base agent")

        self.inference = inference
        with open('hyperparameters.yml', 'r') as file:
            self.hyperparams: Hyperparameters = yaml.safe_load(file)

        Path(self.hyperparams["tensorboard_events_path"]).mkdir(parents=True, exist_ok=True)
        Path(self.hyperparams["weights_path"]).mkdir(parents=True, exist_ok=True)
        Path(self.hyperparams["memory_path"]).mkdir(parents=True, exist_ok=True)

        date = datetime.datetime.now()
        self.date = date.strftime("%d-%m-%Y")

        self.memory: ReplayBuffer
        self.summary_writer: torch.utils.tensorboard.SummaryWriter

        self.version = 0
        while os.path.exists(f"{os.path.join(self.hyperparams['weights_path'], self.GetFileName("pt"))}"):
            self.version += 1

        if inference:
            self.version -= 1
        else:
            self.summary_writer = torch.utils.tensorboard.SummaryWriter(
                self.hyperparams["tensorboard_events_path"])

    def GetFileName(self, extension: str | None = None):
        return f"osu-{self.date}-{self.LastVersion}{f".{extension}" if extension != None else ""}"

    def FormatVersion(self, version: int):
        return f"{version:06d}"

    def ChangeVersion(self, version: int):
        self.version = version

    @property
    def LastVersion(self):
        return self.FormatVersion(self.version)


class OsuAgent(BaseAgent):
    def __init__(self, ctx: Context, env: Environment, inference: bool):
        super().__init__(inference)
        self.env = env
        self.ctx = ctx

        Logger.Info("Initizalizing agent")
        (width, height) = ctx.ScreenCTX.WindowProperties["downscaled_play_area"]
        self.policy_network = PolicyNetwork(
            width=width, height=height, controls=env.control_space, actions=env.action_space.shape[0]).to(device)

        # init test
        output = self.policy_network(torch.from_numpy(ctx.ScreenCTX.ScreenData).unsqueeze_(0).to(
            device), torch.tensor([[0.5, 0.5, 0.0, 0.0]], dtype=torch.float32).to(device))
        del output

        if not inference:
            self.memory = ReplayBuffer(self.hyperparams["memory_capacity"])

            self.q_value_network1 = QvalueNetwork(
                width=width, height=height, controls=env.control_space, actions=env.action_space.shape[0]).to(device)
            self.q_value_network2 = QvalueNetwork(
                width=width, height=height, controls=env.control_space, actions=env.action_space.shape[0]).to(device)
            self.value_network = ValueNetwork(width=width, height=height, controls=env.control_space).to(device)
            self.value_target_network = ValueNetwork(width=width, height=height, controls=env.control_space).to(device)

            self.value_opt = Adam(self.value_network.parameters(), lr=self.hyperparams["learning_rate"])
            self.q_value1_opt = Adam(self.q_value_network1.parameters(), lr=self.hyperparams["learning_rate"])
            self.q_value2_opt = Adam(self.q_value_network2.parameters(), lr=self.hyperparams["learning_rate"])
            self.policy_opt = Adam(self.policy_network.parameters(), lr=self.hyperparams["learning_rate"])

            self.log_alpha = torch.zeros(1, requires_grad=True, device=device)
            self.alpha_opt = torch.optim.Adam([self.log_alpha], lr=1e-4)
            self.target_entropy = -env.action_space.shape[0]

            self.step = 0

            self.value_loss = torch.nn.MSELoss()
            self.q_value_loss = torch.nn.MSELoss()

            self.q_value_network1.train()
            self.q_value_network2.train()
            self.value_network.train()
            self.value_target_network.train()
            self.policy_network.train()
        else:
            self.Load()
            self.policy_network.eval()

        Logger.Info("Agent successfully initialized")

    def Save(self):
        Logger.Info(f"Saving data version {self.LastVersion}")
        torch.save({
            "policy": {
                "opt": self.policy_opt.state_dict(),
                "model": self.policy_network.state_dict(),
            },
            "q_value_1": {
                "opt": self.q_value1_opt.state_dict(),
                "model": self.q_value_network1.state_dict(),
            },
            "q_value_2": {
                "opt": self.q_value2_opt.state_dict(),
                "model": self.q_value_network2.state_dict(),
            },
            "value": {
                "opt": self.value_opt.state_dict(),
                "model": self.value_target_network.state_dict(),
            },
            "alpha": self.alpha_opt.state_dict()
        }, os.path.join(self.hyperparams['weights_path'], self.GetFileName("pt")))
        """ self.memory.Save(os.path.join(
            self.hyperparams['memory_path'], self.GetFileName("pck"))) """
        Logger.Info(f"Data successfully saved")

    def Load(self, downgrade=False, load_optmizers=True):
        if downgrade:
            self.version -= 1

        Logger.Info(f"Loading saved data version {self.LastVersion} at {os.path.join(
            self.hyperparams['weights_path'], self.GetFileName("pt"))}")

        if not os.path.exists(os.path.join(
                self.hyperparams['weights_path'], self.GetFileName("pt"))):
            Logger.Warning("No saved data found")
            return

        state = torch.load(os.path.join(
            self.hyperparams['weights_path'], self.GetFileName("pt")), weights_only=True)

        self.policy_network.load_state_dict(state["policy"]["model"])

        if not self.inference:
            self.policy_opt.load_state_dict(state["policy"]["opt"])

            self.q_value_network1.load_state_dict(state["q_value_1"]["model"])
            self.q_value_network2.load_state_dict(state["q_value_2"]["model"])
            self.value_network.load_state_dict(state["value"]["model"])
            self.value_target_network.load_state_dict(state["value"]["model"])

            if load_optmizers:
                self.q_value1_opt.load_state_dict(state["q_value_1"]["opt"])
                self.q_value2_opt.load_state_dict(state["q_value_2"]["opt"])
                self.value_opt.load_state_dict(state["value"]["opt"])
                self.alpha_opt.load_state_dict(state["alpha"])

            """ self.memory = ReplayBuffer.Load(os.path.join(
                self.hyperparams['memory_path'], self.GetFileName("pck"))) """

        Logger.Info(f"Data successfully loaded")

        if downgrade:
            self.version += 1

    def SelectAction(self, state: torch.Tensor, controls_state: torch.Tensor):
        action, _ = self.policy_network.sample_or_likelihood(
            state.to(device), controls_state.to(device))
        return action.cpu()

    def Optimize(self, loops: int):
        if len(self.memory) < self.hyperparams["min_experience"]:
            return

        for _ in range(loops):
            state, action, reward, new_state, control_state, new_control_state = self.memory.Sample(
                self.hyperparams["batch_size"])

            state = state.to(device)
            action = action.to(device)
            reward = reward.to(device).unsqueeze(1)
            new_state = new_state.to(device)
            control_state = control_state.to(device)
            new_control_state = new_control_state.to(device)

            reparam_actions, log_probs = self.policy_network.sample_or_likelihood(state, control_state)

            alpha_loss = -(self.log_alpha * (log_probs.detach() + self.target_entropy)).mean()

            self.alpha_opt.zero_grad()
            alpha_loss.backward()
            self.alpha_opt.step()

            alpha = self.log_alpha.exp()

            q1 = self.q_value_network1(state, control_state, reparam_actions)
            q2 = self.q_value_network2(state, control_state, reparam_actions)
            q = torch.min(q1, q2)

            target_value = q.detach() - alpha.detach() * log_probs.detach()
            value = self.value_network(state, control_state)
            value_loss = self.value_loss(value, target_value)

            with torch.no_grad():
                target_q = self.hyperparams["reward_scale"] * reward + \
                    self.hyperparams["reward_gamma"] * self.value_target_network(new_state, new_control_state)

            q1 = self.q_value_network1(state, control_state, action)
            q2 = self.q_value_network2(state, control_state, action)
            q1_loss = self.q_value_loss(q1, target_q)
            q2_loss = self.q_value_loss(q2, target_q)
            policy_loss = (alpha.detach() * log_probs - q).mean()

            self.policy_opt.zero_grad()
            policy_loss.backward()
            self.policy_opt.step()

            self.value_opt.zero_grad()
            value_loss.backward()
            self.value_opt.step()

            self.q_value1_opt.zero_grad()
            q1_loss.backward()
            self.q_value1_opt.step()

            self.q_value2_opt.zero_grad()
            q2_loss.backward()
            self.q_value2_opt.step()

            self.soft_update_target_network(self.value_network, self.value_target_network)
            with torch.no_grad():
                self.summary_writer.add_scalar(
                    f"{self.GetFileName()}/policy-loss", torch.mean(policy_loss), self.step)
                self.summary_writer.add_scalar(
                    f"{self.GetFileName()}/value-loss", torch.mean(value_loss), self.step)
                self.summary_writer.add_scalar(
                    f"{self.GetFileName()}/q1-loss", torch.mean(q1_loss), self.step)
                self.summary_writer.add_scalar(
                    f"{self.GetFileName()}/q2-loss", torch.mean(q2_loss), self.step)
                self.summary_writer.add_scalar(
                    f"{self.GetFileName()}/alpha-loss", torch.mean(alpha_loss), self.step)
                self.summary_writer.add_scalar(
                    f"{self.GetFileName()}/rewards", torch.mean(reward), self.step)
                self.summary_writer.add_histogram(
                    f"{self.GetFileName()}/actions", reparam_actions, self.step)
                self.summary_writer.add_histogram(
                    f"{self.GetFileName()}/log_probs", log_probs, self.step)
                self.step += 1

    @staticmethod
    def soft_update_target_network(local_network: torch.nn.Module, target_network: torch.nn.Module, tau=0.005):
        for target_param, local_param in zip(target_network.parameters(), local_network.parameters()):
            target_param.data.copy_(tau * local_param.data + (1 - tau) * target_param.data)
