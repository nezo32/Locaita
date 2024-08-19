import os

import numpy as np
from agent import Agent
from buffer import ReplayBuffer

cwd = os.getcwd()
train_data_path = os.path.join(cwd, "tmp")
timestamp = os.listdir(train_data_path)[1].split("_")[1].split(".")[0]

memory = ReplayBuffer(8)
memory.load(timestamp)

print(f"\nDATA LENGTH - {memory.length()}")
print(f"REWARDS - min:{np.min(memory.rewards)} max:{np.max(memory.rewards)}\n")


agent = Agent((202, 260, 1), memory, n_epochs=10)
agent.load_models()

agent.learn()
agent.save_models()