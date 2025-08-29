import dotenv
from abc import ABC, abstractmethod
from scripts.utils.initial_message import Greetings

dotenv.load_dotenv()
dotenv.load_dotenv(dotenv_path=".env.local", override=True)


class CallableScript(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def _start(self):
        pass

    @Greetings("LocAIta")
    def Start(self):
        self._start()
