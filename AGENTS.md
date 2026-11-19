# CAD project conventions

- Use OOBB primitives for screw, nut and named fastener-hole geometry. Enable
  `overhang=True` on screw and nut primitives. Use the appropriate mode-specific
  hardware dimensions and clearance extensions wherever assembly access needs
  them; orient extensions toward the accessible face.
- Keep dimensional declarations in `working_oomp_populate.py` and regenerate
  through the populate / working_oomp / working_scad pipeline. Use verbose
  multiline parameter dictionaries.
- Keep paired A/B pieces in one catalogue entry, with individual half files and
  both pieces in `3dpr.stl`. Keep current unversioned part names.
- Put code and rebuild instructions in `BUILD_AND_MODIFY.md`, linked from the
  main project README.
