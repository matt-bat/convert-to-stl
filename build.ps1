param([switch]$SkipInstall)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path .venv/Scripts/python.exe)) {
    py -3.12 -m venv .venv
    if ($LASTEXITCODE) { throw 'Python 3.12 x64 is required' }
}
$python = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not $SkipInstall) {
    & $python -m pip install -r requirements-lock.txt
    if ($LASTEXITCODE) { throw 'Dependency installation failed' }
}
& $python -m pytest -q
if ($LASTEXITCODE) { throw 'Regression tests failed' }
& $python -m PyInstaller --noconfirm 'Convert to STL.spec'
if ($LASTEXITCODE) { throw 'Packaging failed' }
& $python bundle_notices.py
if ($LASTEXITCODE) { throw 'Required notices could not be collected' }
& $python verify_package.py
if ($LASTEXITCODE) { throw 'Packaged conversion checks failed' }
& $python verify_packaged_ui.py 'dist/Convert to STL/Convert to STL.exe'
if ($LASTEXITCODE) { throw 'Packaged UI check failed' }
& $python package_release.py
if ($LASTEXITCODE) { throw 'Release archive check failed' }
