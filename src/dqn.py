from environment import OsuEnv
from network import OsuNetwork
import torch
from torch.utils.tensorboard import SummaryWriter
from utils.memory import ReplayBuffer

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class DQNAgent():
    def __init__(self, batch_size: int, max_memory_size: int,
                 screen_input_shape: tuple[int, int, int], action_input_shape: int, control_shape: int, min_experience: int,
                 gamma: float, learning_rate: float, gradient_clipping_norm=10.0,
                 load_memory_path: str | None = None, load_model_path: str | None = None,
                 ):
        # Memory
        self.batch_size = batch_size

        if load_memory_path is not None:
            self.memory: ReplayBuffer = ReplayBuffer.load(load_memory_path)
        else:
            self.memory = ReplayBuffer(max_memory_size)

        # Shapes
        self.screen_input_shape = screen_input_shape
        self.control_shape = control_shape
        self.action_input_shape = action_input_shape

        # Networks
        self.network = OsuNetwork(screen_input_shape, action_input_shape,
                                  control_shape).to(device)
        self.target_network = OsuNetwork(screen_input_shape,
                                         action_input_shape, control_shape).to(device)
        if load_model_path is not None:
            self.load(load_model_path)

        # Train params
        self.optimizer = torch.optim.RMSprop(
            params=self.network.parameters(), lr=learning_rate, eps=0.01, alpha=0.95)
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.min_experience = min_experience
        self.gradient_clipping_norm = gradient_clipping_norm

        # Summary
        self.tensorboard = SummaryWriter("./tensorboard", "main")
        self.step = 0

    def loss_function(self, y_true, y_pred):
        # Clamped MSE
        return torch.clamp(torch.mean(torch.square(y_true - y_pred)), 0, 1.0)

    def select_action(self, state, controls_state):
        action: torch.Tensor = self.network(state, controls_state).detach()
        _, action = torch.max(action, 1)
        return action

    def random_action(self, x_discrete, y_discrete, click_dim=4):
        # Normal distribution mean=0.5, clipped in [0, 1[ & uniform distrib
        x = self.noise()
        action = torch.tensor([int(x[0] * x_discrete) + x_discrete * int(
            x[1] * y_discrete) + x_discrete * y_discrete * int(x[2] * click_dim)], device=device)
        return action

    def save(self, filepath, memory_path):
        torch.save({
            "opt": self.optimizer.state_dict(),
            "model": self.network.state_dict()
        }, filepath)
        print(f"Model data saved to: {filepath}")
        self.memory.save(memory_path)
        print(f"Memory data saved to: {memory_path}")

    def load(self, filepath):
        state = torch.load(filepath, weights_only=True)
        self.optimizer.load_state_dict(state["opt"])
        self.network.load_state_dict(state["model"])
        for target_param, param in zip(self.target_network.parameters(), self.network.parameters()):
            target_param.data.copy_(param.data)
        print(f"Model data loaded from: {filepath}")

    def optimize(self):
        if len(self.memory) < self.min_experience:
            return
        s1, a1, r1, s2, c_s1, c_s2 = self.memory.sample()
        q: torch.Tensor = self.network(s1, c_s1)
        state_action_values = torch.stack(
            [q[i, a1[i]] for i in range(self.batch_size)])
        next_state_values = self.target_network(s2, c_s2).detach().max(1)[0]
        expected_state_action_values = r1 + self.gamma * next_state_values
        loss = self.loss_function(
            state_action_values, expected_state_action_values)

        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            self.network.parameters(), self.gradient_clipping_norm)
        self.optimizer.step()

        with torch.no_grad():
            self.tensorboard.add_scalar(
                "loss", torch.mean(loss), self.step)
            self.tensorboard.add_scalar(
                "rewards", torch.mean(r1), self.step)
            self.step += 1
