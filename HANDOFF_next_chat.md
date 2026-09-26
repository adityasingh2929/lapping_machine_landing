# Latest stop: front support review, 2026-09-16

User narrowed the remaining pass to the front block/carrier and two low-resolution previews. Saved in place. Current flags include REF_focused_working_pass, REF_focused_seating_review and REF_front_support_finish; do not reapply their deltas. Front block height 0.049, length 0.100, recessed seat 0.771, carrier top 0.785, closed counterbores diameter 0.018. Before narrowing, working-assembly progress included circular plate radius 0.330; plate and cameras were unchanged during the narrowed finish. Current unrelated console/cabinet/regulator were preserved from the on-disk pre-correction state. The full gallery was not refreshed and is not current verification. Use reference_comparisons/front_support_comparison_15.jpg and front_support_comparison_16.jpg. Rear carrier outline/edge radii and unrelated working-assembly discrepancies remain approximate. Stop here for user review.

# Lapping-machine handoff — sixteen-view review delivered, discrepancies remain

## Acceptance and single working files

Acceptance requires visual agreement across all sixteen original photographs. Presentation quality, rendering/reopening and low landmark residuals do not establish fidelity. Comparisons are delivered for review; do not call the reconstruction an exact match or complete while documented visible mismatches remain.

- Save in place: C:/Users/2023a/Downloads/lapping_machine/blender_models/lapping_machine_blockout.blend.
- Maintain generate_blockout.py in that directory. It incrementally preserves existing objects; do not restart reconstruction.
- Preserve compatible manual details; correct geometry where supported by photographs.
- Do not create alternate/versioned models or use/modify v02 files. Leave unrelated backups untouched.
- Originals: ../1.jpeg through ../16.jpeg. REF_14 preserves the sideways orientation in photo 14's portrait file.

## Authoritative current evidence

Read reference_discrepancy_report.md, reference_saved_verification.json, reference_geometry_changes.json, reference_review_notes.json and reference_comparisons/index.html. The gallery's render_manifest.json ties each PNG to source/saved-scene hashes, a common geometry digest and its camera.

At this resume, the saved scene had old geometry and no reference cameras/flags despite later-looking historical renders/logs. reference_resume_audit.json records that state. Corrections were applied once from the audited base. Re-audit the actual .blend before future edits; renders and fit logs alone are not saved-state evidence.

Saved flags: REF_geometry_pass_1, _2, _3, _4, REF_grille_mount_review, REF_hose_clearance_review. Do not clear them or apply deltas again. All sixteen cameras are saved; the current script is embedded as LM_GENERATION_SCRIPT.

## Current geometry, provisional where photos disagree

Front = -Y, rear = +Y, Z up; root LM_ROOT_Move_Complete_Machine. Cabinet-width 1.0 is an arbitrary scale convention.

- Stations: (0, -0.17974), (-0.15566, 0.08987), (+0.15566, 0.08987).
- Ring OD 0.290; head lower OD 0.252, step OD 0.14003; head/ring clearance 0.111.
- Heads/cylinder tops +0.038 from original; beam/column caps only +0.0055. Mount plates 0.230 x 0.2197 x 0.012.
- Console width x0.94, depth x0.826, Y +0.069 about -0.84, height x0.90 with floor fixed. Grilles corrected separately.
- Roller/carrier and later S1 bolt/slot changes are recorded in the change JSON. Front support shape still differs visibly.
- Hose bends accommodate enlarged mounts; hidden routing remains approximate.

Historical 0.033/0.936 correction values and requirements to preserve all original bounds are superseded. Some meshes use world-space vertices despite zero object origins: use world/evaluated bounds, not translation alone.

## Repeatable workflow

Blender: C:/Program Files/Blender Foundation/Blender 5.2/blender.exe.
Python with NumPy/SciPy/Pillow: C:/Users/2023a/anaconda3/python.exe.

Load the single .blend in Blender background mode and run generate_blockout.py:

- -- --reference-pass: refresh cameras from JSON, save in place, render all 16.
- -- --reference-pass --no-render: refresh cameras/embed script/save without renders.
- -- --reference-pass --apply-reference-corrections: apply missing guarded stages; current saved stages do not reapply.
- --reference-views=9,13,15,16 optionally restricts renders. All delivery renders must share the final geometry; check manifest.
- -- --no-render alone: ordinary maintenance, tested successfully on corrected scene. It saves in place and preserves existing details. Deleting named details can invoke old construction defaults; inspect deliberate rebuilds.

reference_analysis.py --gallery generates original/render/50% overlay triptychs. Its camera fitter, --bundle and --console-fit are diagnostics; do not automatically apply their results. Camera JSON holds the latest reviewed fits. Per-camera aspect is stored as custom properties; switching active camera alone does not change scene resolution.

verify_reference_scene.py does not save the .blend. It checks cameras, station alignment, retained objects, embedded script and extra feature projections, writing reference_saved_verification.json. The ordinary maintenance hose sampler now transforms curve points into root coordinates before checking structure.

## Remaining fidelity work

Prioritize front support/carrier section and working-plate contour in 15-16, console housing/side controls in 4/9/10/13, pneumatic details in 12, then louvres and lettering. Separate camera depth ambiguity (especially 12/14/15/16) from geometry. Cameras 12/14 reach optical bounds. Never change a part per camera.

Foot observations were not camera-fit inputs. Grille/bolt checks later informed geometry and are no longer untouched holdouts. Inspect contours and additional unused features. Hidden beam joints and hose routes remain provisional.

The four older finished_*.png presentation renders predate this fidelity pass. Use the current 16-view gallery/report for validation.
