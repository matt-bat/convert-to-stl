# Formats and limitations

[Back to README](../README.md)

| Input | Supported behavior | Units / settings |
| --- | --- | --- |
| 3MF | Core triangle meshes, build/component transforms, repeated instances, production-extension cross-file components | Embedded units; non-printable build items omitted |
| STEP / STP | Open CASCADE surface tessellation and transferred multi-part geometry | Embedded units converted to mm; CAD detail applies |
| IGES / IGS | Open CASCADE surface tessellation | Embedded units converted to mm; CAD detail applies |
| OBJ / PLY / OFF | Supported polygon/triangle meshes through trimesh | User-selected units; mm by default |
| GLB / GLTF | Mesh instances flattened with transforms; embedded or local buffers | Standard metres converted to mm |
| AMF | Ordinary triangle meshes; a single AMF model inside a ZIP is also accepted | Embedded units |
| STL | Binary rewriting and scaling | User-selected units; original preserved |

Every source produces **one binary STL**. Disconnected components remain
disconnected; the converter does not perform a boolean union. It does not split
an assembly into one STL per object. Materials, colours, textures, slicer
settings, names/hierarchy, and parametric history are not retained in STL.

## CAD detail

| Preset | Linear deflection | Angular deflection |
| --- | --- | --- |
| Fast | 0.3 mm | 0.5 radians |
| Balanced | 0.1 mm | 0.3 radians |
| Fine | 0.03 mm | 0.15 radians |

These control surface tessellation, not a guaranteed final dimensional-error
bound. Existing mesh formats retain their triangles. Collapsed zero-area CAD
pole triangles are discarded; this is not a general mesh repair operation.

## Important exclusions

- 3MF beam-lattice and volumetric mesh geometry are unsupported. Vendor-specific
  extensions are not generally implemented. Slicer projects may contain helper
  objects or modifiers; inspect the assembled output before printing.
- AMF constellations and curved-triangle definitions are rejected.
- GLTF remote, absolute, or parent-traversing dependency paths are rejected;
  supported relative sidecar files must remain with the model.
- Point clouds, curves, empty scenes, protected files, native Fusion/SolidWorks
  projects, G-code, and arbitrary CAD formats are not supported.
- Open-edge warnings do not detect every printability problem. Watertightness
  alone does not prove that a model is suitable for printing.

## Resource limits

| Check | Limit |
| --- | --- |
| Source file | 2 GiB |
| Expanded 3MF archive | 1 GiB |
| AMF entry in ZIP | 1 GiB (strictly smaller) |
| 3MF mesh instances | 10,000 |
| Output triangles | 20 million |
| GUI worker time | 20 minutes per source |

Available memory may impose a lower practical limit. Some geometry limits are
checked after parsing, so they are not a hard process-memory cap. Native readers
run in a separate worker process to isolate failures, not in an OS security
sandbox. Representative generated models are tested; compatibility with every
exporter, extension, or malformed input is not claimed.
