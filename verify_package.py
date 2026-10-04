from pathlib import Path
import json
import os
import subprocess
import sys
import numpy as np
import trimesh

root=Path(__file__).resolve().parent
exe=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root/'dist/Convert to STL/Convert to STL.exe'
out=root/'artifacts/packaged-output';out.mkdir(parents=True,exist_ok=True)
env=dict(os.environ);env['PATH']=os.environ.get('SystemRoot','C:/Windows')+'/System32'
env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None)
results=[]
for source in sorted((root/'samples').iterdir()):
    result_file=out/(source.name+'.json')
    command=[str(exe),'--worker',str(source),str(out),'Balanced','millimeter',str(result_file)]
    p=subprocess.run(command,cwd=out,env=env,capture_output=True,timeout=120)
    result=json.loads(result_file.read_text()) if result_file.exists() else {'ok':False,'error':p.stderr.decode(errors='replace')}
    assert p.returncode==0 and result['ok'],(source,result,p.stdout)
    mesh=trimesh.load_mesh(result['output'],process=True)
    expected=[20,20,20] if 'sphere' in source.name else [10,20,30]
    assert np.allclose(mesh.extents,expected,atol=.15),(source,mesh.extents)
    assert mesh.is_watertight,(source,'not watertight')
    results.append({'source':source.name,**result})
    print('PASS',source.name,result['triangles'],result['size_mm'],flush=True)
(root/'artifacts/package-verification.json').write_text(json.dumps(results,indent=2))
print('All packaged conversion checks passed with Python removed from PATH.')
