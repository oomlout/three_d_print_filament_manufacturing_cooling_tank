"""One catalogue entry per assembly; individual halves and a shared print plate."""
import copy
from pathlib import Path
import oobb


def module_for(p):
    if p['oobb_type'] == 'lifter_pump_inlet':
        import working_pump_lifter as module
    else:
        import working_pump_top_clamp as module
    return module


def halves(p):
    key = 'pump_half' if p['oobb_type'] == 'lifter_pump_inlet' else 'clamp_half'
    result = []
    for side in ('a', 'b'):
        half = copy.deepcopy(p)
        half.update({key: side, 'print_set': False, 'file_stem': f'half_{side}'})
        result.append(half)
    return result


def offsets(p):
    module = module_for(p)
    bounds = [module.get_layout(**h)['outline'].bounds for h in halves(p)]
    gap = p['print_gap_mm']
    return [-gap/2-bounds[0][2], gap/2-bounds[1][0]]


def consolidate(p):
    p = copy.deepcopy(p)
    for key in list(p):
        if key.startswith('taxonomy_') and str(p[key]).startswith('half_'):
            del p[key]
    p.pop('pump_half', None)
    p.pop('clamp_half', None)
    p.update({
        'print_set': True,
        'print_gap_mm': 10.0,
        'print_quantity': 1,
        'printed_pieces': ['half_a', 'half_b'],
        'part_role': 'printed_two_piece_assembly',
        'description': p['description'].replace('half A', 'complete A/B print set'),
    })
    p['width'] = p['width_mm'] = 2*p['width_mm'] + p['print_gap_mm']
    return p


def build(thing, **p):
    module = module_for(p)
    for half, shift in zip(halves(p), offsets(p)):
        component = {'components': [], 'components_objects': [], 'components_string': []}
        module.build(component, **half)
        thing['components'].append({
            'type': 'rotation',
            'typetype': 'positive',
            'pos': [shift, 0, 0],
            'rot': [0, 0, 0],
            'objects': component['components'],
        })


def export_halves(folder, p, mode, save_type):
    from working_pump_lifter import make_scad_portable
    for half in halves(p):
        thing = {'components': [], 'components_objects': [], 'components_string': []}
        module_for(p).build(thing, **half)
        suffix = '' if mode == '3dpr' else f'_{mode}'
        name = Path(folder) / (half['file_stem'] + suffix + '.scad')
        oobb.opsc_make_object(str(name), thing['components'], mode=mode, save_type=save_type, overwrite=True)
    make_scad_portable(folder)


def mesh_path(p):
    from working_oomp_populate import build_oomp_id
    return Path('parts') / build_oomp_id(p) / (p.get('file_stem', '3dpr') + '.stl')
