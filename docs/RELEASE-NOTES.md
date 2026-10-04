# Convert to STL 1.0.0

A native Windows app for converting supported 3D models to binary STL on your own PC.

## Downloads

- **convert-to-stl-v1.0.0-windows-x64.zip** — complete portable app, executable,
  runtime, documentation, and license notices. Extract everything, then open
  `Convert to STL/Convert to STL.exe`. Keep `_internal` beside it.
- **convert-to-stl-v1.0.0-source.zip** — complete application, tests, fixtures,
  docs, and build scripts. Python 3.12 x64 on Windows is the build target.
- **SHA256SUMS.txt** — SHA-256 hashes for both ZIPs and the release manifest.
- **release-manifest.json** — version, dependency inventory, and ZIP hashes.

```powershell
Get-FileHash .\convert-to-stl-v1.0.0-windows-x64.zip -Algorithm SHA256
```

Compare the value with `SHA256SUMS.txt` before running the download.

## Features

Supports 3MF, STEP/STP, IGES/IGS, OBJ, PLY, OFF, GLB/GLTF, basic AMF, and STL.
Includes adaptive settings, batch conversion, explicit start, Stop and retry,
collision-safe filenames, dimensions, and open-edge warnings. Conversion runs
locally without an account or upload service.

## Checks and limitations

Release qualification includes the source test suite, eight known-dimension
frozen-worker conversions, a packaged GUI launch, and a check that adding a file
does not start conversion. See VALIDATION.md in the source archive for scope.

Windows x64 only; unsigned portable executable. No MSI installer. STL keeps
geometry only, and this is not an automatic mesh-repair tool. Specialist 3MF
beam/volume geometry, AMF constellations/curves, G-code, and native proprietary
CAD project files are not supported. Inspect converted models in your slicer.

## License

Original project: Convert to STL Attribution-Required Non-Commercial License
v1.0. Attribution is required; commercial use needs prior written permission.
Third-party libraries retain their own licenses and bundled notices.
