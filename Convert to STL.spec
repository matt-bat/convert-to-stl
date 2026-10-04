from pathlib import Path
from PIL import Image
from PyInstaller.utils.hooks import collect_all, collect_delvewheel_libs_directory
ocp_data, ocp_bins, ocp_imports = collect_all('OCP')
ocp_data, ocp_bins = collect_delvewheel_libs_directory('cadquery_ocp_novtk', datas=ocp_data, binaries=ocp_bins)
Path('artifacts').mkdir(exist_ok=True)
Image.open('assets/icon.png').save('artifacts/icon.ico', sizes=[(16,16),(32,32),(48,48),(128,128),(256,256)])
a = Analysis(['app.py'], pathex=[], binaries=ocp_bins, datas=ocp_data + [('assets', 'assets')],
    hiddenimports=ocp_imports + ['trimesh','trimesh.exchange.stl','trimesh.exchange.obj','trimesh.exchange.ply','trimesh.exchange.off','trimesh.exchange.gltf','networkx','PIL.Image'],
    excludes=['pytest','tkinter','matplotlib','scipy','IPython'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Convert to STL',
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False, console=False, icon='artifacts/icon.ico', version='version_info.txt')
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='Convert to STL')
