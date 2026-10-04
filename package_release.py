"""Create reviewed portable/source archives and their release metadata."""
from pathlib import Path
import hashlib
import importlib.metadata as metadata
import json
import os
import platform
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parent
SOURCE_FILES = (
    '.gitignore', '.gitattributes', 'LICENSE', 'README.md', 'CHANGELOG.md',
    'CONTRIBUTING.md', 'SECURITY.md', 'VALIDATION.md', 'pyproject.toml',
    'requirements-lock.txt', 'app.py', 'converter.py', 'build.ps1',
    'Convert to STL.spec', 'version_info.txt', 'bundle_notices.py',
    'package_release.py', 'check_ui.py', 'make_samples.py', 'test_ui.py',
    'verify_package.py', 'verify_packaged_ui.py',
)
SOURCE_DIRS = ('assets', 'docs', 'tests', 'samples', '.github')


def source_files():
    files = [ROOT / name for name in SOURCE_FILES]
    for name in SOURCE_DIRS:
        files.extend(p for p in (ROOT / name).rglob('*')
                     if p.is_file() and '__pycache__' not in p.parts
                     and p.suffix not in ('.pyc', '.pyo'))
    for path in files:
        if not path.is_file():
            raise FileNotFoundError(f'Required release source missing: {path.name}')
    return sorted(set(files))


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for data in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def archive(target, paths, base, prefix=''):
    temporary = target.with_suffix('.zip.partial')
    with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in paths:
            z.write(path, prefix + path.relative_to(base).as_posix())
    with zipfile.ZipFile(temporary) as z:
        bad = z.testzip()
        if bad:
            raise RuntimeError(f'Archive integrity failure: {bad}')
    os.replace(temporary, target)
    return {'file': target.name, 'bytes': target.stat().st_size, 'sha256': sha256(target)}


def main():
    project = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))['project']
    version = project['version']
    folder = ROOT / 'artifacts' / 'releases' / ('v' + version)
    folder.mkdir(parents=True, exist_ok=True)
    runtime = ROOT / 'dist' / 'Convert to STL'
    for name in ('Convert to STL.exe', '_internal/python312.dll', 'LICENSE',
                 'README.md', 'THIRD-PARTY-NOTICES.txt', 'licenses/Python-LICENSE.txt'):
        if not (runtime / name).is_file():
            raise FileNotFoundError(f'Required portable file missing: {name}')
    dependencies = []
    for line in (ROOT / 'requirements-lock.txt').read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        name, expected = line.split('==')
        installed = metadata.version(name)
        if installed != expected:
            raise RuntimeError(f'{name}: installed {installed}, expected {expected}')
        dependencies.append({'name': name, 'version': installed})
    files = source_files()
    assets = [archive(folder / f'convert-to-stl-v{version}-windows-x64.zip',
                      sorted(p for p in runtime.rglob('*') if p.is_file()), ROOT / 'dist'),
              archive(folder / f'convert-to-stl-v{version}-source.zip', files, ROOT,
                      prefix=f'convert-to-stl-{version}/')]
    manifest = {
        'project': project['name'], 'version': version,
        'repository': project['urls']['Repository'], 'tag': 'v' + version,
        'platform': 'windows-x64', 'python': platform.python_version(),
        'license': 'Convert to STL Attribution-Required Non-Commercial License v1.0',
        'assets': assets, 'build_dependencies': dependencies,
        'source_files': {p.relative_to(ROOT).as_posix(): sha256(p) for p in files},
    }
    manifest_path = folder / 'release-manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    sums = [f"{item['sha256']}  {item['file']}" for item in assets]
    sums.append(f'{sha256(manifest_path)}  {manifest_path.name}')
    (folder / 'SHA256SUMS.txt').write_text('\n'.join(sums) + '\n', encoding='utf-8')
    print(f'Release v{version}: {len(files)} source files; ZIP integrity checks passed.')
    for asset in assets:
        print(f"{asset['file']}: {asset['bytes']:,} bytes")


if __name__ == '__main__':
    main()
