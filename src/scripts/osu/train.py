from scripts import CallableScript
from locaita.modules.osu import OsuModule


class OsuTrainScript(CallableScript):
    def _start(self):
        module = OsuModule()
        module.Learn()


def main():
    OsuTrainScript().Start()
