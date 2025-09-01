import os
import subprocess
from time import sleep
from locaita.log.logger import Logger
from locaita.modules.osu.context import Context
from locaita.modules.osu.manager.beatmap import BeatmapManager, ModsHotkeys


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

    def Learn(self):
        with Context() as ctx:
            bm = BeatmapManager(ctx.ScreenCTX, ctx.GameCTX)
            bm.ToBeatmapList()
            bm.SearchMaps(stars={"s_from": 1, "s_to": 1},
                          length={"s_from": 90, "s_to": 180})
            bm.ClearMods()
            bm.SelectMods([ModsHotkeys.DC, ModsHotkeys.FL, ModsHotkeys.EZ])
            # bm.EnterRandomMap()
            """ while ctx.GameCTX.isClientConnected:
                ctx.ScreenCTX.ScreenData
                sleep(0.05) """
