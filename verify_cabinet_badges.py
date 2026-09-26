import bpy,runpy,json,os
from mathutils import Vector
F=os.path.dirname(__file__);m=runpy.run_path(os.path.join(F,'cabinet_nameplates.py'),run_name='verification')
d=json.load(open(os.path.join(F,'cabinet_nameplates_verification.json')))
assert all(m['signature'](bpy.data.objects[n])==v for n,v in d['protected'].items())
src=bpy.data.objects[d['source']]
for n in m['NAMES']:
 o=bpy.data.objects[n];assert o.data.materials[0]==src.data.materials[0]
 assert abs(o.dimensions.x-.2)<1e-5 or abs(o.dimensions.y-.2)<1e-5
 assert o.data.materials[1]==src.data.materials[1]
 assert abs((max(v.co.x for v in o.data.vertices)-min(v.co.x for v in o.data.vertices))/(max(v.co.y for v in o.data.vertices)-min(v.co.y for v in o.data.vertices))-src['aspect_ratio'])<1e-5
 assert (o.matrix_world.to_3x3()@Vector((0,1,0))).normalized().dot(Vector((0,0,1)))>.9999
 assert o.data.uv_layers.active is not None
 assert len(o.modifiers)==len(src.modifiers)
for n,normal in zip(m['NAMES'],[(-1,0,0),(0,1,0),(1,0,0)]):
 assert (bpy.data.objects[n].matrix_world.to_3x3()@Vector((0,0,1))).normalized().dot(Vector(normal))>.9999
assert len([o for o in bpy.data.objects if o.name.startswith(m['NAMES'])])==3
assert not any(o.name.startswith('PR_Cabinet_Left_Badge') for o in bpy.data.objects)
assert bpy.data.images['plate_2.jpeg'].packed_file
assert bpy.data.texts['LM_GENERATION_SCRIPT'].as_string()==open(os.path.join(F,'generate_blockout.py'),encoding='utf-8-sig').read()
print('REOPEN_VERIFIED: three distinct exact-artwork badges; packed artwork; placeholder removed; all protected objects unchanged.')
