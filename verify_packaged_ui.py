"""Verify the frozen native UI and its manual-start guarantee."""
from pathlib import Path
import os,json,subprocess,tempfile,time,shutil,sys
root=Path(__file__).resolve().parent
exe=Path(sys.argv[1]).resolve()
screenshot=root/'artifacts/packaged-ui.png'
startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
subprocess.run([str(exe),'--ui-check',str(screenshot)],startupinfo=startup,timeout=45,check=True)
assert screenshot.is_file() and screenshot.stat().st_size>10000
with tempfile.TemporaryDirectory(prefix='stl_manual_check_') as tmp:
    folder=Path(tmp);source=folder/'manual-start-check.3mf'
    shutil.copyfile(root/'samples/box-10x20x30.3mf',source)
    proc=subprocess.Popen([str(exe),str(source)],startupinfo=startup)
    try:
        time.sleep(8)
        assert proc.poll() is None,'App exited unexpectedly'
        assert not list(folder.glob('*.stl')),'Adding a file started conversion automatically'
    finally:
        proc.terminate();proc.wait(timeout=15)
print('PASS: packaged UI renders; adding one file creates no STL without Convert.')
