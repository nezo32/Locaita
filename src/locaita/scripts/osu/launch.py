import os
import subprocess
from locaita.log.logger import Logger
from locaita.scripts import CallableScript


class OsuLaunchScript(CallableScript):
    def _start(self):
        osu_path = os.getenv("OSU_PATH", "external/osu_game")
        try:
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


def main():
    OsuLaunchScript().Start()
