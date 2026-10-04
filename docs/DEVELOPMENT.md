# Development and releases

[Back to README](../README.md)

## Environment

Windows x64 and Python 3.12 x64 are the build target. Install Git and Python,
clone the repository, then run the setup commands in the README.
`requirements-lock.txt` pins the tested build and runtime environment. Network
access is required for the initial package installation and license collection.
`pyproject.toml` records project metadata and pytest settings; this desktop
repository is not published as a pip package.

## Source map

| File | Responsibility |
| --- | --- |
| `app.py` | Native PySide6 window, queue, settings, subprocess management, internal worker dispatch |
| `converter.py` | Input readers, transforms, unit conversion, mesh inspection, atomic STL output |
| `assets/` | Original icon and dropdown indicator |
| `tests/` | Converter and native UI regression tests |
| `samples/`, `make_samples.py` | Small generated box/sphere models and their generator |
| `Convert to STL.spec`, `version_info.txt` | PyInstaller collection and Windows EXE metadata |
| `bundle_notices.py` | Dependency notices, runtime license texts, and bundled user docs |
| `verify_package.py` | Known-dimension conversions through the frozen executable |
| `verify_packaged_ui.py` | Packaged-window capture and manual-start verification |
| `package_release.py` | Portable/source ZIPs, SHA-256 checksums, dependency/release manifest |
| `build.ps1` | Ordered install, test, build, verification, and packaging workflow |

The GUI starts one `QProcess` per input. The worker writes a small JSON result
file; the GUI displays its status and continues the batch after failures. CAD
uses OCP/Open CASCADE, while ordinary mesh scenes use trimesh. The 3MF and AMF
readers handle their supported XML geometry directly. Outputs use a temporary
file and collision-safe final placement. Originals are never overwritten.

## Commands

```powershell
# Full automated suite (run from the repo directory).
.\.venv\Scripts\python.exe -m pytest -q

# Native source UI.
.\.venv\Scripts\python.exe app.py

# Source UI screenshots plus a real manually initiated batch.
.\.venv\Scripts\python.exe check_ui.py

# Complete release build, including verification and archives.
.\build.ps1

# Reuse an already installed locked environment.
.\build.ps1 -SkipInstall
```

Run UI checks on an interactive Windows desktop. They can briefly display
windows. The GitHub Actions workflow runs source tests on a Windows runner;
local packaged GUI verification remains a release requirement. No automated
release publishing or signing credentials are embedded in the repository.

To check an existing build independently:

```powershell
.\.venv\Scripts\python.exe verify_package.py
.\.venv\Scripts\python.exe verify_packaged_ui.py "dist/Convert to STL/Convert to STL.exe"
```

`--worker` and `--ui-check` are internal/testing interfaces, not a supported
end-user CLI. The ordinary command `app.py <file> ...` adds files to the queue
but does not start conversion. Library use is possible through
`converter.convert(source, output_dir=None, quality='Balanced', unit='millimeter')`;
it returns output path, triangle count, size in mm, and warning text. The GUI's
20-minute timeout is not applied when calling that function directly.

## Release procedure

1. Update the version in `pyproject.toml` and Windows `version_info.txt`; update
   the changelog and release notes. Keep their versions consistent.
2. Run `build.ps1` and inspect `artifacts/packaged-ui.png` plus the generated
   conversion results. Review source and notices for secrets, personal paths,
   unexpected files, and missing licenses.
3. Review the complete diff, commit the verified sources, and tag that commit
   `v<version>`. Do not publish a release from an unreviewed working tree.
4. Create a GitHub release targeting that tag. Upload the portable Windows ZIP,
   full source ZIP, `SHA256SUMS.txt`, and `release-manifest.json` from
   `artifacts/releases/v<version>/`. Use `docs/RELEASE-NOTES.md` as the body.
5. Download/check the published files against their hashes. Confirm the repo
   is public and the release points at the intended commit.

The source ZIP is assembled from an explicit list in `package_release.py`.
Update that list when adding a required root-level source/build file. Binary
runtimes go in release assets, not Git history. The archive manifest records
exact dependency versions and file hashes; it does not claim byte-for-byte
reproducible builds. PyInstaller output contains build-dependent metadata.

## Licensing and dependency changes

Preserve the original project license and separate upstream notices. The
bundle uses unmodified dynamically linked Qt/PySide6 and OCP/Open CASCADE.
See [third-party components](THIRD-PARTY.md) before changing dependencies or
packaging. The app is not code-signed. Maintainers must verify a new build on
the target system and keep source access and notices current when redistributing.
