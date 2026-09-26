import bpy,json,os
from mathutils import Vector
folder=os.path.dirname(__file__);s=bpy.context.scene
o=bpy.data.objects['IF_S1_Perforated_Insert']
items=[]
for p in bpy.data.objects:
 if 'Insert' in p.name or 'insert' in p.name:
  items.append({'name':p.name,'position':list(p.matrix_world.translation),'dimensions':list(p.dimensions),'hidden':p.hide_render,'modifiers':[(m.name,m.type,m.object.name if m.type=='BOOLEAN' and m.object else None) for m in p.modifiers]})
json.dump(items,open(os.path.join(folder,'insert_top_initial_audit.json'),'w'),indent=2)
print(items,flush=True)
for p in bpy.data.objects:
 if p.type in {'MESH','CURVE','FONT','VOLUME'}:p.hide_render=p!=o
cam=bpy.data.objects.new('TEMP_Insert_Top',bpy.data.cameras.new('TEMP_Insert_Top'));s.collection.objects.link(cam)
cam.location=o.matrix_world.translation+Vector((0,0,.6));cam.rotation_euler=(0,0,0);cam.data.type='ORTHO';cam.data.ortho_scale=.29;s.camera=cam
s.render.engine='CYCLES';s.cycles.samples=8;s.cycles.use_denoising=True
s.render.resolution_x=400;s.render.resolution_y=400;s.render.resolution_percentage=100
s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
s.render.filepath=os.path.join(folder,'insert_top_before.png');bpy.ops.render.render(write_still=True)
