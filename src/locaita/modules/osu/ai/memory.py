import random
import torch
import pickle
from collections import namedtuple

Transition = namedtuple('Transition', ('state', 'action', 'reward',
                        'next_state', 'control_state', 'next_control_state'))


class ReplayBuffer:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.memory = []
        self.position = 0

    def Push(self, *args: torch.Tensor):
        if len(self.memory) < self.capacity:
            self.memory.append(None)
        self.memory[self.position] = Transition(args[0].squeeze(0), args[1].squeeze(
            0), args[2], args[3].squeeze(0), args[4].squeeze(0), args[5].squeeze(0))
        self.position = (self.position + 1) % self.capacity

    def Sample(self, batch_size):
        batch = random.sample(self.memory, batch_size)
        s = torch.stack([a[0] for a in batch])
        a = torch.stack([a[1] for a in batch])
        r = torch.stack([a[2] for a in batch])
        s1 = torch.stack([a[3] for a in batch])
        c_s = torch.stack([a[4] for a in batch])
        c_s1 = torch.stack([a[5] for a in batch])
        return s, a, r, s1, c_s, c_s1

    def Save(self, path: str):
        f = open(path, 'wb')
        pickle.dump(self, f)
        f.close()

    @staticmethod
    def Load(path: str):
        with open(path, "rb") as file:
            return pickle.load(file)

    def __len__(self):
        return len(self.memory)
