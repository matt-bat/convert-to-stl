from pathlib import Path
import importlib.metadata as md
import shutil
import sys
import urllib.request
import json
import platform
import tomllib

folder=Path(sys.argv[1]) if len(sys.argv)>1 else Path('dist/Convert to STL')
folder.mkdir(parents=True,exist_ok=True)
licenses=folder/'licenses';licenses.mkdir(exist_ok=True)
names=['PySide6-Essentials','shiboken6','cadquery-ocp-novtk','trimesh','numpy','networkx','Pillow','defusedxml','lxml','PyInstaller']
rows=['THIRD-PARTY NOTICES — Convert to STL','',
'This application uses unmodified dynamically linked libraries. Their licenses',
'are separate from the application source. Compatible replacement DLLs/Python',
'libraries may be placed in _internal; do not mix incompatible ABI versions.',
'Reverse engineering for debugging modifications to LGPL libraries is permitted.',
'']
for name in names:
    d=md.distribution(name)
    rows.append(f'{name} {d.version}')
    rows.append(d.metadata.get('Home-page','') or 'Package information: https://pypi.org/project/'+name+'/')
    for f in d.files or []:
        if any(k in str(f).lower() for k in ('license','copying','copyright')) and str(f).lower().endswith(('.txt','.md','.rst','.html','.lgpl','.gpl','license','copying')):
            p=Path(d.locate_file(f))
            if p.is_file():
                target=licenses/name/str(f);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    rows.append('')
urls={
 'Qt-LGPL-3.0.txt':'https://raw.githubusercontent.com/qt/qtbase/v6.8.3/LICENSES/LGPL-3.0-only.txt',
 'Qt-GPL-3.0.txt':'https://raw.githubusercontent.com/qt/qtbase/v6.8.3/LICENSES/GPL-3.0-only.txt',
 'OCCT-LGPL-2.1.txt':'https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/V7_8_1/LICENSE_LGPL_21.txt',
 'OCCT-exception.txt':'https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/V7_8_1/OCCT_LGPL_EXCEPTION.txt',
 'OCP-Apache-2.0.txt':'https://raw.githubusercontent.com/CadQuery/OCP/master/LICENSE'}
for name,url in urls.items():
    target=licenses/name
    if not target.exists():
        try:
            with urllib.request.urlopen(url,timeout=45) as r:target.write_bytes(r.read())
        except Exception as e: raise RuntimeError('Required license download failed: '+name) from e
rows.extend(['Source code and license locations:',
'Qt 6.8.3: https://download.qt.io/archive/qt/6.8/6.8.3/submodules/',
'PySide/Shiboken 6.8.3: https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.8.3-src/',
'Open CASCADE 7.8.1: https://github.com/Open-Cascade-SAS/OCCT/tree/V7_8_1',
'OCP bindings and wheel build: https://github.com/CadQuery/OCP',
'OCP wheel project: https://github.com/CadQuery/ocp-build-system',
'Python 3.12: https://www.python.org/downloads/source/',
'PyInstaller bootloader exception: https://pyinstaller.org/en/stable/license.html',
'', 'For redistribution, retain the bundled third-party notices and comply with',
'each dependency license, including applicable LGPL source-access requirements.'])
python_license=Path(sys.base_prefix)/'LICENSE.txt'
if not python_license.is_file(): raise FileNotFoundError('Python runtime license missing')
shutil.copyfile(python_license, licenses/'Python-LICENSE.txt')
rows.extend(['', 'Bundled Python runtime: '+platform.python_version(), 'Its license is included as licenses/Python-LICENSE.txt.'])
(folder/'THIRD-PARTY-NOTICES.txt').write_text('\n'.join(rows),encoding='utf-8')
for name in ('README.md','LICENSE','CHANGELOG.md','CONTRIBUTING.md','SECURITY.md','VALIDATION.md'):
    shutil.copyfile(name,folder/name)
shutil.copytree('docs',folder/'docs',dirs_exist_ok=True)
project=tomllib.loads(Path('pyproject.toml').read_text())['project']
(folder/'VERSION.txt').write_text(project['version']+'\n')
print('Third-party notices collected.')
