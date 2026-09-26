# Sixteen-photo fidelity review

The 16-view gallery has been produced and inspected. **Visible discrepancies remain; this is not an exact-match or reconstruction-complete claim.** Acceptance remains visual agreement with the machine across all sixteen photographs, subject to user review.

Working file: `lapping_machine_blockout.blend`. Dimensions below use provisional cabinet-width = 1.0 units, not measured metres.

## Actual saved geometry changes

| Saved change from audited original geometry | Photo evidence and cross-checks |
|---|---|
| Head bottoms raised 0.038; ring-to-head clearance 0.073 → 0.111. Beam and column caps raised separately by only 0.0055. Columns, shafts, cylinders and branches adjusted to retain continuous aligned assemblies. | Overview silhouettes 1–11; gaps and underside connections 15–16. |
| Triangular station radius ×0.946: front Y = −0.17974; rear X = ±0.15566, Y = 0.08987. Ring/head/cylinder/mount centers remain vertically aligned. | Relative overlaps and spacing in 1–11, 15–16. |
| Lower head disk diameter 0.280 → 0.252; raised step 0.190 → 0.14003; flange/hub footprints reduced. Ring OD retained at 0.290. | Head-to-ring silhouettes in 15–16, checked in overviews. |
| Underside plates enlarged from 0.125 × 0.130 to 0.230 × 0.2197; slots and fasteners relocated. | Exposed undersides in 15–16; overview clearances. |
| Console width ×0.94, depth ×0.826 about Y = −0.84, shifted +0.069 in Y, height ×0.90 with floor fixed. Existing controls retained and relocated. Both side grilles moved +0.040 in Y; upper/lower groups raised 0.085/0.040. Upper grille faces brought 0.018 outward with extended frame backs. | Console projection in 1–5, 9–11; grilles in 4–5, 9–10, 13; panel in 14. |
| Roller pairs/carriers repositioned with shared stations. Rollers rotated 90°; carriers 74°. Front fasteners subsequently moved along carrier using both close-ups; slot/support shortened and repositioned with pair. | 15–16 directly; visibility rechecked in 1, 3–5, 9–10. Other stations' hardware remains less certain. |
| Regulator knob extended 0.019. S1 hose bend and approximate cross-link rerouted around enlarged plates, retaining endpoints; link diameter 0.005. | Knob silhouette in 12. Hose changes accommodate corrected structure; exact obscured route is not established by photographs. |

No original objects were deleted. Saved one-time flags prevent double application; an explicit correction rerun left geometry unchanged. Historical 0.033 head shift / 0.936 station factor are superseded, not additional final corrections.

## Remaining visible geometry/detail mismatches

- **15–16:** front support block is too shallow/simplified; carrier section, slot ends, ring cuts and working-plate outline differ. Rear-head overlap and some head/shaft profiles still differ. Improved bolt placement does not resolve these contours.
- **1–5, 9–11, 13:** console lower outline/forward projection retains offsets. Grille sizes, lower-grille height, sockets, isolator, door latches and panel hardware are approximate.
- **6–8, 12:** regulator/lubricator fittings, clear adjuster, gauge artwork and hose bends differ. Hanging cables and external supply length are incomplete.
- Cabinet louvres, small fasteners, bevels, labels and badges remain simplified. Neutral studio lighting does not reproduce workshop reflections or wear.

## Camera and hidden-geometry uncertainty

REF_01–REF_16 map directly to `1.jpeg`–`16.jpeg`. Photo 14 retains its sideways orientation and portrait aspect; 15–16 are landscape. No JPEG was rotated to disguise alignment.

Overview cameras use common structural landmarks; console observations were excluded from those fits. Close-ups have fewer stable depth cues: 12 and 14 reach focal-length bounds, so their lens/pose estimates are not calibrated. Circle-center/ellipse approximations and cropping affect 15–16. These ambiguities can contribute to silhouette offsets and do not justify deforming parts independently per view.

Concealed beam joints, internal machinery, hidden pneumatic circuit and obscured support sections remain provisional.

## Validation and saved-state evidence

All 16 originals, renders and 50% overlays were inspected, including additional table edges, feet, grilles, controls, fasteners and support silhouettes beyond camera-fit landmarks. Unfitted foot picks in 1–11 differ by approximately 4–26 pixels at the 1368 × 1824 preview scale; manual picks themselves are approximate. Grille and bolt observations subsequently guided corrections and are no longer untouched holdout evidence. Improved residuals do not establish full fidelity.

The single saved `.blend` was reopened and audited for all 16 camera mappings/transforms, aligned station centers, 0.111 clearance, retained objects and an embedded script matching `generate_blockout.py`. Normal maintenance passed preservation, duplicate, ring-opening and sampled hose-clearance checks. Evidence: `reference_saved_verification.json`, `reference_geometry_changes.json`, `reference_maintenance_rerun_log.txt`, and the gallery's `render_manifest.json`. Every final render uses one common geometry; only cameras and aspect change. Workshop pixels were excluded from assessment, not used in a whole-image error score.
