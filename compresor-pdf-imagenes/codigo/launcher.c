#define UNICODE
#define _UNICODE
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <commdlg.h>
#include <shellapi.h>
#include <stdio.h>
#include <wchar.h>
#include <stdlib.h>
#include <io.h>
#include <fcntl.h>
#define CAP 32768
static wchar_t folder[CAP],python[CAP],script[CAP];
static HANDLE job;
static int width,errors;
static void process(const wchar_t *path){
 wchar_t full[CAP];if(!GetFullPathNameW(path,CAP,full,NULL)){errors++;return;}
 HANDLE lock=CreateFileW(full,GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
 if(lock==INVALID_HANDLE_VALUE){wprintf(L"No se pudo abrir: %ls\n",full);errors++;return;}
 wchar_t *cmd=calloc(CAP*4,sizeof(wchar_t));if(!cmd){CloseHandle(lock);errors++;return;}
 int count=swprintf(cmd,CAP*4,L"\"%ls\" -I -u \"%ls\" --width %d \"%ls\"",python,script,width,full);
 if(count<0||count>=32767){wprintf(L"La ruta es demasiado larga.\n");errors++;goto done;}
 STARTUPINFOW si={0};si.cb=sizeof(si);PROCESS_INFORMATION pi={0};
 if(!CreateProcessW(python,cmd,NULL,NULL,FALSE,CREATE_SUSPENDED,NULL,folder,&si,&pi)){
  wprintf(L"No se pudo iniciar Python portable. Extrae el ZIP completo y conserva la carpeta runtime.\n");errors++;goto done;
 }
 if(!AssignProcessToJobObject(job,pi.hProcess)){TerminateProcess(pi.hProcess,1);errors++;}
 else{ResumeThread(pi.hThread);WaitForSingleObject(pi.hProcess,INFINITE);DWORD code=1;GetExitCodeProcess(pi.hProcess,&code);if(code)errors++;}
 CloseHandle(pi.hProcess);CloseHandle(pi.hThread);
done:
 free(cmd);CloseHandle(lock);
}
int main(void){
 _setmode(_fileno(stdout),_O_U16TEXT);SetConsoleTitleW(L"Compresor PDF - Imagenes compartidas");
 wprintf(L"COMPRESOR PDF - IMAGENES COMPARTIDAS 2.0\n\nConserva el original. Procesa los PDF localmente.\n\n");
 if(!GetModuleFileNameW(NULL,folder,CAP))return 1;
 wchar_t *slash=wcsrchr(folder,L'\\');if(!slash)return 1;*slash=0;
 swprintf(python,CAP,L"%ls\\runtime\\python.exe",folder);swprintf(script,CAP,L"%ls\\optimizer.py",folder);
 if(GetFileAttributesW(python)==INVALID_FILE_ATTRIBUTES||GetFileAttributesW(script)==INVALID_FILE_ATTRIBUTES){
  wprintf(L"Extrae TODO el ZIP antes de ejecutar el programa. Deben estar optimizer.py y runtime junto al EXE.\nPulsa Intro para cerrar.");getchar();return 1;
 }
 int choice=MessageBoxW(GetConsoleWindow(),L"Elige el modo:\n\nSI: reutilizar imagenes identicas y reducir a 1800 px las imagenes RGB/grises mas anchas. Pierde resolucion en esas imagenes.\n\nNO: solo reutilizar imagenes identicas, sin reducir su calidad.\n\nEl texto y los dibujos independientes no se rasterizan. Siempre conserva el original.",L"Compresion de imagenes PDF",MB_YESNOCANCEL|MB_ICONINFORMATION|MB_DEFBUTTON2);
 if(choice==IDCANCEL)return 0;width=choice==IDYES?1800:0;
 wprintf(width?L"Modo: imagenes hasta 1800 px de ancho.\n":L"Modo: reutilizar duplicados sin perdida.\n");
 job=CreateJobObjectW(NULL,NULL);if(!job)return 1;JOBOBJECT_EXTENDED_LIMIT_INFORMATION lim={0};lim.BasicLimitInformation.LimitFlags=JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
 if(!SetInformationJobObject(job,JobObjectExtendedLimitInformation,&lim,sizeof(lim))){CloseHandle(job);return 1;}
 int argc=0;wchar_t **argv=CommandLineToArgvW(GetCommandLineW(),&argc);
 if(argc>1){for(int i=1;i<argc;i++)process(argv[i]);}
 else{
  wchar_t *files=calloc(CAP,sizeof(wchar_t));if(!files){CloseHandle(job);return 1;}
  OPENFILENAMEW o={0};o.lStructSize=sizeof(o);o.hwndOwner=GetConsoleWindow();o.lpstrFilter=L"Archivos PDF\0*.pdf\0\0";o.lpstrFile=files;o.nMaxFile=CAP;o.lpstrTitle=L"Selecciona uno o varios PDF";o.Flags=OFN_EXPLORER|OFN_ALLOWMULTISELECT|OFN_FILEMUSTEXIST|OFN_PATHMUSTEXIST|OFN_NOCHANGEDIR;
  if(GetOpenFileNameW(&o)){
   wchar_t *next=files+wcslen(files)+1;
   if(!*next)process(files);else while(*next){wchar_t path[CAP];swprintf(path,CAP,L"%ls\\%ls",files,next);process(path);next+=wcslen(next)+1;}
  }else if(CommDlgExtendedError()){wprintf(L"Error del selector. Selecciona menos archivos a la vez.\n");errors++;}
  free(files);
 }
 if(argv)LocalFree(argv);CloseHandle(job);wprintf(L"\nFinalizado. Incidencias: %d. Pulsa Intro para cerrar.\n",errors);getchar();return errors?1:0;
}
