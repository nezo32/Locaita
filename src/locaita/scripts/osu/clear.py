from locaita.modules.osu import OsuModule
from locaita.scripts import CallableScript


class OsuClearScript(CallableScript):
    def _start(self):
        OsuModule().Clear()


def main():
    OsuClearScript().Start()
