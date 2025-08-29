import os
from log.logger import Logger
from scripts.callable_script import CallableScript


class OsuTrainScript(CallableScript):
    def _start(self):
        Logger.Info("my info")


def main():
    OsuTrainScript().Start()
