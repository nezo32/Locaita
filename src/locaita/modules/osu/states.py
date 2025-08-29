from enum import Enum
from typing import TypedDict


class PlayerState(Enum):
    MAIN_MENU = "menu"
    PLAYING = "in_game"
    SONG_SELECT = "song_select"
    RESULT_SCREEN = "results"
    MAP_LOADING = "loader"
    UNKNOWN = "unknown"


class GameState(TypedDict):
    state: PlayerState
    score: int
    accuracy: float
