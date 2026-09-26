# Lapping machine blockout v02

Blender 5.2.0 LTS. All lengths below are provisional metres under the convention **cabinet width = 1.0 m**. None is a measured machine dimension. V01's script and blend remain unchanged; their SHA-256 hashes were recorded before this pass.

## Changes and evidence

| Dimension | v01 | v02 | Basis |
|---|---:|---:|---|
| Ring rim to head underside clearance | 0.073 | 0.125 | 15–16 show a substantial open band; 4, 6, 10 support more space than v01. Exact gap remains an estimate. |
| Exposed silver shaft length | 0.044 | 0.030 | 15–16 show relatively short silver connections above the black hubs. |
| Ring wall, radial thickness | 0.022 | 0.018 | Slightly wider visible opening relative to outer diameter in 15–16; checked against full views. |
| Ring height | 0.083 | 0.075 | Slightly lower height/diameter ratio better fits the side walls in 4, 10, 15–16. |
| Head lower disk diameter | 0.280 | 0.270 | Disks appear somewhat smaller than ring outside diameters in the close-ups. Conservative reduction, not a direct pixel-ratio measurement. |
| Longitudinal member width | 0.085 | 0.115 | Broader support face over the station mounting plates, consistent with the underside views. |
| Lateral member depth along Y | 0.085 | 0.145 | Broader station support footprint; separate offset branches remain at the shared station Y coordinate. |
| Underside mounting plate X × Y | 0.125 × 0.130 | 0.205 × 0.190 | Plates in 15–16 occupy much more of the head diameter than v01 represented. |
| Console upper housing depth | 0.420 | 0.400 | Reduced rear bulk; compared with 4, 10, 13. |
| Console front fascia height | 0.080 | 0.055 | Shallower overhanging front lip visible in those views. |
| Console rear housing height | 0.210 | 0.140 | Removes the excessive solid wedge depth from v01. |
| Console panel angle from horizontal | 17.2° | 12.0° | Provisional gentler slope, separating camera foreshortening from geometry. |
| Console rear top elevation | 0.700 | 0.655 | Consequence of the revised slope and housing depth. Front top remains 0.570. |
| Console housing bottom elevation | 0.490 | 0.515 | Produces the thinner front fascia. |
| Console lower cabinet top | 0.510 | 0.530 | Keeps the lower cabinet connected to the revised upper enclosure. |
| Console housing center Y | −0.840 | −0.865 | Moves overhang toward the operator. Lower cabinet center stays −0.840; X stays zero. |
| Housing overhang, front / rear | 0.040 / 0.040 | 0.055 / 0.005 | A more pronounced forward projection and reduced rear projection. |

The head disks, steps, flanges, hubs and cylinders are not stretched. The desired head clearance and short shaft length now determine the mounting plate, beam, column-top and cylinder elevations as a connected stack. Derived elevations: ring rim **0.830 → 0.822**, head underside **0.903 → 0.947**, beam underside **1.055 → 1.085**, cylinder top **1.395 → 1.425**. Main head stack height and cylinder length remain unchanged.

## Retained assumptions

The working plate diameter stays **0.730**, ring outside diameter **0.290**, and all three station XY coordinates stay exactly **(0, −0.190), (−0.164545, 0.095), (+0.164545, 0.095)**. The plate still provides 0.030 edge margin and approximately 0.03909 separation between rings. Cabinet, tabletop and front/rear column spacing remain unchanged.

The photographs establish front/rear centerline columns, lateral station offsets and broad individual underside plates. They do **not** conclusively establish the hidden beam fabrication. V02 retains the simple longitudinal member with two lateral branches, broadens their visible footprint, and uses touching end connections without overlapping top faces. It does not claim a verified concealed spine, weld detail or internal load path. Beam height remains 0.085. No extra diagonal members or internal mechanisms were invented.

## Review presentation

Medium-grey paint, warm cream panels, dark working metal and silver cylinders are separate simple materials. Lower direct-light levels and a neutral, gently self-lit studio floor make the parts easier to distinguish without the washed-out v01 appearance. The studio is presentation-only.

Eight renders are supplied: front/side/top orthographic checks, console-facing and side perspective views, opposing three-quarter perspectives, and a low close-up approximating 16.jpeg. Camera numbers indicate comparison references, not calibrated camera matches. The close-up deliberately crops the overall machine; every full-machine camera has a numerical framing check. Geometry is identical across all cameras.

The blend opens in a three-quarter material-preview modeling view. Camera/light/floor objects are hidden only in the viewport and remain enabled for rendering. Extras and relationship lines are hidden. The root marker is hidden independently of its visible children; select `LM_ROOT_Move_Complete_Machine` in the Outliner to move the assembly.

## Running and checking

Use `generate_blockout_v02.py` in Blender 5.2's Scripting workspace, or run:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --python-expr 'import bpy; bpy.ops.wm.read_factory_settings(use_empty=True)' --python 'C:\Users\2023a\Downloads\lapping_machine\blender_models\generate_blockout_v02.py'
```

The explicit empty-scene option above is for a fresh standalone build. Running the script in an existing scene only replaces `LM_BLOCKOUT`; unrelated objects are preserved. It configures world, rendering and viewport settings. Edit `C` near the start; beam elevation is derived immediately below it. `RENDER = False` skips previews; `SAVE = False` is available for non-saving validation.

Generation checks retain ring fit/separation, shared head/shaft/cylinder alignment, positive clearance, available hub/shaft height, column/table clearance and console/column clearance. `verify_rebuild_v02.py` additionally checks the saved viewport configuration, visible machine geometry, viewport-only presentation hiding, ring manifold topology/open inner radius, and preservation of an unrelated sentinel during rebuilding. Results are saved in `blockout_v02_checks.txt` and `verification_v02.txt`.

These are geometry-review checks, not a fabrication validation or a complete collision solver. Fine controls, bolts, labels, hoses, wiring and surface wear remain deferred.

## Execution result

Executed the complete v02 script in Blender 5.2.0 LTS using Eevee and inspected all eight rendered viewpoints. The close-up confirmed the more open head/ring spacing; side views confirmed the shallower console profile. The first full-machine perspective camera heights were too high relative to the cylinder tops, so those cameras were lowered without changing the geometry. The review background was lightened independently of the machine's direct lighting.

Reopened the saved blend in Blender for validation. All assertions passed, including visible machine meshes, material-preview/perspective viewport settings, hidden presentation outlines, hollow manifold rings and preservation of an unrelated object across regeneration. Generated object count remained 116. V01 script and blend SHA-256 hashes match the pre-edit values.
