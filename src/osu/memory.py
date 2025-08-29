import threading
import time
from osu.state import OsuInGameStates
from typing import TypedDict
import websocket
import json
""" import win32api
import win32con """


class Hits(TypedDict):
    score: int
    accuracy: float


""" def debounce(wait_time):
    def decorator(func):
        timer = None
        lock = threading.Lock()

        def debounced_function(*args, **kwargs):
            nonlocal timer
            with lock:
                if timer is not None:
                    timer.cancel()
                timer = threading.Timer(
                    wait_time, func, args=args, kwargs=kwargs)
                timer.start()
        return debounced_function
    return decorator """


class OsuMemory():
    def __init__(self):
        self.__state: OsuInGameStates = OsuInGameStates.UNKNOWN
        self.__hits: Hits = {
            'score': 0,
            'accuracy': 0.0
        }

        self.ws = websocket.WebSocketApp("ws://127.0.0.1:7272")
        self.ws.on_open = lambda *_: print("connected to ws")
        self.ws.on_close = lambda *_: print("connection to ws is closed")
        self.ws.on_error = lambda *e: print("error occurred in ws")
        self.ws.on_message = self.OnMessage
        self.state_lock = threading.Lock()
        self.hits_lock = threading.Lock()

        self.thread = threading.Thread(target=self.ws.run_forever)
        self.thread.start()
        """ self.cancellation_token_lock = threading.Lock()
        self.cancellation_token = False
        self.keypress_thread = threading.Thread(target=self.keypress)
        self.keypress_thread.start() """

    def GetInGameState(self) -> OsuInGameStates:
        with self.state_lock:
            return self.__state

    def GetHitsData(self):
        with self.hits_lock:
            return self.__hits

    """ @debounce(1)
    def keypress_send_pause(self):
        self.ws.send_text("pause")

    @debounce(1)
    def keypress_send_resume(self):
        self.ws.send_text("resume")

    def keypress(self):
        while True:
            with self.cancellation_token_lock:
                if self.cancellation_token:
                    break
                
            if win32api.GetAsyncKeyState(win32con.VK_HOME) < 0:
                self.keypress_send_pause()
            if win32api.GetAsyncKeyState(win32con.VK_END) < 0:
                self.keypress_send_resume()
            time.sleep(0.05) """

    def OnMessage(self, _, m):
        data = json.loads(m)
        with self.state_lock:
            self.__state = data["state"]
        with self.hits_lock:
            self.__hits = {
                "accuracy": data["accuracy"],
                "score": data["score"]
            }

    def OnClose(self, *_):
        print("ws is closed")
        """ with self.cancellation_token_lock:
            self.cancellation_token = True
        self.ws.close() """

    def __del__(self):
        """ with self.cancellation_token_lock:
            self.cancellation_token = True """
        self.ws.close()
        self.thread.join()
        """ self.keypress_thread.join() """
