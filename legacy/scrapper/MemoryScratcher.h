#include <windows.h>
#include <tlhelp32.h>
#include <string>
#include <vector>
#include <cstdint>
#include <stdexcept>

typedef struct
{
    int h300;
    int h100;
    int h50;
    int hMiss;
    int combo;
    uint64_t score;
    int maxCombo;
    double accuracy;
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

#define EXPORT extern "C" __declspec(dllexport)
#define NULLC '\0'

EXPORT void Initialize();
EXPORT void Clear();

EXPORT void SuspendProcess();
EXPORT void ResumeProcess();

EXPORT void GetHitsData();
EXPORT unsigned int GetStateData();

EXPORT int GetH300();
EXPORT int GetH100();
EXPORT int GetH50();
EXPORT int GetHMiss();
EXPORT int GetCombo();
EXPORT double GetAcc();
EXPORT int GetMaxCombo();
EXPORT unsigned long long GetScore();
