import bpy,os,json,hashlib
from mathutils import Vector
folder=os.path.dirname(os.path.abspath(__file__))
data=json.load(open(os.path.join(folder,'valve_verification.json')))
import runpy
helper=runpy.run_path(os.path.join(folder,'valve_correction.py'))
assert all(helper['digest'](bpy.data.objects[n])==v for n,v in data['protected'].items())
assert all(bpy.data.objects.get(f'VP_S{i}_Valve_Body') and bpy.data.objects.get(f'VP_S{i}_Lever_Grip') for i in (1,2,3))
assert all(bpy.data.objects.get(f'PR_{p}_Badge_Exact') for p in ['Console_Panel','Console_Fascia','Front_Beam'])
print('REOPEN_VERIFIED three valves and levers; unrelated geometry and all nameplates preserved',flush=True)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.use_denoising=True
try:
    cp=bpy.context.preferences.addons['cycles'].preferences;cp.compute_device_type='CUDA';cp.get_devices()
    for d in cp.devices:d.use=d.type=='CUDA'
    s.cycles.device='GPU' if any(d.type=='CUDA' for d in cp.devices) else 'CPU'
except Exception:s.cycles.device='CPU'
c=bpy.data.objects.new('VP_Temp_Camera',bpy.data.cameras.new('VP_Temp_Camera'));s.collection.objects.link(c);s.camera=c;c.data.clip_start=.005
s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
for pos,target,lens,w,h,file in [((-1.0,-.65,1.48),(-.06,-.04,1.22),65,1000,760,'valves_overview.png'),((.65,.30,1.22),(.237,.09,1.09),75,850,700,'valve_closeup.png')]:
    c.location=pos;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=lens
    s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=os.path.join(folder,file);bpy.ops.render.render(write_still=True)
