#include <windows.h>
#include <tlhelp32.h>
#include <string>

extern "C"
{
    __declspec(dllexport) HANDLE GetOsuHandle();
    __declspec(dllexport) BOOL CloseOsuHandle(HANDLE);
}