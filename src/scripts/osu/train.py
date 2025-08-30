from log.logger import Logger
from scripts import CallableScript
from locaita.modules.osu import OsuModule


class OsuTrainScript(CallableScript):
    def _start(self):
        OsuModule().Learn()


def main():
    OsuTrainScript().Start()
