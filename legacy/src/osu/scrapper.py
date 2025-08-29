import ctypes
import ctypes.util
import os

os.add_dll_directory(r"C:\mingw64\bin")
lib = ctypes.CDLL(
    r"e:\projects\py\LocaOsuModule\scrapper\memory_scratcher.dll")

lib.Initialize.argtypes = []
lib.Clear.argtypes = []
lib.SuspendProcess.argtypes = []
lib.ResumeProcess.argtypes = []
lib.GetHitsData.argtypes = []
lib.GetH300.argtypes = []
lib.GetH100.argtypes = []
lib.GetH50.argtypes = []
lib.GetHMiss.argtypes = []
lib.GetCombo.argtypes = []
lib.GetMaxCombo.argtypes = []
lib.GetStateData.argtypes = []
lib.GetAcc.argtypes = []
lib.GetScore.argtypes = []

lib.Initialize.restype = None
lib.Clear.restype = None
lib.SuspendProcess.restype = None
lib.ResumeProcess.restype = None
lib.GetHitsData.restype = None
lib.GetH300.restype = ctypes.c_int
lib.GetH100.restype = ctypes.c_int
lib.GetH50.restype = ctypes.c_int
lib.GetHMiss.restype = ctypes.c_int
lib.GetCombo.restype = ctypes.c_int
lib.GetMaxCombo.restype = ctypes.c_int
lib.GetStateData.restype = ctypes.c_uint
lib.GetAcc.restype = ctypes.c_double
lib.GetScore.restype = ctypes.c_uint64


def Initialize() -> None:
    lib.Initialize()


def Clear() -> None:
    lib.Clear()


def GetHitsData() -> None:
    lib.GetHitsData()


def SuspendProcess() -> None:
    lib.SuspendProcess()


def ResumeProcess() -> None:
    lib.ResumeProcess()


def GetH300() -> int:
    return lib.GetH300()


def GetH100() -> int:
    return lib.GetH100()


def GetH50() -> int:
    return lib.GetH50()


def GetHMiss() -> int:
    return lib.GetHMiss()


def GetCombo() -> int:
    return lib.GetCombo()


def GetAcc() -> float:
    return lib.GetAcc()


def GetMaxCombo() -> int:
    return lib.GetMaxCombo()


def GetScore() -> int:
    return lib.GetScore()


def GetStateData() -> int:
    return lib.GetStateData()
