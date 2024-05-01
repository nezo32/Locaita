import ctypes

lib = ctypes.CDLL('F:\\LocAInaOsuModule\\dll\\MemoryScratcher.dll')

class Hits(ctypes.Structure):
    _fields_ = [('h300', ctypes.c_int),
                ('h100', ctypes.c_int),
                ('h50', ctypes.c_int),
                ('hMiss', ctypes.c_int)]

lib.GetBaseRulesetsAddress.argtypes = [ctypes.c_void_p]
lib.GetHitsData.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
lib.CloseOsuHandle.argtypes = [ctypes.c_void_p]
lib.ClearHitsData.argtypes = [ctypes.c_void_p]

lib.GetH300.argtypes = [ctypes.POINTER(Hits)]
lib.GetH100.argtypes = [ctypes.POINTER(Hits)]
lib.GetH50.argtypes = [ctypes.POINTER(Hits)]
lib.GetHMiss.argtypes = [ctypes.POINTER(Hits)]


lib.GetOsuHandle.restype = ctypes.c_void_p
lib.GetBaseRulesetsAddress.restype = ctypes.c_void_p
lib.GetHitsData.restype = ctypes.POINTER(Hits)

lib.GetH300.restype = ctypes.c_int
lib.GetH100.restype = ctypes.c_int
lib.GetH50.restype = ctypes.c_int
lib.GetHMiss.restype = ctypes.c_int

def GetOsuHandle(): 
    return lib.GetOsuHandle()

def CloseOsuHandle(handle):
    lib.CloseOsuHandle(handle)

def GetBaseRulesetsAddress(handle):
    return lib.GetBaseRulesetsAddress(handle)

def GetHitsData(handle, baseRulesetsAddress):
    return lib.GetHitsData(handle, baseRulesetsAddress)

def GetH300(hitsData):
    return lib.GetH300(hitsData)
def GetH100(hitsData):
    return lib.GetH100(hitsData)
def GetH50(hitsData):
    return lib.GetH50(hitsData)
def GetHMiss(hitsData):
    return lib.GetHMiss(hitsData)


def ClearHitsData(dataPointer):
    lib.ClearHitsData(dataPointer)
    
