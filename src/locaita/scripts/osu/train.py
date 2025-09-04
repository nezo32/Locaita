from locaita.modules.osu import OsuModule
from locaita.scripts import CallableScript


class OsuTrainScript(CallableScript):
    def _start(self):
        OsuModule().Learn()


def main():
    OsuTrainScript().Start()
