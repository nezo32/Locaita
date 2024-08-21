from osu.scrapper import ClearHitsData, ClearSigPage, CloseOsuHandle, CreateHitsData, \
    GetAcc, GetBaseAddress, GetCombo, GetH100, GetH300, GetH50, GetHMiss, GetHitsData, \
    GetMaxCombo, GetOsuHandle, GetRulesetsSigPage, GetScore, GetStateData, GetStatusSigPage
import ctypes
from osu.state import OsuInGameStates

class OsuMemory():
    def __init__(self):
        self.__pid = ctypes.c_ulong()
        self.__handle = GetOsuHandle(ctypes.byref(self.__pid))
        
        self.__rulesetSigPage = GetRulesetsSigPage(self.__handle)
        self.__statusSigPage = GetStatusSigPage(self.__handle)
        
        self.__rulesetBaseAddress = GetBaseAddress(self.__handle, self.__rulesetSigPage)
        self.__statusBaseAddress = GetBaseAddress(self.__handle, self.__statusSigPage)
        
        self.__hitsStruct = CreateHitsData()
        
        self.__tempCombo = 0
        self.__tempMiss = 0
        
        self.__hits = {
            '300': 0,
            '100': 0,
            '50': 0,
            'miss': 0,
            'slider_breaks': 0,
            'combo': 0,
            'score': 0,
            'max_combo': 0,
            'accuracy': 0.0
        }
    
    def GetInGameState(self) -> OsuInGameStates:
        return OsuInGameStates(GetStateData(self.__handle, self.__statusBaseAddress))
    
    def __getHitsData(self):
        self.__hits['300'] = GetH300(self.__hitsStruct)
        self.__hits['100'] = GetH100(self.__hitsStruct)
        self.__hits['50'] = GetH50(self.__hitsStruct)
        self.__hits['miss'] = GetHMiss(self.__hitsStruct)
        self.__hits['combo'] = GetCombo(self.__hitsStruct)
        self.__hits['max_combo'] = GetMaxCombo(self.__hitsStruct)
        self.__hits['accuracy'] = GetAcc(self.__hitsStruct)
        self.__hits['score'] = GetScore(self.__hitsStruct)

        if self.__tempCombo > self.__hits['max_combo']:
            self.__tempCombo = 0
            
        if self.__hits['combo'] < self.__tempCombo and self.__hits['miss'] == self.__tempMiss:
            self.__hits['slider_breaks'] += 1
        
        self.__tempCombo = self.__hits['combo']
        self.__tempMiss = self.__hits['miss']
        
        return self.__hits
    
    def GetHitsData(self):
        self.__hitsStruct = GetHitsData(self.__handle, self.__rulesetBaseAddress, self.__hitsStruct)
        return self.__getHitsData()
    
    def ClearOsuMemoryData(self):
        ClearHitsData(self.__hitsStruct)
        ClearSigPage(self.__rulesetSigPage)
        ClearSigPage(self.__statusSigPage)
        CloseOsuHandle(self.__handle)
    
    def __del__(self):
        self.ClearOsuMemoryData()