import bpy,json,os,hashlib
from mathutils import Vector
folder=os.path.dirname(__file__)
d=json.load(open(os.path.join(folder,'flange_screw_verification.json')))
def snapshot(o):
    r={'matrix':[list(row) for row in o.matrix_world],'hide_render':o.hide_render}
    if o.type=='MESH':r['vertices']=[list(v.co) for v in o.data.vertices]
    if o.type=='CAMERA':r['camera']=[o.data.lens,o.data.shift_x,o.data.shift_y,o.data.sensor_width]
    return hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()
assert all(snapshot(bpy.data.objects[n])==v for n,v in d['protected'].items())
ri=bpy.data.objects['LM_ROOT_Move_Complete_Machine'].matrix_world.inverted()
def bounds(name):
    o=bpy.data.objects[name];p=[ri@o.matrix_world@Vector(v) for v in o.bound_box]
    return Vector([min(v[k] for v in p) for k in range(3)]),Vector([max(v[k] for v in p) for k in range(3)])
for i in (1,2,3):
    fl,fh=bounds(f'S{i}_Head_Flange');sl,sh=bounds(f'S{i}_Head_Raised_Step');c=(fl+fh)/2
    assert abs((fl.z-sh.z)/(fh.z-fl.z)-.5)<.001
    for j in range(4):
        wl,wh=bounds(f'MD_S{i}_Flange_Bolt_{j}_Washer');wc=(wl+wh)/2
        r=Vector((wc.x-c.x,wc.y-c.y,0)).length
        assert abs(wl.z-sh.z)<1e-5
        assert r-(wh.x-wl.x)/2-(fh.x-fl.x)/2>.0009
    print('REOPEN_VERIFIED',i,'retained gap',fl.z-sh.z,'screw radius',r)
assert bpy.context.scene.get('REF_flange_screws_on_stage')
assert bpy.data.texts['LM_GENERATION_SCRIPT'].as_string()==open(os.path.join(folder,'generate_blockout.py'),encoding='utf-8-sig').read()
print('All non-screw geometry and cameras unchanged. Embedded script matches.')
