# Code, modification and rebuild guide

[Back to the project overview](README.md)

This guide contains the source-file links, code-use instructions and rebuild
commands for the cooling tank. The main README covers the design, assembly
and printable downloads.

## Download and adapt with your AI

Download the whole project folder if you want to change the parametric design.
Give your AI the project files and describe the dimensions or behaviour you
want to change. Ask it to update the persistent source definitions, regenerate
the affected outputs and check the resulting geometry. The STL files are ready
for printing; source-level rebuilding also requires the local dependencies
listed below.

For example:

> Read README.md and BUILD_AND_MODIFY.md. Change the lifter height to 90 mm in
> the persistent parameter definitions, retain the two-identical-halves joint,
> regenerate the affected CAD, and verify the new geometry and documentation.

## Editable files

| Part | Size | SCAD |
| --- | --- | --- |
| Solid end cap | 15 mm total / 12 mm insertion | [SCAD](parts/three_d_print_filament_manufacture_cooling_tank_cap_end_solide_15_mm_depth/3dpr.scad) |
| Solid end cap | 6 mm total / 3 mm insertion | [SCAD](parts/three_d_print_filament_manufacture_cooling_tank_cap_end_solide_6_mm_depth/3dpr.scad) |
| Slotted end cap, inside seal groove | 15 mm total / 12 mm insertion | [SCAD](parts/three_d_print_filament_manufacture_cooling_tank_cap_end_open_15_mm_depth/3dpr.scad) |
| Slotted end cap, inside seal groove | 6 mm total / 3 mm insertion | [SCAD](parts/three_d_print_filament_manufacture_cooling_tank_cap_end_open_6_mm_depth/3dpr.scad) |
| Grooved 3 x 3 cover | 44 x 44 x 3 mm | [SCAD](parts/three_d_print_filament_manufacture_cooling_tank_cap_cover_3_by_3_oobb_3_mm_thickness/3dpr.scad) |
| Identical lifter half | 75 mm lift / 9 mm web / 30 mm shoes, assembled | [SCAD](parts/three_d_print_filament_manufacture_cooling_tank_lifter_75_mm_lift_height_9_mm_thickness_30_mm_support_thickness/3dpr.scad) |

- [Cap/cover assembly](preview/cap_seal_assembly.scad)
- [Pump inlet riser exploded assembly](preview/pump_lifter_assembly.scad) — set `gap=0` to close the halves; its adjacent assets folder is required.
- [Blender demonstration scene](demonstration/cooling_tank_demonstration.blend)
- [Scene dimensions and source meshes](demonstration/scene_data.json)
- [Demonstration geometry preparation](action_prepare_demonstration.py)
- [Blender scene and lighting script](action_render_demonstration.py)
- [Pump-holder import, placement and hose route](working_demonstration_pump.py)
- [Pump-top clamp geometry](working_pump_top_clamp.py)

## Persistent design and rebuild

Edit the verbose parameter dictionaries in
[working_oomp_populate.py](working_oomp_populate.py): `PROFILE`, `CAP_FIT`,
`CAP_OPENING`, `CAP_SEAL`, `CAP_COVER`, `LIFTER_VARIANTS`, `PUMP_LIFTER`, `PUMP_TOP_CLAMP` and `PUMP_CRADLE`. Geometry lives in
[working_scad.py](working_scad.py), with the pump variant in
[working_pump_lifter.py](working_pump_lifter.py). The populate → `parts_source` →
`working_oomp` → `parts` → `working_scad` pipeline regenerates CAD and taxonomy
navigation. Generated YAML files are outputs, not the sole source of changes.

```powershell
python action_make_scad.py
python -m unittest discover -s tests -q
python action_verify_cooling_tank.py
python action_preview_cooling_tank.py
python action_preview_cap_seal.py
python action_preview_lifter.py
python action_preview_pump_lifter.py
python action_preview_pump_top_clamp.py
python action_prepare_demonstration.py
python action_verify_pump_assembly.py
blender --background --factory-startup --python action_render_demonstration.py
```

The demonstration renderer needs Blender (tested with 5.2.2), and the
preparation script uses trimesh/Manifold to remove the solid parts from the
water volumes. Add `-- --draft` to the Blender command for a quick preview.
The full render also creates `demonstration/pump_hose_detail.png` and saves
both camera views in the editable scene.
The CAD pipeline uses the existing local OOMP/OOBB environment, OpenSCAD and
Shapely; verification uses trimesh and NumPy. The inherited exporter attempts
SVG/DXF on 3D objects and may report that the top-level object is not 2D;
SCAD, STL and PNG are the intended outputs.

Taxonomy starts with `three_d_print / filament_manufacture / cooling_tank`,
followed by the part type and dimensions. `cap_end_solide` retains the original
requested spelling. No version suffix is appended to any current part.

## Pump inlet parameters

The demonstration imports the base, top, retaining lid and nominal pump from the sibling
`oomlout_oobb_holder_motor_pump_submersible_jt_500` project. It reverses the
print-orientation transforms and positions the assembled holder at axial
X=285 mm, Y=-11 mm. Two cradle ribs support all four feet at Z=26 mm.
The pump and top retain the holder’s 15 mm local offset; the pump itself
uses its current 180-degree orientation, and the whole holder rotates 180
degrees in the tank. The base datum is 8.7 mm, the body 79 mm, the top 13 mm
and the lid 3 mm, placing the clamp mounting surface at Z=129.7 mm.
The original holder geometry is preserved.

[working_demonstration_pump.py](working_demonstration_pump.py) owns the verbose
`PUMP_PLACEMENT` dictionary, the imported assembly transforms and the hose sweep.
The rear support is centred at X=125 mm, with A spanning X=110–125 and B spanning
X=125–140. A smooth external hose route joins the riser's existing R40 channel.
The illustrated hose has approximately a 489 mm centreline, 12 mm open bore and 14 mm OD,
with 13.2 mm nominal overlap on the pump outlet. This is a routing illustration,
not a confirmed hose cut length or pump connection fit.

Preparation refreshes [cached source files](source_file/pump_holder) from that
sibling project when available, and otherwise uses the included copies.
[Provenance and SHA-256 hashes](source_file/pump_holder/provenance.json) retain
their source identities. The pump holder remains a separately maintained
project; its three meshes are extracted from the combined print set, with their
layout offsets removed. They are additional assembly components, outside the
cooling-tank catalogue of thirteen parts. The source pump project is not modified.

[Pump assembly verification](verification/pump_assembly.json) checks the real
meshes for gutter and cap collisions, tube bore continuity, holder placement and
source hashes. The nominal hose overlaps the two riser grips intentionally;
the check confines this overlap to the grip and taper. It also verifies the new
top clamp's M6 axes, cable clearance and filament clearance. Water volumes are cut
around the new holder, pump, hose and rear support before rendering.

`PUMP_LIFTER` declares the 75 mm lift, 30 mm assembled web/support thickness,
12 mm tube ID, 14 mm tube OD, 14.4 mm guide, 13.6 mm grip, 4 mm grip length, 2 mm transition,
40 mm centreline bend radius and 15 mm outlet height above the inside floor.
`tube_wall_mm` is derived as `(tube_od_mm - tube_id_mm) / 2`, currently 1 mm.
The preview shows the tube's outside envelope; its internal bore is not rendered.
The 18 mm outlet window opens through the foot. Flow-hole and joint positions
are explicit dictionaries in the same definition. Half B mirrors the channel
and joints across X; rotating it 180 degrees about Y and translating it 30 mm
along Z aligns both channel faces at Z=15. Each part prints flat at Z=0.

The side entry is midway between the lower rim and upper bottom, currently
Y=66.75. The outlet is Y=17.25, including the 2.25 mm gutter floor. The builder
rejects incompatible tube clearance, backing thickness, bend length, holes
and fastener placement. Equal web and support thickness keeps both halves
flat for printing. Changing the tube or lift may require moving the explicitly
declared holes and fasteners. Physical tube fit remains a trial.

Taxonomy includes `lifter_pump_inlet / 75_mm_lift_height / 30_mm_thickness /
30_mm_support_thickness / 14_mm_tube_od`. Each A/B assembly has one definition
and one folder, without a half suffix in its taxonomy. Exported SCAD
files inline their generated curved-channel module so each part's SCAD is
self-contained, including copies in taxonomy navigation.

[working_split_parts.py](working_split_parts.py) builds both halves from that
single definition. The exporter writes `half_a.scad`, `half_b.scad` and their
STLs beside the combined `3dpr.scad` / `3dpr.stl`. The combined layout places
the flat-print halves 10 mm apart. Assembly preparation reads the individual
files, never the translated print layout. The retired separate entries are
outside the active catalogue, under `verification/superseded_half_entries*`.

To rebuild just this variant through the persistent pipeline:

```powershell
python -c "import action_make_scad; action_make_scad.main(filter='lifter_pump_inlet')"
python action_preview_pump_lifter.py
python -m unittest discover -s tests -q
python action_verify_cooling_tank.py
python -c "import scad_help; scad_help.generate_navigation(sort=scad_help.get_navigation_sort())"
```

## Pump support cradle

`PUMP_CRADLE` in [working_oomp_populate.py](working_oomp_populate.py) declares
11 mm holder offset, 26 mm foot-seat height, 18 mm rib thickness, 60 mm foot
pitch, 12.6 mm pockets and four 10 mm flow holes per rib. The dimensions enter
the taxonomy. [working_pump_cradle.py](working_pump_cradle.py) builds a rib
from the gutter cavity profile with relieved sides and a contacting flat floor.
Its one catalogue entry has `print_quantity=2`; both installed ribs use the
same mesh. Preview and demonstration preparation read the exported STL.

```powershell
python -c "import action_make_scad; action_make_scad.main(filter='pump')"
python action_prepare_demonstration.py
python action_preview_pump_cradle.py
python action_preview_pump_top_clamp.py
python -m unittest discover -s tests -q
python action_verify_cooling_tank.py
python action_verify_pump_assembly.py
blender --background --factory-startup --python-exit-code 1 --python action_render_demonstration.py -- --gpu
```

`--gpu` selects OptiX on a supported NVIDIA GPU; omit it for CPU rendering.
The render keeps the requested half-full water level, below the raised pump
body. That is an illustration, not its operating fill level.

## Verification

The pump-top clamp is defined by `PUMP_TOP_CLAMP`, including R40, the 18.7 mm
bend-start height above its mounting surface, 4 mm feet, 22 mm half thickness,
16.4 mm straight inlet relief, a taper to the 14.4 mm guide, 13.6 mm grip and
M6 holes at ±15 mm along the gutter on `mount_row_offset_mm=-15`, the inboard row.
`outlet_offset_mm=-9` and `wire_offset_mm=9` match the current holder orientation. The straight relief extends 12.7 mm above
the flange; the R40 bend starts at 18.7 mm. The 16 mm driver bores open to the
outer face above the 4 mm flange, preserving material beneath each screw head. Its two
halves use OOBB M6 socket-head cuts, M3 countersinks and M3 nut pockets. Always use OOBB
primitives for screw and nut cuts, with `overhang=True`, named hardware sizes
and the appropriate mode-specific print allowances. Use `clearance='top'`
in each primitive's local coordinates when head or nut access must extend to
the outside; rotate the primitive to point that extension out of the part.
For nuts, anchor `zz='bottom'` at the bearing face so the overhang steps remain
at that face when the access pocket is extended.

`joint_screw_length_mm=25` and `joint_tip_protrusion_mm=1` derive equal recesses:
`(2 * half_thickness_mm - joint_screw_length_mm + joint_tip_protrusion_mm) / 2`.
With 22 mm halves this is 10 mm on each side. Countersunk length includes the
head; the 25 mm screw reaches through the nut pocket and protrudes 1 mm.
The mesh checks probe the recessed seats, nut bearing faces, access tunnels
and remaining boss walls. The two M6×12 mounting screws retain their existing
16 mm driver access. The exact toroidal
channel module is embedded in each exported SCAD. Changing the holder top/lid
thickness requires checking the bend start against the pump outlet tip;
preparation verifies at least 9 mm of straight hose beyond the rigid tip and
checks that the configured rigid-outlet allowance covers the actual pump.
Assembly placement uses the holder's base plate plus foot height as its rear
face datum. `PUMP_PLACEMENT['pump_rotation_in_holder_degrees']=180` matches
the sibling project’s current pump rotation. Port coordinates are converted from that default rotation before
placing the hose. The assembly verifier checks the actual pump against base,
top and lid as well as the hose and a 3 mm minimum filament surface clearance
across the whole pump assembly. It probes the foot bearing rings on both sides
of their M6 bores to confirm all four sit on real, equal-height pocket floors.

```powershell
python -c "import action_make_scad; action_make_scad.main(filter='pump_hose_clamp')"
python action_preview_pump_top_clamp.py
python action_prepare_demonstration.py
python action_verify_cooling_tank.py
python action_verify_pump_assembly.py
```

The automated suite checks cap fit, wall thickness, clearances, catalogue
identity, lifter joints, seal compression and groove alignment. The
[mesh report](verification/cooling_tank_meshes.json) checks all thirteen catalogue entries, their fifteen individual
STLs and both combined print layouts for dimensions, positive volume, closure, consistent winding and connected bodies,
and probes the real bores and mating grooves. It also checks that the inside
cover clears the insertion ledge. The original ten meshes also have independent
volume comparisons; pump halves have exported-mesh probes for the continuous
bend, backing, grip diameter, open outlet and complementary fastener pockets.
These digital checks do not establish
cooling performance, flow rate, structural load capacity or watertightness.

To check the saved demonstration scene without rendering it again:

```powershell
blender --background demonstration/cooling_tank_demonstration.blend --python-exit-code 1 --python action_verify_demonstration.py
```

[Scene verification report](verification/demonstration_scene.json) ·
[Catalogue consolidation report](verification/catalogue_cleanup.json)

## Additional backend documentation

[CAD_BUILDING.md](CAD_BUILDING.md) describes the inherited CAD backend and
output-selection infrastructure. The cooling-tank parts currently use the
OpenSCAD route above; SolidCraft is disabled in their part definitions.
