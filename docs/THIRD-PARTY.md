# Third-party components

[Back to README](../README.md)

The project LICENSE covers original Convert to STL work. Third-party code,
binary libraries, and their notices remain under their own licenses. The
project's noncommercial condition does not replace or narrow upstream rights.

| Component | Role | Upstream |
| --- | --- | --- |
| PySide6 / Shiboken / Qt | Native interface and process integration | https://www.qt.io/qt-for-python |
| OCP / Open CASCADE | STEP and IGES parsing and tessellation | https://github.com/CadQuery/OCP ; https://github.com/Open-Cascade-SAS/OCCT |
| trimesh | Mesh import, transforms, inspection and STL export | https://github.com/mikedh/trimesh |
| NumPy | Geometry arrays and numerical operations | https://numpy.org/ |
| NetworkX | Graph operations used by trimesh | https://networkx.org/ |
| Pillow | Icon generation and packaged image support | https://python-pillow.github.io/ |
| defusedxml / lxml | XML handling | https://github.com/tiran/defusedxml ; https://lxml.de/ |
| CPython | Bundled interpreter and standard library | https://www.python.org/ |
| PyInstaller | Executable bootloader and bundling | https://pyinstaller.org/ |

`bundle_notices.py` collects installed distribution license files, the Python
runtime license, and the relevant Qt/OCCT/OCP license texts. Missing required
downloads fail the release build. `THIRD-PARTY-NOTICES.txt` in the portable
release lists versions and upstream source locations; `licenses/` contains
the actual texts. Some dependencies bundle further components whose notices
are included in their distribution licenses.

LGPL libraries are dynamically linked and remain in `_internal/`. Compatible
replacements can be installed there; rebuilding from the provided application
source against modified libraries is also possible. Reverse engineering for
debugging modifications to LGPL libraries is permitted. Do not mix incompatible
ABIs. Preserve upstream copyright and license notices when redistributing.

Build-only packages are pinned alongside runtime packages in the lockfile.
Release manifests distinguish neither a legal SBOM nor a vulnerability scan:
the dependency inventory is supplied for build inspection and provenance.
