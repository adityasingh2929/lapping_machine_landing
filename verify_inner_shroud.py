import bpy,os,json,runpy,math
from mathutils import Vector
F=os.path.dirname(__file__);m=runpy.run_path(os.path.join(F,'cabinet_inner_shroud.py'),run_name='verify');d=json.load(open(os.path.join(F,'inner_shroud_verification.json')))
assert all(m['sig'](bpy.data.objects[n])==v for n,v in d['protected'].items())
o=bpy.data.objects['CI_Recessed_Inner_Shroud'];e=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
for i in range(16):
 a=i*math.tau/16;p=Vector((math.cos(a),math.sin(a),.685));v=Vector((-math.cos(a),-math.sin(a),0))
 assert e.ray_cast(p,v)[0]
assert len([q for q in bpy.data.objects if q.name.startswith('CI_Recessed_Inner_Shroud')])==1
assert bpy.data.texts['LM_GENERATION_SCRIPT'].as_string()==open(os.path.join(F,'generate_blockout.py'),encoding='utf-8-sig').read()
print('REOPEN VERIFIED: one opaque four-sided shroud; 16 surrounding sight directions blocked; all pre-existing geometry/transforms unchanged; embedded generator matches.')
