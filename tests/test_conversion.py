from pathlib import Path
import json
import zipfile
import numpy as np
import pytest
import trimesh
from converter import convert, ConversionError

@pytest.fixture
def box(): return trimesh.creation.box(extents=[10,20,30])

def assert_size(result, expected):
    mesh=trimesh.load_mesh(result['output'],process=True)
    assert np.allclose(mesh.extents,expected,rtol=1e-5,atol=1e-3)
    assert mesh.is_watertight
    assert result['triangles']>=12

@pytest.mark.parametrize('ext',['obj','ply','off','glb','gltf','3mf'])
def test_mesh_formats(tmp_path,box,ext):
    file=tmp_path/('box.'+ext)
    model=box.copy()
    if ext in ('glb','gltf'): model.apply_scale(.001)
    payload=model.export(file_type=ext)
    if isinstance(payload,dict):
        for name,value in payload.items(): (tmp_path/name).write_bytes(value)
        file=tmp_path/'model.gltf'
    elif isinstance(payload,str): file.write_text(payload)
    else: file.write_bytes(payload)
    assert_size(convert(file),[10,20,30])

def test_units_and_collision(tmp_path,box):
    file=tmp_path/'日本語 cube.obj';box.export(file)
    first=convert(file,unit='inch');before=Path(first['output']).read_bytes()
    second=convert(file,unit='inch')
    assert first['output']!=second['output']
    assert Path(first['output']).read_bytes()==before
    assert_size(second,[254,508,762])

@pytest.mark.parametrize('ext',['step','iges'])
def test_cad(tmp_path,ext):
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
    shape=BRepPrimAPI_MakeBox(10,20,30).Shape()
    file=tmp_path/('cube.'+ext)
    if ext=='step':
        from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
        writer=STEPControl_Writer();writer.Transfer(shape,STEPControl_AsIs);writer.Write(str(file))
    else:
        from OCP.IGESControl import IGESControl_Writer
        writer=IGESControl_Writer('MM',0);writer.AddShape(shape);writer.Write(str(file))
    assert_size(convert(file),[10,20,30])

def test_3mf_assembly(tmp_path,box):
    vertices=''.join(f'<vertex x="{x}" y="{y}" z="{z}"/>' for x,y,z in box.vertices)
    faces=''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a,b,c in box.faces)
    xml=f'''<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" unit="inch"><resources>
    <object id="1"><mesh><vertices>{vertices}</vertices><triangles>{faces}</triangles></mesh></object>
    <object id="2"><components><component objectid="1"/><component objectid="1" transform="1 0 0 0 1 0 0 0 1 20 0 0"/></components></object>
    </resources><build><item objectid="2" transform="1 0 0 0 1 0 0 0 1 5 0 0"/><item objectid="1" printable="0" transform="1 0 0 0 1 0 0 0 1 1000 0 0"/></build></model>'''
    file=tmp_path/'assembly.3mf'
    with zipfile.ZipFile(file,'w') as z:z.writestr('3D/3dmodel.model',xml)
    result=convert(file);assert_size(result,[762,508,762])
    loaded=trimesh.load_mesh(result['output']);assert np.isclose(loaded.bounds[0,0],0)
    assert result['triangles']==24

def test_3mf_external_component(tmp_path,box):
    vertex=''.join(f'<vertex x="{x}" y="{y}" z="{z}"/>' for x,y,z in box.vertices)
    faces=''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a,b,c in box.faces)
    file=tmp_path/'production.3mf'
    with zipfile.ZipFile(file,'w') as z:
        z.writestr('_rels/.rels','<Relationships><Relationship Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" Target="/3D/main.model"/></Relationships>')
        z.writestr('3D/main.model','<model xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06"><resources><object id="1"><components><component objectid="2" p:path="/3D/Objects/part.model" transform="1 0 0 0 1 0 0 0 1 40 0 0"/></components></object></resources><build><item objectid="1"/></build></model>')
        z.writestr('3D/Objects/part.model',f'<model><resources><object id="2"><mesh><vertices>{vertex}</vertices><triangles>{faces}</triangles></mesh></object></resources><build/></model>')
    r=convert(file);assert_size(r,[10,20,30]);assert np.isclose(trimesh.load_mesh(r['output']).centroid[0],40)

def test_amf(tmp_path,box):
    verts=''.join(f'<vertex><coordinates><x>{x}</x><y>{y}</y><z>{z}</z></coordinates></vertex>' for x,y,z in box.vertices)
    tris=''.join(f'<triangle><v1>{a}</v1><v2>{b}</v2><v3>{c}</v3></triangle>' for a,b,c in box.faces)
    f=tmp_path/'box.amf';f.write_text(f'<amf unit="millimeter"><object id="0"><mesh><vertices>{verts}</vertices><volume>{tris}</volume></mesh></object></amf>')
    assert_size(convert(f),[10,20,30])

def test_corrupt_file(tmp_path):
    file=tmp_path/'bad.3mf';file.write_bytes(b'not a model')
    with pytest.raises(Exception):convert(file)
    assert not list(tmp_path.glob('*.stl'))

def test_remote_gltf_rejected(tmp_path):
    file=tmp_path/'remote.gltf';file.write_text(json.dumps({'buffers':[{'uri':'https://example.com/model.bin'}]}))
    with pytest.raises(ConversionError,match='local'):convert(file)

def test_open_mesh_warns(tmp_path):
    file=tmp_path/'triangle.obj';file.write_text('v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n')
    assert 'Open edges' in convert(file)['warning']

def test_original_stl_not_overwritten(tmp_path,box):
    file=tmp_path/'box.stl';box.export(file);original=file.read_bytes()
    result=convert(file)
    assert Path(result['output'])!=file
    assert file.read_bytes()==original

def test_cad_sphere_poles(tmp_path):
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeSphere
    from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
    p=tmp_path/'sphere.step'
    w=STEPControl_Writer();w.Transfer(BRepPrimAPI_MakeSphere(10).Shape(),STEPControl_AsIs);w.Write(str(p))
    r=convert(p)
    m=trimesh.load_mesh(r['output'],process=True)
    assert m.is_watertight
    assert np.allclose(m.extents,[20,20,20],atol=.15)
    assert not r['warning']

def test_step_inch_units(tmp_path):
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
    from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
    from OCP.Interface import Interface_Static
    p=tmp_path/'inch-unit.step'
    writer=STEPControl_Writer()
    Interface_Static.SetCVal_s('write.step.unit','INCH')
    try:
        # This writer emits unscaled coordinates with the chosen unit declaration.
        # A 1 x 2 x 3 coordinate box declared INCH is 25.4 x 50.8 x 76.2 mm.
        writer.Transfer(BRepPrimAPI_MakeBox(1,2,3).Shape(),STEPControl_AsIs)
        writer.Write(str(p))
    finally:
        Interface_Static.SetCVal_s('write.step.unit','MM')
    assert 'INCH' in p.read_text().upper()
    assert_size(convert(p),[25.4,50.8,76.2])
