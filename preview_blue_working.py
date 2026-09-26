import bpy,os,runpy,json,math
from mathutils import Vector
F=os.path.dirname(__file__);helper=runpy.run_path(os.path.join(F,'match_blue_working_parts.py'));d=json.load(open(os.path.join(F,'blue_working_verification.json')))
assert all(helper['signature'](bpy.data.objects[n])==v for n,v in d['protected'].items())
assert not bpy.data.objects.get('IF_S1_Perforated_Insert')
assert not any('_Ring_Groove_' in o.name for o in bpy.data.objects)
root=bpy.data.objects['LM_ROOT_Move_Complete_Machine'];ri=root.matrix_world.inverted();dep=bpy.context.evaluated_depsgraph_get();hits=[]
for i in (1,2,3):
 o=bpy.data.objects[f'S{i}_Hollow_Ring'];p=[ri@o.matrix_world@Vector(v) for v in o.bound_box];c=(Vector([min(q[k] for q in p) for k in range(3)])+Vector([max(q[k] for q in p) for k in range(3)]))/2
 for radius in (0,.055,.10):
  for j in range(12):
   start=root.matrix_world@Vector((c.x+radius*math.cos(j*math.tau/12),c.y+radius*math.sin(j*math.tau/12),.825))
   # Ignore hidden boolean cutters by testing only render-visible evaluated meshes.
   nearest=(100,None)
   for q in bpy.data.objects:
    if q.type!='MESH' or q.hide_render:continue
    e=q.evaluated_get(dep);inv=e.matrix_world.inverted();ok,loc,n,idx=e.ray_cast(inv@start,inv.to_3x3()@Vector((0,0,-1)),distance=.1)
    if ok:
     dist=(e.matrix_world@loc-start).length
     if dist<nearest[0]:nearest=(dist,q.name)
   if nearest[1]!='Circular_Working_Plate':hits.append((i,radius,j,nearest))
assert not hits,str(hits)
print('VERIFIED: all 108 ring-interior samples expose the continuous working plate; unrelated objects preserved',flush=True)
s=bpy.context.scene;s.cycles.samples=16;s.cycles.use_denoising=True
try:
 cp=bpy.context.preferences.addons['cycles'].preferences;cp.compute_device_type='CUDA';cp.get_devices()
 for dev in cp.devices:dev.use=dev.type=='CUDA'
 s.cycles.device='GPU' if any(dev.type=='CUDA' for dev in cp.devices) else 'CPU'
except Exception:s.cycles.device='CPU'
cam=bpy.data.objects.new('TEMP_Working_Review',bpy.data.cameras.new('TEMP_Working_Review'));s.collection.objects.link(cam);s.camera=cam
cam.location=root.matrix_world@Vector((.90,-1.20,1.58));target=root.matrix_world@Vector((0,-.02,.87));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=62
s.render.resolution_x=900;s.render.resolution_y=700;s.render.resolution_percentage=100;s.render.filepath=os.path.join(F,'blue_working_updated.png');bpy.ops.render.render(write_still=True)
