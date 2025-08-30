import contextlib
from typing import override
from locaita.modules.osu.context.game import GameContext
from locaita.modules.osu.context.screen import ScreenContext


class Context(contextlib.AbstractContextManager["Context"]):
    def __init__(self):
        self.GameCTX = GameContext()
        self.ScreenCTX = ScreenContext()

    @override
    def __enter__(self):
        self.GameCTX.__enter__()
        self.ScreenCTX.__enter__()
        return super().__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        args = (exc_type, exc_value, traceback)
        self.GameCTX.__exit__(*args)
        self.ScreenCTX.__exit__(*args)
        return super().__exit__(*args)
