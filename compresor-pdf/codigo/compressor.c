#define UNICODE
#define _UNICODE
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <commdlg.h>
#include <shellapi.h>
#include <stdio.h>
#include <wchar.h>
#include <stdlib.h>
#include <string.h>
#include <io.h>
#include <fcntl.h>

#define CAP 32768
extern const unsigned char payload0[], payload0_end[], payload1[], payload1_end[], payload2[], payload2_end[], payload3[], payload3_end[], payload4[], payload4_end[];
static const wchar_t *names[]={L"qpdf.exe",L"qpdf30.dll",L"libgcc_s_seh-1.dll",L"libstdc++-6.dll",L"libwinpthread-1.dll"};
static const unsigned char *starts[]={payload0,payload1,payload2,payload3,payload4};
static const unsigned char *ends[]={payload0_end,payload1_end,payload2_end,payload3_end,payload4_end};
static wchar_t root[CAP], engine[CAP], logpath[CAP];
static HANDLE job;
static int ok_count, skip_count, err_count;

static void join(wchar_t *out,const wchar_t *dir,const wchar_t *name){swprintf(out,CAP,L"%ls\\%ls",dir,name);}
static unsigned long long size_of(const wchar_t *p){WIN32_FILE_ATTRIBUTE_DATA d; if(!GetFileAttributesExW(p,GetFileExInfoStandard,&d))return 0; return ((unsigned long long)d.nFileSizeHigh<<32)|d.nFileSizeLow;}
static void cleanup(void){wchar_t p[CAP]; for(int i=0;i<5;i++){join(p,root,names[i]);DeleteFileW(p);} const wchar_t *files[]={L"analysis.json",L"candidate.pdf",L"best.pdf",L"qpdf.log"}; for(int i=0;i<4;i++){join(p,root,files[i]);DeleteFileW(p);} RemoveDirectoryW(root);}
static int setup(void){
 wchar_t temp[CAP]; if(!GetTempPathW(CAP,temp))return 0;
 for(int i=0;i<100;i++){swprintf(root,CAP,L"%lsPDFsinPerdida-%lu-%llu-%d",temp,GetCurrentProcessId(),GetTickCount64(),i); if(CreateDirectoryW(root,NULL))break; if(i==99)return 0;}
 for(int i=0;i<5;i++){wchar_t p[CAP];join(p,root,names[i]);HANDLE h=CreateFileW(p,GENERIC_WRITE,0,NULL,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,NULL); if(h==INVALID_HANDLE_VALUE)return 0;DWORD len=(DWORD)(ends[i]-starts[i]),written=0;BOOL good=WriteFile(h,starts[i],len,&written,NULL);CloseHandle(h);if(!good||written!=len)return 0;}
 join(engine,root,L"qpdf.exe");join(logpath,root,L"qpdf.log");
 job=CreateJobObjectW(NULL,NULL); if(!job)return 0;
 JOBOBJECT_EXTENDED_LIMIT_INFORMATION lim={0};lim.BasicLimitInformation.LimitFlags=JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
 return SetInformationJobObject(job,JobObjectExtendedLimitInformation,&lim,sizeof(lim));
}
/* No shell is used. Quoted Windows paths cannot contain a literal double quote. */
static DWORD run(const wchar_t *args,const wchar_t *out){
 wchar_t cmd[CAP*3];swprintf(cmd,CAP*3,L"\"%ls\" %ls",engine,args);
 SECURITY_ATTRIBUTES sa={sizeof(sa),NULL,TRUE};
 HANDLE h=CreateFileW(out?out:logpath,GENERIC_WRITE,FILE_SHARE_READ,&sa,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,NULL);
 HANDLE err=out?CreateFileW(logpath,GENERIC_WRITE,FILE_SHARE_READ,&sa,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,NULL):h;
 HANDLE input=CreateFileW(L"NUL",GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE,&sa,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
 if(h==INVALID_HANDLE_VALUE||err==INVALID_HANDLE_VALUE||input==INVALID_HANDLE_VALUE){if(h!=INVALID_HANDLE_VALUE)CloseHandle(h);if(out&&err!=INVALID_HANDLE_VALUE)CloseHandle(err);if(input!=INVALID_HANDLE_VALUE)CloseHandle(input);return 999;}
 STARTUPINFOW si={0};si.cb=sizeof(si);si.dwFlags=STARTF_USESTDHANDLES;si.hStdOutput=h;si.hStdError=err;si.hStdInput=input;
 PROCESS_INFORMATION pi={0}; DWORD code=999;
 if(CreateProcessW(engine,cmd,NULL,NULL,TRUE,CREATE_NO_WINDOW|CREATE_SUSPENDED,NULL,root,&si,&pi)){
  if(AssignProcessToJobObject(job,pi.hProcess)){ResumeThread(pi.hThread);WaitForSingleObject(pi.hProcess,INFINITE);GetExitCodeProcess(pi.hProcess,&code);}else TerminateProcess(pi.hProcess,999);
  CloseHandle(pi.hProcess);CloseHandle(pi.hThread);
 }
 CloseHandle(input);CloseHandle(h);if(out)CloseHandle(err);return code;
}
/* qpdf expands object streams and canonicalizes PDF names before this scan. */
static int has_signature(const wchar_t *path){
 FILE *f=_wfopen(path,L"rb");if(!f)return -1;
 char b[65537];size_t carry=0,n;int found=0;
 while((n=fread(b+carry,1,65536-carry,f))>0){size_t total=carry+n;b[total]=0;
  if(strstr(b,"\"/ByteRange\"")||strstr(b,"\"/Sig\"")||strstr(b,"\"/DocMDP\"")){found=1;break;}
  carry=total<64?total:64;memmove(b,b+total-carry,carry);
 }
 if(ferror(f))found=-1;fclose(f);return found;
}
static void process(const wchar_t *input){
 wchar_t src[CAP],args[CAP*3],json[CAP],candidate[CAP],best[CAP],dest[CAP];
 if(!GetFullPathNameW(input,CAP,src,NULL)){err_count++;return;}
 wprintf(L"\nArchivo: %ls\n",src);
 const wchar_t *ext=wcsrchr(src,L'.');if(!ext||_wcsicmp(ext,L".pdf")){wprintf(L"Omitido: selecciona un archivo PDF.\n");skip_count++;return;}
 HANDLE lock=CreateFileW(src,GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
 if(lock==INVALID_HANDLE_VALUE){wprintf(L"Error: no se pudo abrir; puede estar en uso o sin permisos.\n");err_count++;return;}
 unsigned long long original=size_of(src),smallest=original;
 join(json,root,L"analysis.json");join(candidate,root,L"candidate.pdf");join(best,root,L"best.pdf");DeleteFileW(best);
 swprintf(args,CAP*3,L"--is-encrypted \"%ls\"",src);
 DWORD enc=run(args,NULL);
 if(enc!=2){wprintf(L"Omitido: PDF cifrado o no se pudo analizar con seguridad.\n");skip_count++;goto done;}
 swprintf(args,CAP*3,L"--check \"%ls\"",src);
 if(run(args,NULL)!=0){wprintf(L"Omitido: el PDF tiene errores o avisos de integridad.\n");skip_count++;goto done;}
 swprintf(args,CAP*3,L"--json --json-key=qpdf --json-stream-data=none \"%ls\"",src);
 if(run(args,json)!=0){wprintf(L"Error al analizar el documento.\n");err_count++;goto done;}
 int sig=has_signature(json);DeleteFileW(json);
 if(sig!=0){wprintf(sig>0?L"Omitido: firma digital o campo de firma; se conserva intacto.\n":L"Error al verificar firmas.\n");if(sig>0)skip_count++;else err_count++;goto done;}
 for(int i=0;i<2;i++){
  wprintf(L"Optimizando sin perdida (%d/2)...\n",i+1);
  swprintf(args,CAP*3,L"--object-streams=%ls --compress-streams=y --decode-level=generalized --recompress-flate --compression-level=9 --preserve-unreferenced \"%ls\" \"%ls\"",i?L"disable":L"preserve",src,candidate);
  DeleteFileW(candidate);
  if(run(args,NULL)!=0){wprintf(L"Error en la optimizacion. No se guarda ninguna copia.\n");err_count++;goto done;}
  swprintf(args,CAP*3,L"--check \"%ls\"",candidate);
  if(run(args,NULL)!=0){wprintf(L"La copia no paso la verificacion; no se guarda.\n");err_count++;goto done;}
  unsigned long long now=size_of(candidate);
  if(now>0&&now<smallest){DeleteFileW(best);if(!MoveFileW(candidate,best)){wprintf(L"Error al guardar el temporal.\n");err_count++;goto done;}smallest=now;}
 }
 if(smallest==original){wprintf(L"Ya optimizado: no se consiguio reducirlo sin perdida. No se crea copia.\n");skip_count++;goto done;}
 {size_t stem=(size_t)(ext-src);if(stem>CAP-80){err_count++;goto done;}
  int saved=0;
  for(int i=1;i<=9999;i++){
   if(i==1)swprintf(dest,CAP,L"%.*ls_comprimido.pdf",(int)stem,src);else swprintf(dest,CAP,L"%.*ls_comprimido (%d).pdf",(int)stem,src,i);
   if(MoveFileExW(best,dest,MOVEFILE_COPY_ALLOWED|MOVEFILE_WRITE_THROUGH)){saved=1;break;}
   DWORD e=GetLastError();if(e!=ERROR_FILE_EXISTS&&e!=ERROR_ALREADY_EXISTS)break;
  }
  if(!saved){wprintf(L"Error: no se pudo guardar junto al original. Revisa espacio y permisos.\n");err_count++;goto done;}
  wprintf(L"Guardado: %ls\n%.2f MB -> %.2f MB | Reduccion: %.1f%%\n",dest,original/1048576.0,smallest/1048576.0,100.0*(original-smallest)/original);ok_count++;
 }
done:
 CloseHandle(lock);DeleteFileW(json);DeleteFileW(candidate);DeleteFileW(best);
}
int main(void){
 _setmode(_fileno(stdout),_O_U16TEXT);SetConsoleTitleW(L"Compresor PDF sin perdida");
 wprintf(L"COMPRESOR PDF SIN PERDIDA - Windows 64 bits\n\nMantiene contenido y calidad visual. Siempre conserva el original.\nNo procesa PDF cifrados, con firma digital o con errores.\n\n");
 if(!setup()){wprintf(L"No se pudo iniciar el motor temporal. Pulsa Intro para cerrar.\n");cleanup();getchar();return 1;}
 int argc=0;wchar_t **argv=CommandLineToArgvW(GetCommandLineW(),&argc);
 if(argc>1){for(int i=1;i<argc;i++)process(argv[i]);}
 else{
  wchar_t *selection=calloc(CAP,sizeof(wchar_t));
  OPENFILENAMEW ofn={0};ofn.lStructSize=sizeof(ofn);ofn.hwndOwner=GetConsoleWindow();ofn.lpstrFilter=L"Documentos PDF\0*.pdf\0\0";ofn.lpstrFile=selection;ofn.nMaxFile=CAP;ofn.lpstrTitle=L"Selecciona los PDF que deseas comprimir";ofn.Flags=OFN_EXPLORER|OFN_ALLOWMULTISELECT|OFN_FILEMUSTEXIST|OFN_PATHMUSTEXIST|OFN_NOCHANGEDIR;
  if(selection&&GetOpenFileNameW(&ofn)){
   wchar_t *next=selection+wcslen(selection)+1;
   if(!*next)process(selection);else while(*next){wchar_t path[CAP];join(path,selection,next);process(path);next+=wcslen(next)+1;}
  }else if(CommDlgExtendedError()){wprintf(L"Error en el selector: selecciona menos archivos a la vez.\n");err_count++;}
  free(selection);
 }
 if(argv)LocalFree(argv);cleanup();if(job)CloseHandle(job);
 wprintf(L"\nFinalizado: %d comprimidos; %d omitidos; %d errores.\n\nPulsa Intro para cerrar.",ok_count,skip_count,err_count);fflush(stdout);getchar();return err_count?1:0;
}
