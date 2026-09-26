import bpy,json,os,hashlib
from mathutils import Vector
folder=os.path.dirname(__file__)
d=json.load(open(os.path.join(folder,'insert_frame_verification.json')))
def digest(o):
    r={'matrix':[list(row) for row in o.matrix_world],'hide':o.hide_render}
    if o.type=='MESH':r.update(vertices=[list(v.co) for v in o.data.vertices],materials=[m.name if m else None for m in o.data.materials])
    if o.type=='CURVE':r['points']=[[list(p.co) for p in s.bezier_points] for s in o.data.splines]
    if o.type=='CAMERA':r['lens']=[o.data.lens,o.data.shift_x,o.data.shift_y]
    return hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()
assert all(digest(bpy.data.objects[n])==h for n,h in d['protected'].items())
deps=bpy.context.evaluated_depsgraph_get()
insert=bpy.data.objects['IF_S1_Perforated_Insert'].evaluated_get(deps)
for j in range(5):
    c=bpy.data.objects[f'IF_S1_Insert_Opening_{j}']
    p=insert.matrix_world.inverted()@c.matrix_world.translation;p.z+=.1
    assert not insert.ray_cast(p,Vector((0,0,-1)),distance=.2)[0],f'Insert hole {j} blocked'
spine=bpy.data.objects['PROVISIONAL_Longitudinal_Spine'].evaluated_get(deps)
root=bpy.data.objects['LM_ROOT_Move_Complete_Machine']
for y in (-.45,.46):
    p=spine.matrix_world.inverted()@root.matrix_world@Vector((0,y,1.3))
    assert not spine.ray_cast(p,Vector((0,0,-1)),distance=.4)[0]
assert bpy.data.texts['LM_GENERATION_SCRIPT'].as_string()==open(os.path.join(folder,'generate_blockout.py'),encoding='utf-8-sig').read()
assert len([o for o in bpy.data.objects if o.name=='IF_S1_Perforated_Insert'])==1
print('REOPEN VERIFIED: protected geometry/cameras unchanged; five through-openings in separate S1 insert; main frame bays open; embedded script matches.')
