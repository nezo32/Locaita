import ctypes

lib = ctypes.CDLL('F:\\LocAInaOsuModule\\dll\\MemoryScratcher.dll')

class OsuHits(ctypes.Structure):
    _fields_ = [('h300', ctypes.c_int),
                ('h100', ctypes.c_int),
                ('h50', ctypes.c_int),
                ('hMiss', ctypes.c_int)]

lib.GetBaseRulesetsAddress.restype = ctypes.POINTER(OsuHits)

def GetOsuHandle(): 
    return lib.GetOsuHandle()

def CloseOsuHandle(handle):
    lib.CloseOsuHandle(handle)

def GetBaseRulesetsAddress(handle):
    return lib.GetBaseRulesetsAddress(handle)

def GetHitsData(handle, baseRulesetsAddress) -> OsuHits:
    return lib.GetHitsData(handle, baseRulesetsAddress)

def ClearHitsData(dataPointer):
    lib.ClearHitsData(dataPointer)
    
