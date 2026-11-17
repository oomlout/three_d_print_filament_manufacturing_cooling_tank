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
- [Blender demonstration scene](demonstration/cooling_tank_demonstration.blend)
- [Scene dimensions and source meshes](demonstration/scene_data.json)
- [Demonstration geometry preparation](action_prepare_demonstration.py)
- [Blender scene and lighting script](action_render_demonstration.py)

## Persistent design and rebuild

Edit the verbose parameter dictionaries in
[working_oomp_populate.py](working_oomp_populate.py): `PROFILE`, `CAP_FIT`,
`CAP_OPENING`, `CAP_SEAL`, `CAP_COVER` and `LIFTER_VARIANTS`. Geometry lives in
[working_scad.py](working_scad.py). The populate → `parts_source` →
`working_oomp` → `parts` → `working_scad` pipeline regenerates CAD and taxonomy
navigation. Generated YAML files are outputs, not the sole source of changes.

```powershell
python action_make_scad.py
python -m unittest discover -s tests -q
python action_verify_cooling_tank.py
python action_preview_cooling_tank.py
python action_preview_cap_seal.py
python action_preview_lifter.py
python action_prepare_demonstration.py
blender --background --factory-startup --python action_render_demonstration.py
```

The demonstration renderer needs Blender (tested with 5.2.2), and the
preparation script uses trimesh/Manifold to remove the solid parts from the
water volumes. Add `-- --draft` to the Blender command for a quick preview.
The CAD pipeline uses the existing local OOMP/OOBB environment, OpenSCAD and
Shapely; verification uses trimesh and NumPy. The inherited exporter attempts
SVG/DXF on 3D objects and may report that the top-level object is not 2D;
SCAD, STL and PNG are the intended outputs.

Taxonomy starts with `three_d_print / filament_manufacture / cooling_tank`,
followed by the part type and dimensions. `cap_end_solide` retains the original
requested spelling. No version suffix is appended to any current part.

## Verification

The automated suite checks cap fit, wall thickness, clearances, catalogue
identity, lifter joints, seal compression and groove alignment. The
[mesh report](verification/cooling_tank_meshes.json) checks all ten current
STLs for dimensions, volume, closure, consistent winding and connected bodies,
and probes the real bores and mating grooves. It also checks that the inside
cover clears the insertion ledge. These digital checks do not establish
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
