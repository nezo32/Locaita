import os
import re
import sys
import logging
import threading
import log.levels as levels
from dotenv import load_dotenv

load_dotenv()
load_dotenv(dotenv_path=".env.local", override=True)

RESET = "\033[0m"
COLORS = {
    "TIME": "\033[38;5;28m",
    "DEBUG": "\033[1;36m",
    "INFO": "\033[1;32;1m",
    "WARNING": "\033[1;93m",
    "ERROR": "\033[1;91m",
    "CRITICAL": "\033[1;95m",

    "STRING": "\033[38;5;173m",
    "NUMBER": "\033[38;5;150m",
    "NONE": "\033[38;5;27m"
}

base_logger = logging.getLogger("locaita")
channel = logging.StreamHandler()
file_handler = logging.FileHandler("logs/locaita.log")
base_logger.addHandler(channel)
base_logger.addHandler(file_handler)
_log_format = f"%(asctime)s - [%(levelname)s] - {os.path.basename(sys.argv[0]).split(".")[0]} - %(message)s"


def mapLevel(level: levels.LogLevels):
    match level:
        case levels.NOT_SET:
            return logging.NOTSET
        case levels.DEBUG:
            return logging.DEBUG
        case levels.INFO:
            return logging.INFO
        case levels.WARNING:
            return logging.WARNING
        case levels.ERROR:
            return logging.ERROR
        case levels.FATAL:
            return logging.CRITICAL
        case _:
            return logging.NOTSET


class ColorFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()

    STRING_PATTERN = re.compile(
        r'([\"])(.*?)(\1)')
    NUMBER_PATTERN = re.compile(r'(\d+(?:\.\d+)?)')
    NONE_PATTERN = re.compile(r'None')

    def colorize_strings(self, text: str) -> str:
        def repl(match):
            return f"{COLORS['STRING']}{match.group(0)}{RESET}"
        return self.STRING_PATTERN.sub(repl, text)

    def colorize_number(self, text: str):
        def repl(match):
            return f"{COLORS['NUMBER']}{match.group(0)}{RESET}"
        return self.NUMBER_PATTERN.sub(repl, text)

    def colorize_none(self, text: str):
        def repl(match):
            return f"{COLORS['NONE']}{match.group(0)}{RESET}"
        return self.NONE_PATTERN.sub(repl, text)

    def colorize(self, text):
        x = self.colorize_number(text)
        x = self.colorize_strings(x)
        x = self.colorize_none(x)
        return x

    def format(self, record: logging.LogRecord) -> str:
        time = f"{COLORS['TIME']}{self.formatTime(record, self.datefmt)}{RESET}"
        level = f"{COLORS.get(record.levelname, "")}{record.levelname}{RESET}"
        script = os.path.basename(sys.argv[0]).split(".")[0]
        message = self.colorize(record.getMessage())
        return f"{time} - [{level}] - {script} - {message}"


class Logger:

    def SetLevel(level: levels.LogLevels):
        level = mapLevel(level)
        base_logger.setLevel(level)
        channel.setLevel(level)
        file_handler.setLevel(level)

    def SetFormatter(formatter: logging.Formatter, file_formatter: logging.Formatter | None = None):
        channel.setFormatter(formatter)
        file_handler.setFormatter(file_formatter or formatter)

    def Debug(msg: object):
        base_logger.debug(msg)

    def Info(msg: object):
        base_logger.info(msg)

    def Warning(msg: object):
        base_logger.warning(msg)

    def Error(msg: object):
        base_logger.error(msg)

    def Fatal(msg: object):
        base_logger.critical(msg)


Logger.SetLevel(levels.LevelFromString(os.getenv("LOG_LEVEL", "DEBUG")))
Logger.SetFormatter(ColorFormatter(),
                    logging.Formatter(_log_format))


def handle_thread_exception(args):
    base_logger.error("Raised exception in thread %s", args.thread.name, exc_info=(
        args.exc_type, args.exc_value, args.exc_traceback))


threading.excepthook = handle_thread_exception
