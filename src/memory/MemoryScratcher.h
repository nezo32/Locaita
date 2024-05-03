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
    int combo;
    int maxCombo;
} Hits;

typedef struct
{
    MEMORY_BASIC_INFORMATION mbi;
    char info[128];
} MEMPAGE;

typedef struct
{
    MEMPAGE *page;
    char *signature;
    char *mask;
} SigPage;

extern "C"
{
    __declspec(dllexport) HANDLE GetOsuHandle();

    __declspec(dllexport) Hits *CreateHitsData();
    __declspec(dllexport) SigPage *GetRulesetsSigPage(HANDLE);
    __declspec(dllexport) SigPage *GetStatusSigPage(HANDLE);
    __declspec(dllexport) uint64_t GetBaseAddress(HANDLE, SigPage *);

    __declspec(dllexport) Hits *GetHitsData(HANDLE, uint64_t, Hits *);
    __declspec(dllexport) uint32_t GetStateData(HANDLE, uint64_t);

    __declspec(dllexport) int GetH300(Hits *);
    __declspec(dllexport) int GetH100(Hits *);
    __declspec(dllexport) int GetH50(Hits *);
    __declspec(dllexport) int GetHMiss(Hits *);
    __declspec(dllexport) int GetCombo(Hits *);
    __declspec(dllexport) int GetMaxCombo(Hits *);

    __declspec(dllexport) void ClearHitsData(Hits *);
    __declspec(dllexport) void ClearSigPage(SigPage *);
    __declspec(dllexport) BOOL CloseOsuHandle(HANDLE);
}