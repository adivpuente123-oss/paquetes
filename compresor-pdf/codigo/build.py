"""Rebuild on Linux: pip install ziglang==0.17.1, then python build.py."""
from pathlib import Path
import hashlib, subprocess, sys, urllib.request, zipfile
ROOT=Path(__file__).resolve().parent
URL='https://github.com/qpdf/qpdf/releases/download/v12.4.2/qpdf-12.4.2-mingw64.zip'
EXPECTED='773d2fa0c7d161e2271430734338e560a07b25d0edf11ceee8e53de435012766'
vendor=ROOT/'vendor'
archive=ROOT/'qpdf.zip'
if not archive.exists():
    urllib.request.urlretrieve(URL,archive)
if hashlib.sha256(archive.read_bytes()).hexdigest()!=EXPECTED:
    raise RuntimeError('Checksum qpdf incorrecto')
with zipfile.ZipFile(archive) as z:
    z.extractall(vendor)
names=['qpdf.exe','qpdf30.dll','libgcc_s_seh-1.dll','libstdc++-6.dll','libwinpthread-1.dll']
asm=['.section .rdata,"dr"']
for i,name in enumerate(names):
    path=vendor/'qpdf-12.4.2-mingw64'/'bin'/name
    asm += [f'.global payload{i}',f'.global payload{i}_end',f'payload{i}:',f'.incbin "{path.as_posix()}"',f'payload{i}_end:']
(ROOT/'payload.S').write_text('\n'.join(asm)+'\n')
subprocess.run([sys.executable,'-m','ziglang','cc','-target','x86_64-windows-gnu','-O2','-Wall','-Wextra',str(ROOT/'compressor.c'),str(ROOT/'payload.S'),'-lcomdlg32','-lshell32','-luser32','-Wl,--stack,8388608','-o',str(ROOT/'CompresorPDF.exe')],check=True)
print('Creado:',ROOT/'CompresorPDF.exe')
