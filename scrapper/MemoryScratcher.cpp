#include "MemoryScratcher.h"

const SYSTEM_INFO systemInfo = []()
{
    SYSTEM_INFO si;
    GetSystemInfo(&si);
    return si;
}();

HANDLE process;
Hits *data;
SigPage *statusSP = nullptr;
SigPage *rulesetsSP = nullptr;
uint64_t rulesetsBase = 0;
uint64_t statusBase = 0;

/* HELPERS */
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
    return (*szMask == NULLC);
}
uint64_t FindSignature(uint64_t start, size_t size, const char *sig, const char *mask)
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
    return 0;
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

/* PROCESS SUSPEND/RESUME */
void SuspendProcess()
{
    HANDLE hThreadSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);

    THREADENTRY32 threadEntry;
    threadEntry.dwSize = sizeof(THREADENTRY32);

    Thread32First(hThreadSnapshot, &threadEntry);

    do
    {
        if (threadEntry.th32OwnerProcessID == GetProcessId(process))
        {
            HANDLE hThread = OpenThread(THREAD_ALL_ACCESS, FALSE,
                                        threadEntry.th32ThreadID);

            SuspendThread(hThread);
            CloseHandle(hThread);
        }
    } while (Thread32Next(hThreadSnapshot, &threadEntry));

    CloseHandle(hThreadSnapshot);
}
void ResumeProcess()
{
    HANDLE hThreadSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);

    THREADENTRY32 threadEntry;
    threadEntry.dwSize = sizeof(THREADENTRY32);

    Thread32First(hThreadSnapshot, &threadEntry);

    do
    {
        if (threadEntry.th32OwnerProcessID == GetProcessId(process))
        {
            HANDLE hThread = OpenThread(THREAD_ALL_ACCESS, FALSE,
                                        threadEntry.th32ThreadID);

            ResumeThread(hThread);
            CloseHandle(hThread);
        }
    } while (Thread32Next(hThreadSnapshot, &threadEntry));

    CloseHandle(hThreadSnapshot);
}

/* INITIALIZATION */
void GetOsuHandle()
{

    WCHAR name[] = L"osu!.exe";
    DWORD pid = 0;

    while (pid == 0)
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

        if (pid == 0)
        {
            printf("... can`t find osu! process retrying ...\n");
            Sleep(1000);
        }
    }

    process = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, pid);

    if (process == 0)
    {
        printf("... can`t open process code: %d ...\n", GetLastError());
    }
}
void GetRulesetsSigPage()
{
    printf("... querying memory pages ...\n");
    auto pages = QueryMemPages(process);

    printf("... finding rulesets signature ...\n");
    // 7D 15 A1 ?? ?? ?? ?? 85 C0
    const char signature[] = "\x7d\x15\xa1\x00\x00\x00\x00\x85\xc0";
    const char mask[] = "xxx????xx";

    uint64_t rulesetsAddress = 0;
    MEMPAGE *neededPage{};

    for (auto &page : pages)
    {
        if (page.mbi.State == MEM_COMMIT)
        {
            auto result = FindSignature((uint64_t)page.mbi.BaseAddress, page.mbi.RegionSize, signature, mask);
            if (result != 0)
            {
                printf("Rulesets signature address: %p\n", result);
                neededPage = &page;
                break;
            }
        }
    }

    SigPage *sp = new SigPage();

    sp->page = neededPage;

    sp->mask = (char *)malloc(10);
    sp->signature = (char *)malloc(10);

    memcpy(sp->mask, mask, 10);
    memcpy(sp->signature, signature, 10);

    rulesetsSP = sp;
}
void GetStatusSigPage()
{
    printf("... querying memory pages ...\n");
    auto pages = QueryMemPages(process);

    printf("... finding status signature ...\n");
    // 48 83 F8 04 73 1E
    const char signature[] = "\x48\x83\xf8\x04\x73\x1e";
    const char mask[] = "xxxxxx";

    uint64_t rulesetsAddress = 0;
    MEMPAGE *neededPage{};

    for (auto &page : pages)
    {
        if (page.mbi.State == MEM_COMMIT)
        {
            auto result = FindSignature((uint64_t)page.mbi.BaseAddress, page.mbi.RegionSize, signature, mask);
            if (result != 0)
            {
                printf("Rulesets signature address: %p\n", result);
                neededPage = &page;
                break;
            }
        }
    }

    SigPage *sp = new SigPage();

    sp->page = neededPage;

    sp->mask = (char *)malloc(7);
    sp->signature = (char *)malloc(7);

    memcpy(sp->mask, mask, 7);
    memcpy(sp->signature, signature, 7);

    statusSP = sp;
}
void GetBaseAddresses()
{
    rulesetsBase = FindSignature((uint64_t)statusSP->page->mbi.BaseAddress, statusSP->page->mbi.RegionSize, statusSP->signature, statusSP->mask);
    statusBase = FindSignature((uint64_t)rulesetsSP->page->mbi.BaseAddress, rulesetsSP->page->mbi.RegionSize, rulesetsSP->signature, rulesetsSP->mask);
}
void CreateHitsData()
{
    data = new Hits();
}
void Initialize()
{
    GetOsuHandle();
    GetRulesetsSigPage();
    GetStatusSigPage();
    GetBaseAddresses();
    CreateHitsData();
}

/* QUERIEING */
void GetHitsData()
{
    // Rulesets      7D 15 A1 ?? ?? ?? ?? 85 C0
    // Ruleset       [[Rulesets - 0xB] + 0x4]
    // Hit300        [[Ruleset + 0x68] + 0x38] + 0x8A    int16
    // Hit100        [[Ruleset + 0x68] + 0x38] + 0x88    int16
    // Hit50         [[Ruleset + 0x68] + 0x38] + 0x8C    int16
    // HitMiss       [[Ruleset + 0x68] + 0x38] + 0x92    int16
    // Combo         [[Ruleset + 0x68] + 0x38] + 0x94    int16
    // MaxCombo      [[Ruleset + 0x68] + 0x38] + 0x68    int16
    // Accuracy      [[Ruleset + 0x68] + 0x48] + 0xC     float64
    // Score         [[Ruleset + 0x68] + 0x38] + 0x78    int32

    int32_t buffer{};
    size_t readBytes{};

    ReadProcessMemory(process, (LPBYTE)rulesetsBase - 0xB, &buffer, sizeof(int32_t), &readBytes);
    ReadProcessMemory(process, (LPBYTE)buffer + 0x4, &buffer, sizeof(int32_t), &readBytes);

    uint32_t rulesetAddress = buffer;
    uint32_t rulesetAccAddress = buffer;
    ReadProcessMemory(process, (LPBYTE)rulesetAddress + 0x68, &buffer, sizeof(int32_t), &readBytes);
    ReadProcessMemory(process, (LPBYTE)buffer + 0x48, &rulesetAccAddress, sizeof(int32_t), &readBytes);
    ReadProcessMemory(process, (LPBYTE)buffer + 0x38, &buffer, sizeof(int32_t), &readBytes);

    int32_t hits = buffer;
    int32_t accuracy = rulesetAccAddress;
    int16_t buff{};
    int32_t buffScore{};
    double buffAcc{};
    ReadProcessMemory(process, (LPBYTE)rulesetAccAddress + 0xC, &buffAcc, sizeof(double), &readBytes);
    data->accuracy = buffAcc;
    printf("accuracy: %f ", buffAcc);
    ReadProcessMemory(process, (LPBYTE)hits + 0x8A, &buff, sizeof(int16_t), &readBytes);
    data->h300 = buff;
    printf("300: %d ", buff);
    ReadProcessMemory(process, (LPBYTE)hits + 0x88, &buff, sizeof(int16_t), &readBytes);
    data->h100 = buff;
    printf("100: %d ", buff);
    ReadProcessMemory(process, (LPBYTE)hits + 0x8C, &buff, sizeof(int16_t), &readBytes);
    data->h50 = buff;
    printf("50: %d ", buff);
    ReadProcessMemory(process, (LPBYTE)hits + 0x92, &buff, sizeof(int16_t), &readBytes);
    data->hMiss = buff;
    printf("miss: %d ", buff);
    ReadProcessMemory(process, (LPBYTE)hits + 0x94, &buff, sizeof(int16_t), &readBytes);
    data->combo = buff;
    printf("combo: %d ", buff);
    ReadProcessMemory(process, (LPBYTE)hits + 0x68, &buff, sizeof(int16_t), &readBytes);
    data->maxCombo = buff;
    printf("maxCombo: %d ", buff);
    ReadProcessMemory(process, (LPBYTE)hits + 0x78, &buffScore, sizeof(int32_t), &readBytes);
    data->score = buffScore;
    printf("maxCombo: %d ", buff);
}
uint32_t GetStateData()
{
    // Status       48 83 F8 04 73 1E
    // State        [Status - 0x4]

    uint32_t buffer{};
    size_t readBytes{};

    ReadProcessMemory(process, (LPBYTE)statusBase - 0x4, &buffer, sizeof(uint32_t), &readBytes);
    ReadProcessMemory(process, (LPBYTE)buffer, &buffer, sizeof(uint32_t), &readBytes);

    return buffer;
}

/* READING STRUCTURE */
uint64_t GetScore()
{
    return data->score;
}
int GetH300()
{
    return data->h300;
}
int GetH100()
{
    return data->h100;
}
int GetH50()
{
    return data->h50;
}
int GetHMiss()
{
    return data->hMiss;
}
int GetCombo()
{
    return data->combo;
}
double GetAcc()
{
    return data->accuracy;
}
int GetMaxCombo()
{
    return data->maxCombo;
}

/* CLEARING */
void ClearSigPage(SigPage *sp)
{
    free(sp->mask);
    free(sp->signature);
    delete sp;
}
void ClearSigPages()
{
    ClearSigPage(statusSP);
    ClearSigPage(rulesetsSP);
}
void ClearHitsData()
{
    delete data;
}
void CloseOsuHandle()
{
    CloseHandle(process);
}
void Clear()
{
    ClearHitsData();
    ClearSigPages();
    CloseOsuHandle();
}