from typing import Type, Union


NOT_SET = 0
DEBUG = 1
INFO = 2
WARNING = 3
ERROR = 4
FATAL = 5

LogLevels = Type[Union[NOT_SET, DEBUG, INFO, WARNING, ERROR, FATAL]]


def LevelFromString(string: str) -> LogLevels:
    match string:
        case "NotSet" | "NOT_SET":
            return NOT_SET
        case "Debug" | "DEBUG":
            return DEBUG
        case "Info" | "INFO":
            return INFO
        case "Warning" | "WARNING":
            return WARNING
        case "Error" | "ERROR":
            return ERROR
        case "Fatal" | "FATAL":
            return FATAL
        case _:
            return NOT_SET
