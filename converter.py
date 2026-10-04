"""Local conversion engines. No network access or external applications required."""
from pathlib import Path, PurePosixPath
import math
import os
import shutil
import tempfile
import zipfile
import numpy as np
import trimesh
from defusedxml import ElementTree as ET

SUPPORTED = {'.3mf', '.step', '.stp', '.iges', '.igs', '.obj', '.ply', '.off', '.glb', '.gltf', '.amf', '.stl'}
UNITS = {'micron': .001, 'millimeter': 1., 'centimeter': 10., 'meter': 1000., 'inch': 25.4, 'foot': 304.8}
QUALITY = {'Fast': (.3, .5), 'Balanced': (.1, .3), 'Fine': (.03, .15)}

class ConversionError(ValueError):
    pass

def local_name(tag):
    return tag.rsplit('}', 1)[-1]

def children(element, name):
    return [c for c in element if local_name(c.tag) == name]

def child(element, name):
    found = children(element, name)
    if not found:
        raise ConversionError(f'Missing {name} in model.')
    return found[0]

def transform(value):
    result = np.eye(4)
    if value:
        nums = np.array([float(v) for v in value.split()])
        if len(nums) != 12 or not np.isfinite(nums).all():
            raise ConversionError('Invalid 3MF transform.')
        result[:3, :] = nums.reshape(4, 3).T
    return result

def mesh_checked(vertices, faces):
    vertices = np.asarray(vertices, dtype=float)
    faces = np.asarray(faces, dtype=np.int64)
    if vertices.ndim != 2 or vertices.shape[1] != 3 or not len(vertices) or not np.isfinite(vertices).all():
        raise ConversionError('The model has missing or invalid vertices.')
    if faces.ndim != 2 or faces.shape[1] != 3 or not len(faces) or faces.min() < 0 or faces.max() >= len(vertices):
        raise ConversionError('The model has missing or invalid triangles.')
    return trimesh.Trimesh(vertices=vertices, faces=faces, process=False)

def read_3mf(path):
    """Core + production-extension components, units, instances and build transforms."""
    parts = []
    with zipfile.ZipFile(path) as archive:
        if sum(i.file_size for i in archive.infolist()) > 1024**3:
            raise ConversionError('This 3MF expands beyond the 1 GB safety limit.')
        docs = {}
        def normalized(name, base=''):
            if ':' in name or '\\' in name:
                raise ConversionError('Unsupported 3MF resource path.')
            # Production paths normally start at the package root.
            raw = name.lstrip('/') if name.startswith('/') else str(PurePosixPath(base).parent / name) if base else name
            segments = []
            for segment in raw.split('/'):
                if segment == '..':
                    if not segments: raise ConversionError('Invalid 3MF resource path.')
                    segments.pop()
                elif segment not in ('', '.'): segments.append(segment)
            return '/'.join(segments)
        def doc(name):
            if name not in docs:
                try: root = ET.fromstring(archive.read(name))
                except KeyError: raise ConversionError(f'Missing 3MF resource: {name}')
                unit = root.get('unit', 'millimeter')
                if unit not in UNITS: raise ConversionError(f'Unknown 3MF unit: {unit}')
                resources = child(root, 'resources')
                docs[name] = (root, {o.get('id'): o for o in children(resources, 'object')}, UNITS[unit])
            return docs[name]
        try:
            relationships = ET.fromstring(archive.read('_rels/.rels'))
            targets = [r.get('Target') for r in relationships if r.get('Type', '').endswith('/3dmodel') and r.get('TargetMode') != 'External']
            main = normalized(targets[0]) if targets else '3D/3dmodel.model'
        except KeyError:
            main = '3D/3dmodel.model'
        root, objects, scale = doc(main)
        def expand(name, oid, placement, stack):
            key = (name, oid)
            if key in stack or len(stack) > 80:
                raise ConversionError('The 3MF contains circular or excessively nested components.')
            _, objs, unit_scale = doc(name)
            if oid not in objs: raise ConversionError(f'Missing 3MF object {oid}.')
            obj = objs[oid]
            meshes = children(obj, 'mesh')
            components = children(obj, 'components')
            if meshes:
                m = meshes[0]
                if any(local_name(e.tag) in ('beamlattice', 'volumedata') for e in m.iter()):
                    raise ConversionError('Beam/volume 3MF geometry is not supported; export a triangle mesh first.')
                verts = [[float(v.get(k)) for k in ('x','y','z')] for v in child(m, 'vertices')]
                faces = [[int(t.get(k)) for k in ('v1','v2','v3')] for t in child(m, 'triangles')]
                mesh = mesh_checked(verts, faces)
                mesh.apply_scale(unit_scale)
                mesh.apply_transform(placement)
                parts.append(mesh)
                if len(parts) > 10000: raise ConversionError('Too many 3MF instances (limit 10,000).')
            elif components:
                for component in components[0]:
                    subpath = next((v for k,v in component.attrib.items() if local_name(k) == 'path'), None)
                    target = normalized(subpath, name) if subpath else name
                    local = transform(component.get('transform'))
                    local[:3, 3] *= unit_scale
                    expand(target, component.get('objectid'), placement @ local, stack | {key})
            else:
                raise ConversionError(f'3MF object {oid} has no supported triangle geometry.')
        for item in child(root, 'build'):
            if item.get('printable', '1').lower() in ('0', 'false'): continue
            placement = transform(item.get('transform'))
            placement[:3, 3] *= scale
            subpath = next((v for k,v in item.attrib.items() if local_name(k) == 'path'), None)
            expand(normalized(subpath, main) if subpath else main, item.get('objectid'), placement, set())
    if not parts: raise ConversionError('The 3MF has no printable build objects.')
    return trimesh.util.concatenate(parts)

def read_amf(path):
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            entries = [i for i in z.infolist() if i.filename.lower().endswith('.amf')]
            if len(entries) != 1 or entries[0].file_size > 1024**3:
                raise ConversionError('Expected one AMF model, smaller than 1 GB, inside the archive.')
            root = ET.fromstring(z.read(entries[0]))
    else:
        root = ET.parse(path).getroot()
    if children(root, 'constellation'):
        raise ConversionError('AMF constellations are not supported yet. Export an assembled mesh as 3MF or OBJ.')
    unit = root.get('unit', 'millimeter')
    if unit not in UNITS: raise ConversionError(f'Unknown AMF unit: {unit}')
    parts = []
    for obj in children(root, 'object'):
        mesh = child(obj, 'mesh')
        vertices = [[float(child(child(v, 'coordinates'), k).text) for k in ('x','y','z')] for v in child(mesh,'vertices')]
        if any(local_name(e.tag) in ('edge', 'normal', 'nx', 'ny', 'nz') for e in mesh.iter()):
            raise ConversionError('Curved AMF triangles are not supported. Export a tessellated mesh first.')
        for volume in children(mesh, 'volume'):
            faces = [[int(child(t,k).text) for k in ('v1','v2','v3')] for t in children(volume, 'triangle')]
            parts.append(mesh_checked(vertices, faces))
    if not parts: raise ConversionError('No triangle geometry found in AMF.')
    result = trimesh.util.concatenate(parts)
    result.apply_scale(UNITS[unit])
    return result

def read_cad(path, quality):
    from OCP.STEPControl import STEPControl_Reader
    from OCP.IGESControl import IGESControl_Reader
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.Interface import Interface_Static
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.StlAPI import StlAPI_Writer
    # Native CAD readers are most reliable with ASCII filenames.
    with tempfile.TemporaryDirectory(prefix='stl_cad_') as folder:
        staged = Path(folder) / ('input' + path.suffix.lower())
        shutil.copyfile(path, staged)
        reader = STEPControl_Reader() if path.suffix.lower() in ('.step','.stp') else IGESControl_Reader()
        Interface_Static.SetCVal_s('xstep.cascade.unit', 'MM')
        if reader.ReadFile(str(staged)) != IFSelect_RetDone:
            raise ConversionError('The CAD file could not be read. Check it opens in your CAD application.')
        if reader.TransferRoots() == 0:
            raise ConversionError('The CAD file contains no transferable geometry.')
        shape = reader.OneShape()
        if shape.IsNull(): raise ConversionError('The CAD file contains no shape.')
        linear, angular = QUALITY[quality]
        tessellation = BRepMesh_IncrementalMesh(shape, linear, False, angular, True)
        if not tessellation.IsDone(): raise ConversionError('CAD surface meshing did not complete.')
        target = Path(folder) / 'mesh.stl'
        writer = StlAPI_Writer()
        writer.ASCIIMode = False
        if not writer.Write(shape, str(target)):
            raise ConversionError('The CAD surfaces could not be converted into triangles.')
        mesh = trimesh.load_mesh(target, process=False)
        # CAD pole triangulations may contain collapsed triangles; discard only
        # zero-area faces, preserving all nondegenerate surface geometry.
        mesh.update_faces(mesh.nondegenerate_faces(height=0))
        return mesh

def read_mesh(path, unit):
    # Never ask trimesh to fetch URI dependencies. Local sidecar buffers are supported.
    if path.suffix.lower() == '.gltf':
        import json
        payload = json.loads(path.read_text(encoding='utf-8-sig'))
        for group in ('buffers','images'):
            for item in payload.get(group, []):
                uri = item.get('uri','')
                if uri and not uri.startswith('data:') and (':' in uri or uri.startswith(('/', '\\')) or '..' in PurePosixPath(uri).parts):
                    raise ConversionError('GLTF dependencies must be embedded or local files beside the model.')
    scene = trimesh.load_scene(path, process=False, allow_remote=False, skip_materials=True)
    if not scene.geometry: raise ConversionError('No geometry was found.')
    if any(not isinstance(g, trimesh.Trimesh) for g in scene.geometry.values()):
        raise ConversionError('The file contains non-mesh geometry. Export triangulated surfaces first.')
    mesh = scene.to_mesh()
    mesh.apply_scale(1000. if path.suffix.lower() in ('.glb','.gltf') else UNITS[unit])
    return mesh

def convert(source, output_dir=None, quality='Balanced', unit='millimeter'):
    source = Path(source).resolve()
    if not source.is_file(): raise ConversionError('The input file no longer exists.')
    if source.suffix.lower() not in SUPPORTED: raise ConversionError('This file type is not supported.')
    if source.stat().st_size > 2 * 1024**3: raise ConversionError('This file exceeds the 2 GB input limit.')
    if quality not in QUALITY or unit not in UNITS: raise ConversionError('Invalid conversion settings.')
    suffix = source.suffix.lower()
    if suffix == '.3mf': mesh = read_3mf(source)
    elif suffix == '.amf': mesh = read_amf(source)
    elif suffix in ('.step','.stp','.iges','.igs'): mesh = read_cad(source, quality)
    else: mesh = read_mesh(source, unit)
    mesh = mesh_checked(mesh.vertices, mesh.faces)
    if len(mesh.faces) > 20_000_000: raise ConversionError('The mesh exceeds the 20 million triangle limit.')
    warning = ''
    # Welding a copy permits topology inspection without changing the delivered geometry.
    check = mesh.copy()
    check.merge_vertices()
    if not check.is_watertight:
        warning = 'Open edges detected; check the STL in your slicer before printing.'
    folder = Path(output_dir).resolve() if output_dir else source.parent
    folder.mkdir(parents=True, exist_ok=True)
    payload = trimesh.exchange.stl.export_stl(mesh)
    fd, temp = tempfile.mkstemp(prefix='.stl-', suffix='.partial', dir=folder)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        for i in range(10000):
            destination = folder / (source.stem + (f' ({i})' if i else '') + '.stl')
            try:
                # Windows rename is atomic and refuses to replace an existing file.
                if os.name == 'nt': os.rename(temp, destination)
                else:
                    os.link(temp, destination)
                    os.unlink(temp)
                break
            except FileExistsError: continue
        else: raise ConversionError('Too many files with the same output name.')
    finally:
        if os.path.exists(temp): os.unlink(temp)
    return {'output':str(destination), 'triangles':len(mesh.faces),
            'size_mm':[round(float(n),3) for n in mesh.extents], 'warning':warning}
