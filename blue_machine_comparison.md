# Blue machine material update — 2026-09-26

The nine blue_machine photographs show the same overall three-station design as the saved model: triangular ring/head layout, three vertical pneumatic actuators, open overhead branches and longitudinal spine, front/rear support columns, rectangular base, projecting tabletop, and separate sloping control console. Reusing the model for a colour variant is supported. Photographs alone do not establish identical dimensions or every small fitting; the existing reconstruction remains approximate.

Materials were updated in lapping_machine_blockout.blend without changing object geometry, transforms, visibility, or object count. Original geometry digest and saved-file reopen verification are recorded in blue_machine_verification.json. Existing labels and controls are retained; matching the new machine's exact label content and hardware details was outside this material pass.

- Main panels, tabletop, and painted table supports: glossy RAL 5002, represented by the digital approximation sRGB #00387B (https://www.colorxs.com/color/ral-5002-ultramarine-blue). RGB representations of physical paint are approximate and differ between published charts; this is not a calibrated paint measurement.
- Frame, posts, feet, and overhead structure: photo-estimated pale blue-grey #829FA9.
- Console shell: photo-estimated muted blue #46658D; door and control face ivory #DBD3B7.
- Conditioning rings: warm metallic grey; lapping surface: silver grey; raised pressure heads: blackened steel; carriers: dark steel.
- Pneumatic hoses: cyan-blue; aluminium cylinders, fittings, switch colours, and grille finishes retained.

The material update is in blue_machine_materials.py, also embedded as BM_MATERIAL_SCRIPT. The normal generate_blockout.py maintenance save reapplies it when BM_blue_machine_palette is set. The existing .blend1 and alternate files were left untouched.

Current previews: blue_machine_overview.png and blue_machine_frame.png. Earlier preview images depict the former colour scheme.
