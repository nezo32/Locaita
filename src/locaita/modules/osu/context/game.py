import os
import json
import threading
import contextlib
from time import sleep
from websocket import WebSocketApp
from locaita.log.logger import Logger
from locaita.utils.threads import ThreadedClass
from typing import Literal, TypedDict, override
from locaita.modules.osu.states import GameState, PlayerState


class WebSocketDTO(TypedDict):
    state: Literal["menu", "in_game", "song_select",
                   "results", "loader", "unknown"]
    score: int
    accuracy: float


class WebSocketClient(ThreadedClass):
    def __init__(self, url: str):
        super().__init__("WebSocketClient")
        self.__app = WebSocketApp(url)

        self.__app.on_open = self.__onOpen
        self.__app.on_close = self. __onClose
        self.__app.on_error = self.__onError
        self.__app.on_message = self.__onMessage

        self.__connected_lock = threading.Lock()

        self.__isConnected = None

        self.__data: WebSocketDTO = {
            "state": "unknown",
            "score": 0,
            "accuracy": 0.0
        }

    def _ThreadTarget(self):
        self.__app.run_forever()

    def _ThreadStart(self):
        pass

    def _ThreadStop(self):
        self.__app.close()

    def __onOpen(self, ws):
        Logger.Info("Connected to WebSocket osu! server")
        with self.__connected_lock:
            self.__isConnected = True

    def __onClose(self, ws, close_status_code, close_msg):
        Logger.Info(
            f"WebSocket connection closed: {close_status_code} {close_msg}")
        with self.__connected_lock:
            self.__isConnected = False

    def __onError(self, ws: WebSocketApp, error):
        Logger.Error(f"WebSocket error occurred: {error!r}")
        ws.close()

    def __onMessage(self, ws, message: str):
        Logger.Debug(f"Received WebSocket data: {message!r}")
        with self.lock:
            self.__data = json.loads(message)

    def GetData(self):
        with self.lock:
            return self.__data

    @property
    def IsConnected(self):
        with self.__connected_lock:
            return self.__isConnected


class GameContext(contextlib.AbstractContextManager["GameContext"]):
    def __init__(self):
        self.__client = WebSocketClient(
            os.getenv("OSU_WS_URL", "ws://127.0.0.1:7272"))

    @property
    def GameState(self) -> GameState:
        data = self.__client.GetData()
        return {
            "score": data["score"],
            "accuracy": data["accuracy"],
            "state": PlayerState(data["state"])
        }

    @property
    def isClientConnected(self) -> bool:
        return self.__client.IsConnected

    @override
    def __enter__(self):
        self.__client.Start()

        while self.isClientConnected is None:
            sleep(0.5)

        return super().__enter__()

    @override
    def __exit__(self, exc_type, exc_value, traceback):
        self.__client.Stop()
