"""Linux build: pip install ziglang==0.17.1; python build.py.
Downloads pinned official Python/PyPI archives; produces a Windows portable folder.
"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parent
OUTPUT=ROOT/'build'/'CompresorPDF_Imagenes'
DOWNLOADS=ROOT/'build'/'downloads'
OUTPUT.mkdir(parents=True,exist_ok=True)
DOWNLOADS.mkdir(parents=True,exist_ok=True)
manifest=json.loads((ROOT/'manifest.json').read_text())

def fetch(item):
    path=DOWNLOADS/item['filename']
    if not path.exists():
        urllib.request.urlretrieve(item['url'],path)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
        raise RuntimeError('Checksum incorrecto: '+path.name)
    return path

runtime=OUTPUT/'runtime'
with zipfile.ZipFile(fetch(manifest['python'])) as archive:
    archive.extractall(runtime)
for item in manifest['wheels']:
    with zipfile.ZipFile(fetch(item)) as archive:
        archive.extractall(runtime/'Lib/site-packages')
(runtime/'python312._pth').write_text('python312.zip\n.\nLib/site-packages\n..\nimport site\n')
source=ROOT.parent/'optimizer.py' if (ROOT.parent/'optimizer.py').exists() else ROOT/'optimizer.py'
shutil.copy2(source,OUTPUT/'optimizer.py')
subprocess.run([sys.executable,'-m','ziglang','cc','-target','x86_64-windows-gnu',
               '-O2','-Wall','-Wextra','-Werror',str(ROOT/'launcher.c'),
               '-lcomdlg32','-lshell32','-luser32','-Wl,--stack,8388608',
               '-o',str(OUTPUT/'CompresorPDF_Imagenes.exe')],check=True)
print('Carpeta portable:',OUTPUT)
