"""Make small, known-dimension models for packaged-app verification."""
from pathlib import Path
import shutil
import trimesh
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeSphere
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCP.IGESControl import IGESControl_Writer
root=Path('samples');root.mkdir(exist_ok=True)
box=trimesh.creation.box(extents=[10,20,30])
for ext in ('obj','ply','off','3mf'):
    box.export(root/f'box-10x20x30.{ext}')
m=box.copy();m.apply_scale(.001);m.export(root/'box-10x20x30.glb')
for name,shape in [('box-10x20x30',BRepPrimAPI_MakeBox(10,20,30).Shape()),('sphere-diameter-20',BRepPrimAPI_MakeSphere(10).Shape())]:
    writer=STEPControl_Writer();writer.Transfer(shape,STEPControl_AsIs);writer.Write(str(root/(name+'.step')))
writer=IGESControl_Writer('MM',0);writer.AddShape(BRepPrimAPI_MakeBox(10,20,30).Shape());writer.Write(str(root/'box-10x20x30.iges'))
