from locaita.modules.osu import OsuModule
from locaita.scripts import CallableScript


class OsuInferenceScript(CallableScript):
    def _start(self):
        OsuModule().Inference()


def main():
    OsuInferenceScript().Start()
