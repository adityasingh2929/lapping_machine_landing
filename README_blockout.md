# Lapping machine blockout

Target and executed runtime: Blender 5.2.0 LTS. Cabinet width is provisionally 1 metre; no measured scale is implied.

Open `lapping_machine_blockout.blend`. Move `LM_ROOT_Move_Complete_Machine` to move all machine parts. Studio and cameras are separate. The seven cameras cover front, rear, left, right, top, and opposing three-quarter views. All geometry is separate and named by component/station.

Edit the `C` configuration at the beginning of `generate_blockout.py` and rerun to regenerate. Station XY coordinates are defined once and shared by ring, head, shaft and cylinder. Front is -Y; rear +Y; Z is up. Upper support members in the provisional collection represent an adjustable silhouette, not verified concealed joints.

To regenerate in an existing Blender file, open the script in the Scripting workspace and Run Script, or use Blender's Python Console:

```python
path = r'C:\Users\2023a\Downloads\lapping_machine\blender_models\generate_blockout.py'
exec(compile(open(path, encoding='utf-8').read(), path, 'exec'), {'__file__': path, '__name__': '__main__'})
```

Only the `LM_BLOCKOUT` collection is rebuilt. Unrelated scene objects are preserved. Rendering, active camera, world and unit settings are configured for the blockout. Existing unrelated objects can appear in renders; hide those manually if needed. The generated blend is saved beside the script. Set `RENDER = False` to skip the seven PNG previews.

To build a fresh standalone file from PowerShell (this explicitly starts an empty scene):

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --python-expr 'import bpy; bpy.ops.wm.read_factory_settings(use_empty=True)' --python 'C:\Users\2023a\Downloads\lapping_machine\blender_models\generate_blockout.py'
```

Assertions check ring separation/plate margins, shared station alignment, positive head clearance, head-to-mount space, column/table clearance and console/column clearance. Results are in `blockout_checks.txt`. These do not constitute a general collision solver or verification of hidden machine structure. Simple paint/metal materials and modest bevels only; fasteners, labels, controls, vents, wiring, hoses and wear are intentionally deferred.
