"""Non-saving validation of the saved v02 file and its regeneration."""
import bpy
import os
import json
from mathutils import Vector

folder=os.path.dirname(__file__)
path=os.path.join(folder,'generate_blockout_v02.py')
report=[]
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active
            assert space.shading.type=='MATERIAL'
            assert not space.overlay.show_extras
            assert not space.overlay.show_relationship_lines
            assert space.region_3d.view_perspective=='PERSP'
            report.append('Saved viewport: material preview, perspective, extras/relationships hidden')
presentation=bpy.data.collections['08_PRESENTATION']
assert all(o.hide_get() and not o.hide_render for o in presentation.objects)
report.append('Presentation objects hidden only in viewport; enabled for rendering')
assert bpy.data.objects['S1_Head_Lower_Disk'].visible_get()
assert bpy.data.objects['Panel_Front'].visible_get()
report.append('Machine geometry remains visible with root marker hidden')

sentinel=bpy.data.objects.new('UNRELATED_PRESERVATION_TEST',None)
bpy.context.scene.collection.objects.link(sentinel)
sentinel.location=(7,8,9)
before=len(bpy.data.collections['LM_BLOCKOUT'].all_objects)
source=open(path,encoding='utf-8').read().replace('RENDER = True','RENDER = False').replace('SAVE = True','SAVE = False')
exec(compile(source,path,'exec'),{'__file__':path,'__name__':'__main__'})
assert bpy.data.objects.get(sentinel.name) is sentinel
assert tuple(sentinel.location)==(7.0,8.0,9.0)
after=len(bpy.data.collections['LM_BLOCKOUT'].all_objects)
assert before==after,(before,after)
report.append(f'Rebuild: {before} generated objects before/after; unrelated sentinel unchanged')

config=json.loads(bpy.data.objects['LM_ROOT_Move_Complete_Machine']['configuration'])
for i,xy in enumerate(config['stations'],1):
    ring=bpy.data.objects[f'S{i}_Hollow_Ring']
    points=[ring.matrix_world @ v.co for v in ring.data.vertices]
    center=((min(v.x for v in points)+max(v.x for v in points))/2,
            (min(v.y for v in points)+max(v.y for v in points))/2)
    assert max(abs(center[k]-xy[k]) for k in [0,1])<1e-6
    min_radius=min(((v.x-xy[0])**2+(v.y-xy[1])**2)**.5 for v in points)
    assert abs(min_radius-(config['ring_diameter']/2-config['ring_wall']))<1e-6
    counts={}
    for face in ring.data.polygons:
        for edge in face.edge_keys:
            counts[edge]=counts.get(edge,0)+1
    assert all(v==2 for v in counts.values()),'Non-manifold ring'
    report.append(f'S{i}: centered hollow manifold ring; inner radius {min_radius:.3f}')
report.append('All generation assertions (separation, fit, alignment, clearances, framing) rerun successfully')
with open(os.path.join(folder,'verification_v02.txt'),'w') as f:f.write('\n'.join(report))
print('V02_VERIFICATION_OK\n'+'\n'.join(report))
if hasattr(bpy.context.scene,'eevee'):
    print('EEVEE_PROPERTIES',list(bpy.context.scene.eevee.bl_rna.properties.keys()))
