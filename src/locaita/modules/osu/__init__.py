import gc
import os
import shutil
import threading
from time import sleep
import traceback
import subprocess

import torch
from locaita.log.logger import Logger
from locaita.modules.osu.context import Context
from locaita.modules.osu.ai.agent import OsuAgent
from locaita.modules.osu.states import PlayerState
from locaita.modules.osu.ai.environment import Environment


class OsuModule:
    def __init__(self):
        pass

    def Clear(self):
        Logger.Info("Clearing memory, checkpoints, tensorboard events")
        try:
            shutil.rmtree("memory")
        except Exception as e:
            Logger.Error(f"Error occured while clearing memory: {e} / {traceback.format_exc()}")
        try:
            shutil.rmtree("tensorboard")
        except Exception as e:
            Logger.Error(f"Error occured while clearing tensorboard events: {e} / {traceback.format_exc()}")
        try:
            shutil.rmtree("weights")
        except Exception as e:
            Logger.Error(f"Error occured while clearing weights checkpoints: {e} / {traceback.format_exc()}")

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
        with Context() as ctx:
            env = Environment(ctx)
            agent = OsuAgent(ctx, env, inference=True)
            state, controls_state = env.Reset()
            while ctx.GameCTX.GameState["state"] == PlayerState.PLAYING:
                with torch.no_grad():
                    action = agent.SelectAction(
                        state, controls_state)
                    env.Step(action)

    def __params_count(self, model: torch.nn.Module):
        return sum(p.numel() for p in model.parameters())

    def Learn(self):
        Logger.Info("Training will start in 5 seconds")
        sleep(5)
        with Context() as ctx:
            MAPS_COUNT = 50

            env = Environment(ctx)
            agent = OsuAgent(ctx, env, inference=False)
            agent.Load(downgrade=True)

            Logger.Info(
                f"Window info: {ctx.ScreenCTX.WindowProperties["window"]}")
            Logger.Info(
                f"Play area info: {ctx.ScreenCTX.WindowProperties["play_area"]}")
            policy_count = self.__params_count(agent.policy_network)
            Logger.Info(
                f"Parameters count for train: {policy_count + self.__params_count(agent.value_network) + self.__params_count(agent.value_target_network) + self.__params_count(agent.q_value_network1) + self.__params_count(agent.q_value_network2)}")

            for _ in range(MAPS_COUNT):
                state, controls_state = env.Reset()

                steps = 0
                while ctx.GameCTX.GameState["state"] == PlayerState.PLAYING:
                    with torch.no_grad():
                        action = agent.SelectAction(
                            state, controls_state)
                        new_state, new_controls_state, reward = env.Step(action)

                    agent.memory.Push(state, action, reward, new_state,
                                      controls_state, new_controls_state)

                    state = new_state
                    controls_state = new_controls_state

                    steps += 1
                env.ResetAfter()
                Logger.Info(
                    f"Map ended. Steps performed: {steps}")

                agent.Optimize(loops=steps)

                gc.collect()

                agent.Save()
