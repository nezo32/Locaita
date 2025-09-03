from locaita.modules.osu import OsuModule
from locaita.scripts import CallableScript

MAPS_TO_LEARN = 3


class OsuTrainScript(CallableScript):
    def _start(self):
        OsuModule().Learn(maps_count=MAPS_TO_LEARN)


def main():
    OsuTrainScript().Start()
