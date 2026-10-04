# User guide

[Back to README](../README.md)

## Files and batches

Choose **Add files** or drop supported files anywhere in the window. File
pickers allow multiple selections. Add individual files, not folders. Duplicate
paths already in the queue are ignored. File types are detected from extensions.

Click **Convert** to process the current pending queue. The app captures both
that batch and its settings at startup. You can add files while it works;
those files wait for your next batch. Settings cannot change during conversion.

**Remove** takes selected entries out of the queue without deleting files.
**Clear finished** removes entries that are no longer pending, including saved,
warning, error, and stopped entries. It does not remove output files.

## Save location

**Beside original files** saves each STL in its source directory. **Selected
folder** saves all outputs in one folder; choose that folder before converting.
If `part.stl` already exists, the app tries `part (1).stl`, then `part (2).stl`.
Converting an existing STL therefore creates another file rather than replacing it.

## Adaptive settings

- **CAD surface detail** appears when pending STEP/STP/IGES/IGS files need it.
  Balanced is the default. Fine makes curved surfaces smoother at the cost of
  processing time and larger files; Fast uses fewer triangles.
- **Source units** appears for pending OBJ/PLY/OFF/STL files, which often lack
  reliable unit metadata. Choose millimetres, centimetres, inches, or metres
  according to how the source model was created. The choice applies to every
  such file in the batch; use separate batches if their units differ.
- Other supported formats use their embedded or format-defined units. For
  a 3MF-only queue, the app shows an explanation instead of irrelevant controls.
- All exports use millimetre coordinates, but STL has no unit field. Import
  the output as millimetres in your slicer.

## Results and recovery

| Status | Meaning and next action |
| --- | --- |
| Ready | Queued; click Convert when ready. |
| Converting | The current worker is processing this source. |
| Saved | STL written; select it for triangle count and dimensions. |
| Check mesh | STL written, but open edges were detected. Inspect it in your slicer. |
| Error | Conversion failed; open Details for the message. |
| Stopped | You stopped its worker; it can be queued again. |

Select one row to see its summary. Double-click or choose **Details** for paths
and the full message. **Open output** opens the selected result's folder, or
the most recent output folder when the selected row has no saved output.

**Stop** interrupts the current file and preserves completed outputs. Remaining
pending files stay ready. **Requeue failed** returns failed and stopped entries
to Ready; it does not start them. You must click Convert again. Closing the app
during a batch asks whether to stop it. The queue itself is not saved between runs.

The progress line counts completed files, not progress inside one CAD operation.
A large single file can take time without advancing the line.

## Keyboard and resizing

| Shortcut | Action |
| --- | --- |
| Ctrl+O | Add files |
| Ctrl+Enter | Start pending batch |
| Delete, while the file list has focus | Remove selected entries |
| Tab / Shift+Tab | Move between controls |
| Space, while a button has focus | Activate it |

The minimum window is 860 × 520 logical pixels. The file list and settings
scroll independently as needed; Convert and Stop stay in the footer. Status
labels use words as well as colour. Complete screen-reader compatibility and
every Windows display-scaling setting have not been certified.

## Troubleshooting

- **App will not open:** extract the entire ZIP before launching it. Do not move
  the EXE away from `_internal`. Use Windows x64. Check Windows Security's
  notification/history if the unsigned download was blocked; verify the
  checksum and source instead of disabling your security software.
- **Convert is unavailable:** add a supported file, wait for a current batch to
  finish, or choose the required output folder.
- **Wrong size:** check source units for plain meshes and import the STL as
  millimetres. CAD/3MF units come from the source file. Compare the dimensions
  in the result with your expected dimensions.
- **Missing colour or print settings:** STL cannot contain them. Keep the
  original project for those features.
- **Missing GLTF geometry:** keep local sidecar buffers with the GLTF file.
  Remote URLs are rejected. Export an embedded GLB if practical.
- **Check mesh:** open edges are a warning, not an automatic repair. Inspect or
  repair the model in your preferred CAD tool or slicer before printing.
- **CAD error or timeout:** confirm the model opens in its original CAD program,
  try Fast detail, split a large assembly, or export a supported mesh there.
- **Permission or disk error:** choose an output folder you can write to and
  confirm there is sufficient free space.

Include the app version, Windows version, source format, selected settings,
and exact error in a [bug report](https://github.com/matt-bat/convert-to-stl/issues/new?template=bug_report.yml).
Only attach model files you are permitted to share publicly.

## Privacy and data

The app reads models locally and writes STLs to your chosen location. It creates
temporary worker result files and temporary CAD intermediates; normal cleanup
removes them, though a crash or forced termination can leave temporary files.
Cancellation can leave an unfinished `.stl-*.partial` file if it interrupts the
output write. Such a file is not a completed STL.

The chosen custom output-folder path is stored using Windows QSettings under
`HKEY_CURRENT_USER\Software\MattBat\ConvertToSTL`. The app does not persist the
queue, upload models, or send telemetry. Clicking Open output launches Explorer.
Build-time dependency and license downloads are separate from app operation.
