import bpy,json,os,runpy,math
from mathutils import Vector
folder=os.path.dirname(__file__)
helpers=runpy.run_path(os.path.join(folder,'correct_insert_pattern.py'),run_name='inspection')
d=json.load(open(os.path.join(folder,'insert_pattern_verification.json')))
assert all(helpers['protected_digest'](bpy.data.objects[n])==v for n,v in d['protected'].items())
o=bpy.data.objects['IF_S1_Perforated_Insert'];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
assert len([m for m in o.modifiers if m.type=='BOOLEAN' and m.object and m.object.name.startswith('IF_S1_Insert_Opening_')])==7
for c in [q for q in bpy.data.objects if q.name.startswith('IF_S1_Insert_Opening_')]:
 p=o.matrix_world.inverted()@c.matrix_world.translation;p.z=.05
 assert not ev.ray_cast(p,Vector((0,0,-1)))[0]
assert bpy.data.texts['LM_GENERATION_SCRIPT'].as_string()==open(os.path.join(folder,'generate_blockout.py'),encoding='utf-8-sig').read()
print('REOPEN VERIFIED: seven open holes, all unrelated objects and normal visibility preserved; generation script synchronized.')
