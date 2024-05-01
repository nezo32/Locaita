#include <windows.h>
#include <tlhelp32.h>
#include <string>
#include <vector>

typedef struct
{
    int h300;
    int h100;
    int h50;
    int hMiss;
} Hits;

extern "C"
{
    __declspec(dllexport) HANDLE GetOsuHandle();
    __declspec(dllexport) uint64_t GetBaseRulesetsAddress(HANDLE);
    __declspec(dllexport) Hits *GetHitsData(HANDLE, uint64_t);
    __declspec(dllexport) void ClearHitsData(Hits *);
    __declspec(dllexport) __declspec(dllexport) BOOL CloseOsuHandle(HANDLE);
}