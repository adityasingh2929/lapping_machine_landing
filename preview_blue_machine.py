import bpy,os,json,runpy
folder=os.path.dirname(bpy.data.filepath)
# Reopen validation: all original objects and geometry remain, and blue material is saved.
source=open(os.path.join(folder,'apply_blue_machine.py')).read().split('before=geometry_digest()')[0]
ns={};exec(source,ns)
expected=json.load(open(os.path.join(folder,'blue_machine_verification.json')))
assert ns['geometry_digest']()==expected['geometry_sha256']
assert len(bpy.data.objects)==expected['objects']
assert bpy.data.objects['Panel_Front'].data.materials[0].name=='BM_RAL_5002_Ultramarine_Gloss'
assert bpy.data.objects['Front_Centerline_Column'].data.materials[0].name=='LM_Grey_Paint'
print('REOPEN_VERIFIED_GEOMETRY_AND_PALETTE',flush=True)
s=bpy.context.scene;s.cycles.samples=16;s.cycles.use_denoising=True
try:
    cp=bpy.context.preferences.addons['cycles'].preferences;cp.compute_device_type='CUDA';cp.get_devices()
    for d in cp.devices:d.use=d.type=='CUDA'
    s.cycles.device='GPU' if any(d.type=='CUDA' for d in cp.devices) else 'CPU'
except Exception:s.cycles.device='CPU'
s.render.resolution_x=1100;s.render.resolution_y=1100;s.render.resolution_percentage=100
for cam,file in [('MD_Preview_Complete','blue_machine_overview.png'),('IF_Preview_Frame','blue_machine_frame.png')]:
    s.camera=bpy.data.objects[cam];s.render.filepath=os.path.join(folder,file)
    bpy.ops.render.render(write_still=True)
