from locaita.modules.osu import OsuModule
from scripts import CallableScript


class OsuTrainScript(CallableScript):
    def _start(self):
        module = OsuModule()
        module.Learn()


def main():
    OsuTrainScript().Start()
