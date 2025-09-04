import os
from pathlib import Path
import dotenv
import signal
import traceback
from abc import ABC, abstractmethod

from locaita.log.logger import Logger
from locaita.utils.threads import ClearAllThreads
from locaita.utils.initial_message import Greetings

dotenv.load_dotenv()
dotenv.load_dotenv(dotenv_path=".env.local", override=True)


class ShutdownController:
    def __init__(self):
        self._old_handlers = {}

    def _handle(self, signum, frame):
        Logger.Info(f"Shutdown signal received: {signal.Signals(signum).name}")
        ClearAllThreads()
        raise Exception("shutdown signal")

    def __enter__(self):
        caught = [signal.SIGINT, signal.SIGTERM]
        if os.name == "nt" and hasattr(signal, "SIGBREAK"):
            caught.append(signal.SIGBREAK)

        for s in caught:
            self._old_handlers[s] = signal.getsignal(s)
            signal.signal(s, self._handle)
        return self

    def __exit__(self, exc_type, exc, tb):
        for s, h in self._old_handlers.items():
            signal.signal(s, h)
        return False


class CallableScript(ABC):
    def __init__(self):
        super().__init__()

        Path("logs").mkdir(
            parents=True, exist_ok=True)

    @abstractmethod
    def _start(self):
        pass

    @Greetings("LocAIta")
    def Start(self):
        with ShutdownController():
            try:
                self._start()
            except KeyboardInterrupt:
                Logger.Info("Interrupted by user (KeyboardInterrupt)")
            except Exception as e:
                Logger.Error(
                    f"Unhandled exception: {str(e)} / {traceback.format_exc()}")
            finally:
                ClearAllThreads()
