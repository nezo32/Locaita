import torch
import torch.nn as nn


class CNN(nn.Module):
    def __init__(self, in_channels: int):
        super().__init__()
        self.model = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=8, stride=4),
            nn.LeakyReLU(inplace=True),
            nn.Conv2d(32, 64, kernel_size=4, stride=2),
            nn.LeakyReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, stride=1),
            nn.LeakyReLU(inplace=True),
            nn.Flatten()
        )

    def forward(self, x):
        return self.first(x)


class OsuNetwork(nn.Module):

    def __init__(self, screen_input_shape: tuple[int, int, int], actions_shape: int, control_shape: int):
        super().__init__()

        def conv2d_size_out(size, kernel_size=5, stride=2):
            return (size - (kernel_size - 1) - 1) // stride + 1

        convw = conv2d_size_out(conv2d_size_out(conv2d_size_out(
            screen_input_shape[1], kernel_size=8, stride=4), kernel_size=4, stride=2), kernel_size=3, stride=1)
        convh = conv2d_size_out(conv2d_size_out(conv2d_size_out(
            screen_input_shape[0], kernel_size=8, stride=4), kernel_size=4, stride=2), kernel_size=3, stride=1)

        self.cnn = CNN(screen_input_shape[2])
        self.fc1 = nn.Sequential(
            nn.Linear(convw * convh * 64, 1024),
            nn.LeakyReLU(inplace=True)
        )
        self.fc2 = nn.Sequential(
            nn.Linear(control_shape, 64),
            nn.LeakyReLU(inplace=True)
        )
        self.fc3 = nn.Linear(1024 + 64, actions_shape)

    def forward(self, state, control_state):
        x = self.cnn(state)
        x = self.fc1(x)
        y = self.fc2(control_state)
        y = torch.concat([x, y], dim=1)
        return self.fc3(y)
