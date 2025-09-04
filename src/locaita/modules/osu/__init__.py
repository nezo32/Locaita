import gc
import os
import threading
import subprocess
from random import random

import torch
from locaita.log.logger import Logger
from locaita.modules.osu.ai.agent import DDQN
from locaita.modules.osu.context import Context
from locaita.modules.osu.states import PlayerState
from locaita.modules.osu.ai.environment import Environment


class OsuModule:
    def __init__(self):
        pass

    def StartGame(self):
        osu_path = os.getenv("OSU_PATH", "external/osu_game")
        try:
            Logger.Info("Starting osu!lazer")
            result = subprocess.run(
                ["dotnet", "run", "--project",
                    os.path.join(osu_path, "osu.Desktop")],
                capture_output=True,
                text=True,
                check=True
            )
            with open("logs/osu_game.log", "w") as file:
                file.write(result.stdout)
                Logger.Info(f"osu!lazer log saved to: {file.name}")

        except subprocess.CalledProcessError as e:
            Logger.Error(f"Error calling .NET: {e.stderr}")
        except FileNotFoundError:
            Logger.Error(
                "Error: 'dotnet' command not found. Ensure .NET is installed")

    def Inference(self):
        raise NotImplementedError()

    def __params_count(self, model: torch.nn.Module):
        return sum(p.numel() for p in model.parameters())

    def Learn(self):
        with Context() as ctx:
            MAPS_COUNT = 0

            env = Environment(ctx)
            agent = DDQN(ctx, env, inference=False)

            """ 
                For osu! window with resolution of 1280x720 and downscale multiplier of 15
                there is 4.878.144.448 parameters. Not very good action space optimization
                if using discrete actions space. Consider move to predict mu and sigma for
                Normal distibution on screen
            """
            Logger.Info(
                f"Parameters count: {self.__params_count(agent.network) + self.__params_count(agent.target_network)}")

            steps = 0
            best_reward = -999999999.9
            epsilon = agent.hyperparams["epsilon_init"]
            epsilon_decay = agent.hyperparams["epsilon_decay"]
            epsilon_min = agent.hyperparams["epsilon_min"]
            for _ in range(MAPS_COUNT):
                state, controls_state = env.Reset()
                episode_reward = 0.0
                while ctx.GameCTX.GameState["state"] == PlayerState.PLAYING:
                    if steps > agent.hyperparams["min_experience"]:
                        if random() > epsilon:
                            with torch.no_grad():
                                action = agent.SelectAction(
                                    state, controls_state)
                        else:
                            action = torch.tensor(
                                [env.action_space.sample()])
                    else:
                        action = torch.tensor([env.action_space.sample()])

                    new_state, new_controls_state, reward = env.Step(action)

                    episode_reward += reward.item()

                    agent.memory.Push(state, action, reward, new_state,
                                      controls_state, new_controls_state)

                    state = new_state
                    controls_state = new_controls_state

                    steps += 1

                epsilon = max(epsilon * epsilon_decay, epsilon_min)
                env.ResetAfter()
                Logger.Info(
                    f"Map ended. Steps performed: {steps}, episode reward: {episode_reward}")

                agent.Optimize()
                if steps % agent.hyperparams["steps_to_sync"] == 0:
                    agent.ReplaceTarget()

                gc.collect()

                if episode_reward > best_reward:
                    agent.Save()
                    best_reward = episode_reward
