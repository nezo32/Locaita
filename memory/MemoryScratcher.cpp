#include "MemoryScratcher.h"

// Debugger structs
typedef struct
{
    MEMORY_BASIC_INFORMATION mbi;
    char info[128];
} MEMPAGE;

static const SYSTEM_INFO systemInfo = []()
{
    SYSTEM_INFO si;
    GetSystemInfo(&si);
    return si;
}();

std::vector<MEMPAGE> QueryMemPages(HANDLE h_proc)
{
    std::vector<MEMPAGE> pages;
    pages.reserve(200);

    SIZE_T numBytes = 0;
    uintptr_t pageStart = (uintptr_t)systemInfo.lpMinimumApplicationAddress;
    uintptr_t allocationBase = 0;

    do
    {
        MEMORY_BASIC_INFORMATION mbi;
        memset(&mbi, 0, sizeof(mbi));

        numBytes = VirtualQueryEx(h_proc, (LPVOID)pageStart, &mbi, sizeof(mbi));

        if (mbi.State != MEM_FREE)
        {
            auto bReserved = mbi.State == MEM_RESERVE;
            auto bPrevReserved = pages.size() ? pages.back().mbi.State == MEM_RESERVE : false;
            if (bReserved || bPrevReserved || allocationBase != (uintptr_t)mbi.AllocationBase)
            {
                allocationBase = (uintptr_t)mbi.AllocationBase;

                MEMPAGE curPage;
                memset(&curPage, 0, sizeof(MEMPAGE));
                memcpy(&curPage.mbi, &mbi, sizeof(mbi));

                pages.push_back(curPage);
            }
            else
            {
                if (pages.size())
                    pages.back().mbi.RegionSize += mbi.RegionSize;
            }
        }

        uintptr_t newAddress = (uintptr_t)mbi.BaseAddress + mbi.RegionSize;

        if (newAddress <= pageStart)
            break;

        pageStart = newAddress;
    } while (numBytes);

    return pages;
}

bool MemoryCompare(const BYTE *bData, const BYTE *bMask, const char *szMask)
{
    for (; *szMask; ++szMask, ++bData, ++bMask)
    {
        if (*szMask == 'x' && *bData != *bMask)
        {
            return false;
        }
    }
    return (*szMask == NULL);
}

uint64_t FindSignature(HANDLE process, uint64_t start, size_t size, const char *sig, const char *mask)
{
    BYTE *data = (BYTE *)LocalAlloc(LPTR, size);
    memset(data, 0, size);

    SIZE_T bytesRead;

    ReadProcessMemory(process, (LPVOID)start, data, size, &bytesRead);

    for (uint64_t i = 0; i < size; i++)
    {
        if (MemoryCompare((const BYTE *)(data + i), (const BYTE *)sig, mask))
        {
            LocalFree(data);
            return start + i;
        }
    }

    LocalFree(data);
    return NULL;
}

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

    while (pid == NULL)
    {
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

        if (pid == NULL)
        {
            printf("... can`t find osu! process retrying ...\n");
            Sleep(1000);
        }
    }

    HANDLE process = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, pid);

    if (process == NULL)
    {
        printf("... can`t open process code: %d ...\n", GetLastError());
    }

    return process;
}

__declspec(dllexport) uint64_t GetBaseRulesetsAddress(HANDLE process)
{
    printf("... querying memory pages ...\n");
    auto pages = QueryMemPages(process);

    printf("... finding rulesets signature ...\n");
    const char signature[] = "\x7d\x15\xa1\x00\x00\x00\x00\x85\xc0";
    const char mask[] = "xxx????xx";

    uint64_t rulesetsAddress = 0;

    for (auto &page : pages)
    {
        if (page.mbi.State == MEM_COMMIT)
        {
            auto result = FindSignature(process, (uint64_t)page.mbi.BaseAddress, page.mbi.RegionSize, signature, mask);
            if (result != NULL)
            {
                printf("Rulesets signature address: %p\n", result);
                rulesetsAddress = result;
                break;
            }
        }
    }

    return rulesetsAddress;
}

__declspec(dllexport) Hits *GetHitsData(HANDLE process, uint64_t baseRulesetsAddress)
{
    // Rulesets      7D 15 A1 ?? ?? ?? ?? 85 C0          int16
    // Ruleset       [[Rulesets - 0xB] + 0x4]
    // Hit300        [[Ruleset + 0x68] + 0x38] + 0x8A    int16
    // Hit100        [[Ruleset + 0x68] + 0x38] + 0x88    int16
    // Hit50         [[Ruleset + 0x68] + 0x38] + 0x8C    int16
    // HitMiss       [[Ruleset + 0x68] + 0x38] + 0x92    int16

    Hits *hitsReturn = new Hits();

    int32_t buffer{};
    size_t readBytes{};

    ReadProcessMemory(process, (LPBYTE)baseRulesetsAddress - 0xB, &buffer, sizeof(int32_t), &readBytes);
    ReadProcessMemory(process, (LPBYTE)buffer + 0x4, &buffer, sizeof(int32_t), &readBytes);

    uint32_t rulesetAddress = buffer;
    ReadProcessMemory(process, (LPBYTE)rulesetAddress + 0x68, &buffer, sizeof(int32_t), &readBytes);
    ReadProcessMemory(process, (LPBYTE)buffer + 0x38, &buffer, sizeof(int32_t), &readBytes);

    int32_t hits = buffer;
    int16_t buff{};
    ReadProcessMemory(process, (LPBYTE)hits + 0x8A, &buff, sizeof(int16_t), &readBytes);
    hitsReturn->h300 = buff;
    ReadProcessMemory(process, (LPBYTE)hits + 0x88, &buff, sizeof(int16_t), &readBytes);
    hitsReturn->h100 = buff;
    ReadProcessMemory(process, (LPBYTE)hits + 0x8C, &buff, sizeof(int16_t), &readBytes);
    hitsReturn->h50 = buff;
    ReadProcessMemory(process, (LPBYTE)hits + 0x92, &buff, sizeof(int16_t), &readBytes);
    hitsReturn->hMiss = buff;

    return hitsReturn;
}

__declspec(dllexport) void ClearHitsData(Hits *data)
{
    delete data;
}

__declspec(dllexport) BOOL CloseOsuHandle(HANDLE pOsu)
{
    return CloseHandle(pOsu);
}