import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Normal


class FeatureExtractor(nn.Module):
    def __init__(self, width, height, controls, actions=None, hidden_filters=256):
        super().__init__()
        self.hidden_filters = hidden_filters

        self.conv1 = nn.Conv2d(in_channels=1, out_channels=32, kernel_size=5, stride=2, padding=2)
        self.conv2 = nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3, stride=2, padding=1)
        self.conv3 = nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3, stride=2, padding=1)
        self.conv4 = nn.Conv2d(in_channels=128, out_channels=256, kernel_size=3, stride=1, padding=1)

        self._feature_size = self._get_conv_output((1, 173, 130))

        output_features = self._feature_size + controls + (actions if actions != None else 0)
        self.hidden1 = nn.Linear(in_features=output_features, out_features=hidden_filters)
        self.hidden2 = nn.Linear(in_features=hidden_filters, out_features=hidden_filters)

    def _get_conv_output(self, shape):
        with torch.no_grad():
            x = torch.zeros(1, *shape)
            x = F.relu(self.conv1(x))
            x = F.relu(self.conv2(x))
            x = F.relu(self.conv3(x))
            x = F.relu(self.conv4(x))
            output_size = x.numel()
        return output_size

    def forward(self, state, control_state, actions=None):
        x = F.relu(self.conv1(state))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        x = F.relu(self.conv4(x))
        x = x.view(x.size(0), -1)

        x = (torch.cat([x, control_state], dim=1) if actions ==
             None else torch.cat([x, control_state, actions], dim=1))
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
    def __init__(self, width, height, controls, actions):
        super(PolicyNetwork, self).__init__()
        self.extractor = FeatureExtractor(width, height, controls)

        self.mu = nn.Linear(in_features=self.extractor.hidden_filters, out_features=actions)
        self.log_std = nn.Linear(in_features=self.extractor.hidden_filters, out_features=actions)

    def forward(self, state, control_state):
        x = self.extractor(state, control_state)

        mu = self.mu(x)
        log_std = self.log_std(x)
        std = log_std.clamp(min=-20, max=2).exp()
        return mu, std

    def sample_or_likelihood(self, state, control_state):
        mu, std = self(state, control_state)
        dist = Normal(mu, std)
        # Reparameterization trick
        u = dist.rsample()
        tanh_u = torch.tanh(u)
        action = 0.5 * (tanh_u + 1.0)
        log_prob = dist.log_prob(value=u)
        # correction
        log_prob -= torch.log(1 - tanh_u.pow(2) + 1e-6)
        log_prob = log_prob.sum(-1, keepdim=True)
        return action, log_prob
