import ctypes

lib = ctypes.CDLL('F:\\LocAInaOsuModule\\dll\\MemoryScratcher.dll')

class Hits(ctypes.Structure):
    _fields_ = [('h300', ctypes.c_int),
                ('h100', ctypes.c_int),
                ('h50', ctypes.c_int),
                ('hMiss', ctypes.c_int),
                ('combo', ctypes.c_int),
                ('maxCombo', ctypes.c_int)]

class SigPage(ctypes.Structure):
    _fields_ = [('page', ctypes.c_void_p),
                ('signature', ctypes.c_char_p),
                ('mask', ctypes.c_char_p),]

lib.GetBaseAddress.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
lib.GetHitsData.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
lib.GetStateData.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
lib.GetRulesetsSigPage.argtypes = [ctypes.c_void_p]
lib.GetStatusSigPage.argtypes = [ctypes.c_void_p]
lib.CloseOsuHandle.argtypes = [ctypes.c_void_p]
lib.ClearHitsData.argtypes = [ctypes.c_void_p]

lib.GetH300.argtypes = [ctypes.POINTER(Hits)]
lib.GetH100.argtypes = [ctypes.POINTER(Hits)]
lib.GetH50.argtypes = [ctypes.POINTER(Hits)]
lib.GetHMiss.argtypes = [ctypes.POINTER(Hits)]
lib.GetCombo.argtypes = [ctypes.POINTER(Hits)]
lib.GetMaxCombo.argtypes = [ctypes.POINTER(Hits)]


lib.GetOsuHandle.restype = ctypes.c_void_p
lib.GetBaseAddress.restype = ctypes.c_void_p
lib.GetHitsData.restype = ctypes.POINTER(Hits)
lib.GetStateData.restype = ctypes.c_int32
lib.GetRulesetsSigPage.restype = ctypes.POINTER(SigPage)
lib.GetStatusSigPage.restype = ctypes.POINTER(SigPage)
lib.CreateHitsData.restype = ctypes.POINTER(Hits)


lib.GetH300.restype = ctypes.c_int
lib.GetH100.restype = ctypes.c_int
lib.GetH50.restype = ctypes.c_int
lib.GetHMiss.restype = ctypes.c_int
lib.GetCombo.restype = ctypes.c_int
lib.GetMaxCombo.restype = ctypes.c_int

def GetOsuHandle(): 
    return lib.GetOsuHandle()

def GetRulesetsSigPage(handle):
    return lib.GetRulesetsSigPage(handle)
def GetStatusSigPage(handle):
    return lib.GetStatusSigPage(handle)
def CreateHitsData():
    return lib.CreateHitsData()

def GetBaseAddress(handle, sigPage):
    return lib.GetBaseAddress(handle, sigPage)

def GetHitsData(handle, baseRulesetsAddress, hits):
    return lib.GetHitsData(handle, baseRulesetsAddress, hits)
def GetStateData(handle, baseAddress):
    return lib.GetStateData(handle, baseAddress)

def GetH300(hitsData):
    return lib.GetH300(hitsData)
def GetH100(hitsData):
    return lib.GetH100(hitsData)
def GetH50(hitsData):
    return lib.GetH50(hitsData)
def GetHMiss(hitsData):
    return lib.GetHMiss(hitsData)
def GetCombo(hitsData):
    return lib.GetCombo(hitsData)
def GetMaxCombo(hitsData):
    return lib.GetMaxCombo(hitsData)


def ClearHitsData(dataPointer):
    lib.ClearHitsData(dataPointer)
def ClearSigPage(sigPage):
    lib.ClearSigPage(sigPage)
def CloseOsuHandle(handle):
    lib.CloseOsuHandle(handle)
    
