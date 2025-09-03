import gc
import os
from random import random
import subprocess
import threading
from time import sleep

import torch
from locaita.log.logger import Logger
from locaita.modules.osu.ai.agent import DDQN
from locaita.modules.osu.ai.scheduler import LinearSchedule
from locaita.modules.osu.context import Context
from locaita.modules.osu.ai.environment import Environment
from locaita.modules.osu.states import PlayerState


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

    def Learn(self, maps_count: int):
        SCHEDULE_TIMESTAMP = 4000000
        INITIAL_P = 1.0
        FINAL_P = 0.05

        with Context() as ctx:
            env = Environment(ctx)
            agent = DDQN(ctx, env, inference=False)
            scheduler = LinearSchedule(SCHEDULE_TIMESTAMP, FINAL_P, INITIAL_P)

            steps = 0
            for _ in range(maps_count):
                state, controls_state = env.Reset()
                thread = None
                while ctx.GameCTX.GameState["state"] == PlayerState.PLAYING:
                    with torch.no_grad():
                        """ if steps > agent.hyperparams["min_experience"]:
                            if random() > scheduler.value(steps):
                                action = agent.SelectAction(
                                    state, controls_state)
                            else:
                                action = torch.tensor(
                                    [env.action_space.sample()])
                        else:
                            action = torch.tensor([env.action_space.sample()]) """
                        action = agent.SelectAction(state, controls_state)

                        new_state, new_controls_state, reward = env.Step(
                            action)
                        th = threading.Thread(target=agent.memory.Push,
                                              args=(state, action, reward, new_state, controls_state, new_controls_state))
                        th.start()

                    if thread is not None and type(thread) == threading.Thread:
                        thread.join()
                    thread = threading.Thread(target=agent.Optimize)
                    thread.start()

                    state = new_state
                    controls_state = new_controls_state

                env.ResetAfter()
                gc.collect()

                if steps % agent.hyperparams["steps_to_sync"] == 0:
                    agent.ReplaceTarget()

                agent.Save()
