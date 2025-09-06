import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Normal


def conv2d_size_out(size, kernel_size=5, stride=2):
    return (size - (kernel_size - 1) - 1) // stride + 1


def sizeout(size):
    return conv2d_size_out(conv2d_size_out(conv2d_size_out(
        size, kernel_size=8, stride=4), kernel_size=4, stride=2), kernel_size=3, stride=1)


class FeatureExtractor(nn.Module):
    def __init__(self, width, height, controls, actions=None,
                 conv_out_features=256, controls_out_features=64, hidden_filters=256):
        super().__init__()

        self.conv_out_features = conv_out_features
        self.controls_out_features = controls_out_features
        self.hidden_filters = hidden_filters

        convw = sizeout(width)
        convh = sizeout(height)

        self.conv = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=8, stride=4),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, kernel_size=4, stride=2),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, stride=1),
            nn.ReLU(inplace=True),
            nn.Flatten(),

            nn.Linear(convw * convh * 64, conv_out_features),
            nn.ReLU(inplace=True)
        )

        self.controls = nn.Sequential(
            nn.Linear(controls, controls_out_features),
            nn.ReLU(inplace=True)
        )

        output_features = conv_out_features + controls_out_features + (actions if actions != None else 0)
        self.hidden1 = nn.Linear(in_features=output_features, out_features=hidden_filters)
        self.hidden2 = nn.Linear(in_features=hidden_filters, out_features=hidden_filters)

    def forward(self, state, control_state, actions=None):
        x = self.conv(state)
        y = self.controls(control_state)
        x = (torch.cat([x, y], dim=1) if actions == None else torch.cat([x, y, actions], dim=1))
        x = F.relu(self.hidden1(x))
        return F.relu(self.hidden2(x))


class ValueNetwork(nn.Module):
    def __init__(self, width, height, controls):
        super(ValueNetwork, self).__init__()
        self.extractor = FeatureExtractor(width, height, controls)

        self.value = nn.Linear(in_features=self.extractor.hidden_filters, out_features=1)

    def forward(self, state, control_state):
        features = self.extractor(state, control_state)
        return self.value(features)


class QvalueNetwork(nn.Module):
    def __init__(self, width, height, controls, actions):
        super(QvalueNetwork, self).__init__()
        self.extractor = FeatureExtractor(width, height, controls, actions)

        self.q_value = nn.Linear(in_features=self.extractor.hidden_filters, out_features=1)

    def forward(self, state, control_state, actions):
        x = self.extractor(state, control_state, actions)
        return self.q_value(x)


class PolicyNetwork(nn.Module):
    def __init__(self, width, height, controls, actions, action_bounds):
        super(PolicyNetwork, self).__init__()
        self.action_bounds = action_bounds
        self.extractor = FeatureExtractor(width, height, controls)

        self.mu = nn.Linear(in_features=self.extractor.hidden_filters, out_features=actions)
        self.log_std = nn.Linear(in_features=self.extractor.hidden_filters, out_features=actions)

    def forward(self, state, control_state):
        x = self.extractor(state, control_state)

        mu = self.mu(x)
        log_std = self.log_std(x)
        std = log_std.clamp(min=-20, max=2).exp()
        dist = Normal(mu, std)
        return dist

    def sample_or_likelihood(self, state, control_state):
        dist = self(state, control_state)
        # Reparameterization trick
        u = dist.rsample()
        action = torch.tanh(u)
        log_prob = dist.log_prob(value=u)
        # Enforcing action bounds
        log_prob -= torch.log(1 - action ** 2 + 1e-6)
        log_prob = log_prob.sum(-1, keepdim=True)
        return (action * self.action_bounds[1]).clamp_(self.action_bounds[0], self.action_bounds[1]), log_prob
