import bpy,json,os,hashlib
from mathutils import Vector
folder=os.path.dirname(__file__)
d=json.load(open(os.path.join(folder,'flange_gap_verification.json')))
def snapshot(o):
    r={'matrix':[list(row) for row in o.matrix_world],'hide_render':o.hide_render}
    if o.type=='MESH':r['vertices']=[list(v.co) for v in o.data.vertices]
    if o.type=='CAMERA':r['camera']=[o.data.lens,o.data.shift_x,o.data.shift_y,o.data.sensor_width]
    return hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()
assert all(snapshot(bpy.data.objects[n])==v for n,v in d['protected'].items())
root=bpy.data.objects['LM_ROOT_Move_Complete_Machine'];ri=root.matrix_world.inverted()
for i in (1,2,3):
    def z(name):
        o=bpy.data.objects[name];p=[(ri@o.matrix_world@Vector(v)).z for v in o.bound_box];return min(p),max(p)
    fl,fh=z(f'S{i}_Head_Flange');sl,sh=z(f'S{i}_Head_Raised_Step');nl,nh=z(f'MD_S{i}_Flange_Central_Neck')
    assert abs((fl-sh)/(fh-fl)-.5)<.001
    assert nl<sh and nh>fl
    print('REOPEN_VERIFIED',i,'gap',fl-sh,'thickness',fh-fl)
assert bpy.context.scene.get('REF_small_flange_clearance')
assert bpy.data.texts['LM_GENERATION_SCRIPT'].as_string()==open(os.path.join(folder,'generate_blockout.py'),encoding='utf-8-sig').read()
print('All protected objects/cameras unchanged; all three central necks bridge the gap; embedded script matches.')
