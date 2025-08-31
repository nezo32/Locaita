import threading
from typing import Optional
from abc import ABC, abstractmethod


class CancellationToken:
    def __init__(self):
        self.lock = threading.Lock()
        self._cancelled = False

    def Cancel(self):
        with self.lock:
            self._cancelled = True

    def IsCancelled(self):
        with self.lock:
            return self._cancelled


class ThreadedClass(ABC):
    def __init__(self, name: Optional[str] = None, daemon=True):
        super().__init__()
        self.name = name
        self.daemon = daemon
        self.lock = threading.Lock()
        self.cancellation_token = CancellationToken()
        self.thread: Optional[threading.Thread] = None

    @abstractmethod
    def _ThreadTarget():
        pass

    @abstractmethod
    def _ThreadStart():
        pass

    @abstractmethod
    def _ThreadStop():
        pass

    def Start(self):
        self._ThreadStart()
        self.__thread = threading.Thread(
            target=self._ThreadTarget, name=self.name, daemon=self.daemon)
        self.__thread.start()

    def Stop(self):
        self._ThreadStop()
        if self.__thread is not None:
            self.__thread.join()
