import ctypes

lib = ctypes.CDLL('F:\\LocAInaOsuModule\\memory\\MemoryScratcher.dll')

handle = lib.GetOsuHandle()

print(handle)

lib.CloseOsuHandle(handle)