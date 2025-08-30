from time import sleep

from locaita.modules.osu.context import Context


class OsuModule:
    def __init__(self):
        pass

    def Learn(self):
        with Context() as ctx:
            while ctx.GameCTX.isClientConnected:

                sleep(0.01)
