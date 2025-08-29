from enum import Enum


class OsuInGameStates(Enum):
    MAIN_MENU = "menu"
    PLAYING = "in_game"
    SONG_SELECT = "song_select"
    RESULT_SCREEN = "results"
    MAP_LOADING = "loader"
    UNKNOWN = "unknown"
