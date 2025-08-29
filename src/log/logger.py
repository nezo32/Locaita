import os
import sys
import logging
import log.levels as levels
from dotenv import load_dotenv

load_dotenv()
load_dotenv(dotenv_path=".env.local", override=True)

_log_format = f"%(asctime)s - [%(levelname)s] - {os.path.basename(sys.argv[0]).split(".")[0]} - %(message)s"

base_logger = logging.getLogger("locaita")
channel = logging.StreamHandler()
file_handler = logging.FileHandler("logs/locaita.log")
base_logger.addHandler(channel)
base_logger.addHandler(file_handler)


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


class Logger:

    def SetLevel(level: levels.LogLevels):
        level = mapLevel(level)
        base_logger.setLevel(level)
        channel.setLevel(level)
        file_handler.setLevel(level)

    def SetFormatter(formatter: logging.Formatter):
        channel.setFormatter(formatter)
        file_handler.setFormatter(formatter)

    def Debug(msg: object):
        base_logger.debug(msg)

    def Info(msg: object):
        base_logger.info(msg)

    def Warning(msg: object):
        base_logger.warning(msg)

    def Error(msg: object):
        base_logger.error(msg)

    def Critical(msg: object):
        base_logger.critical(msg)


Logger.SetLevel(levels.LevelFromString(os.getenv("LOG_LEVEL", "DEBUG")))
Logger.SetFormatter(logging.Formatter(_log_format))
