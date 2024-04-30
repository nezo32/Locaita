import os
from agent import Agent
from buffer import ReplayBuffer
from constants import ACTIONS_COUNT

cwd = os.getcwd()
train_data_path = os.path.join(cwd, "tmp")
timestamp = os.listdir(train_data_path)[0].split("_")[1].split(".")[0]

memory = ReplayBuffer(64)
memory.load("1714353254")

agent = Agent(ACTIONS_COUNT, (202, 260, 1), memory, n_epochs=50)
agent.load_models()

agent.learn()
agent.save_models()