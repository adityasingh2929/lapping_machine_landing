import bpy,os,sys
from mathutils import Vector
F=os.path.dirname(os.path.dirname(__file__));s=bpy.context.scene
cam=bpy.data.objects.new('Temporary_Web_Poster',bpy.data.cameras.new('Temporary_Web_Poster'));s.collection.objects.link(cam);s.camera=cam
root=bpy.data.objects['LM_ROOT_Move_Complete_Machine'];cam.location=root.matrix_world@Vector((.36,-3.5,1.95));target=root.matrix_world@Vector((0,-.35,.75));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=55
s.cycles.samples=16;s.cycles.use_denoising=True
try:
 cp=bpy.context.preferences.addons['cycles'].preferences;cp.compute_device_type='CUDA';cp.get_devices()
 for d in cp.devices:d.use=d.type=='CUDA'
 s.cycles.device='GPU' if any(d.type=='CUDA' for d in cp.devices) else 'CPU'
except Exception:s.cycles.device='CPU'
s.render.resolution_x=640;s.render.resolution_y=800;s.render.resolution_percentage=100
s.render.filepath=os.path.join(F,'docs','assets','blue-poster.png' if '--blue' in sys.argv else 'machine-poster.png');bpy.ops.render.render(write_still=True)
