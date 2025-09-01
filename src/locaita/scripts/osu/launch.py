from locaita.modules.osu import OsuModule
from locaita.scripts import CallableScript


class OsuLaunchScript(CallableScript):
    def _start(self):
        OsuModule().StartGame()


def main():
    OsuLaunchScript().Start()
