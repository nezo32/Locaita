// Base          F8 01 74 04 83 65                   int16
// Rulesets      7D 15 A1 ?? ?? ?? ?? 85 C0          int16
// Hit300        [[Ruleset + 0x68] + 0x38] + 0x8A    int16
// Hit100        [[Ruleset + 0x68] + 0x38] + 0x88    int16
// Hit50         [[Ruleset + 0x68] + 0x38] + 0x8C    int16
// HitMiss       [[Ruleset + 0x68] + 0x38] + 0x92    int16

#include "MemoryScratcher.h"

const WCHAR *GetWC(const CHAR *c)
{
    const size_t cSize = strlen(c) + 1;
    WCHAR *wc = new WCHAR[cSize];
    mbstowcs(wc, c, cSize);

    return wc;
}

const WCHAR *GetWC(const WCHAR *c)
{
    return c;
}

__declspec(dllexport) HANDLE GetOsuHandle()
{
    WCHAR name[] = L"osu!.exe";
    DWORD pid = 0;

    // Create toolhelp snapshot.
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    PROCESSENTRY32 process;
    ZeroMemory(&process, sizeof(process));
    process.dwSize = sizeof(process);

    // Walkthrough all processes.
    if (Process32First(snapshot, &process))
    {
        do
        {

            if (std::wcscmp(GetWC(process.szExeFile), name) == 0)
            {
                pid = process.th32ProcessID;
                break;
            }
        } while (Process32Next(snapshot, &process));
    }

    CloseHandle(snapshot);

    if (pid != 0)
    {
        return OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, pid);
    }

    return NULL;
}

__declspec(dllexport) BOOL CloseOsuHandle(HANDLE pOsu)
{
    return CloseHandle(pOsu);
}