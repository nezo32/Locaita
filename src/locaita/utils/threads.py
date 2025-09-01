import threading
from typing import Optional
from abc import ABC, abstractmethod

from locaita.log.logger import Logger


class CancellationToken:
    def __init__(self):
        self.lock = threading.Lock()
        self._cancelled = False

    def Cancel(self):
        with self.lock:
            self._cancelled = True

    @property
    def IsCancelled(self):
        with self.lock:
            return self._cancelled


class ThreadedClass(ABC):
    def __init__(self, name: str, daemon=True, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.daemon = daemon
        self.lock = threading.Lock()
        self.cancellation_token = threading.Event()
        self.thread: Optional[threading.Thread] = None
        all_threads.append(self)

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
        Logger.Info(f'Thread "{self.name}" started')

    def Stop(self):
        self.cancellation_token.set()
        self._ThreadStop()
        if self.__thread is not None:
            self.__thread.join()
        if self in all_threads:
            all_threads.remove(self)
            Logger.Info(f'Thread "{self.name}" successfully stopped')


all_threads: list[ThreadedClass] = []


def ClearAllThreads():
    for thread in all_threads:
        thread.Stop()
