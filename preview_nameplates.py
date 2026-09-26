import bpy,os,json,hashlib,math
from mathutils import Vector
folder=os.path.dirname(os.path.abspath(__file__))
s=bpy.context.scene
d=json.load(open(os.path.join(folder,'nameplates_verification.json')))
for n,digest in d['protected_objects'].items():
    o=bpy.data.objects[n]
    x={'matrix':[list(r) for r in o.matrix_world],'materials':[m.name for m in o.data.materials] if hasattr(o.data,'materials') else [],'hide':o.hide_render}
    if o.type=='MESH':x['vertices']=[list(v.co) for v in o.data.vertices]
    assert hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()==digest,n
assert bpy.data.texts['LM_GENERATION_SCRIPT'].as_string()==open(os.path.join(folder,'generate_blockout.py'),encoding='utf-8-sig').read()
assert all(bpy.data.images[f'plate_{i}.jpeg'].packed_file for i in (1,2))
for p in d['plates']:
    o=bpy.data.objects[p['name']]
    if 'Panel' not in o.name:assert (o.matrix_world.to_3x3()@Vector((0,0,1))).y<-.999
    assert len(o.modifiers)==1
print('REOPEN_VERIFIED: protected geometry/material assignments/transforms unchanged; artwork packed; orientations correct',flush=True)
s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.use_denoising=True
try:
    cp=bpy.context.preferences.addons['cycles'].preferences;cp.compute_device_type='CUDA';cp.get_devices()
    for d in cp.devices:d.use=d.type=='CUDA'
    s.cycles.device='GPU' if any(d.type=='CUDA' for d in cp.devices) else 'CPU'
except Exception:s.cycles.device='CPU'
s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
camdata=bpy.data.cameras.new('NP_Temporary_Preview');cam=bpy.data.objects.new('NP_Temporary_Preview',camdata);s.collection.objects.link(cam);s.camera=cam
def render(loc,target,lens,w,h,file):
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();camdata.lens=lens
    camdata.clip_start=.005;s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=os.path.join(folder,file)
    bpy.ops.render.render(write_still=True)
render((.36,-3.5,1.95),(0,-.35,.75),55,640,800,'nameplates_overview.png')
render((.10,-1.65,1.08),(.075,-.96,.572),65,1400,963,'nameplates_closeup.png')
