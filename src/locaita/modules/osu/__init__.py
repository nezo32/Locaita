from time import sleep
from locaita.modules.osu.context.game import GameContext


class OsuModule:
    def __init__(self):
        pass

    def Learn(self):
        with GameContext() as ctx:
            while ctx.isClientConnected:
                print(ctx.GameState["state"])
                sleep(1)
