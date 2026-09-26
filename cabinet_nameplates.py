"""Duplicate the installed finished console artwork onto three identified cabinet faces."""
import bpy,os,json,hashlib
from mathutils import Vector,Matrix
F=os.path.dirname(os.path.abspath(__file__))
NAMES=('NP_Cabinet_Left_Exact','NP_Cabinet_Rear_Right_Area_Exact','NP_Cabinet_Right_Exact')
def signature(o):
 d={'matrix':[list(r) for r in o.matrix_world],'hide':o.hide_render,'materials':[m.name if m else None for m in o.data.materials] if hasattr(o.data,'materials') else []}
 if o.type=='MESH':d['verts']=[list(v.co) for v in o.data.vertices]
 return hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
def apply():
 root=bpy.data.objects['LM_ROOT_Move_Complete_Machine'];ri=root.matrix_world.inverted()
 source=bpy.data.objects['PR_Console_Fascia_Badge_Exact']
 def bounds(name):
  o=bpy.data.objects[name];p=[ri@o.matrix_world@Vector(v) for v in o.bound_box]
  return Vector([min(q[k] for q in p) for k in range(3)]),Vector([max(q[k] for q in p) for k in range(3)])
 old=bpy.data.objects.get('PR_Cabinet_Left_Badge_Backing')
 center=ri@old.matrix_world.translation if old else Vector((0,0,.493))
 if bpy.data.objects.get(NAMES[0]):center=ri@bpy.data.objects[NAMES[0]].matrix_world.translation
 before={o.name:signature(o) for o in bpy.data.objects if o.name not in NAMES and not o.name.startswith('PR_Cabinet_Left_Badge')}
 # Remove the entire obsolete backing/text group, never the console or upper-frame artwork.
 for o in list(bpy.data.objects):
  if o.name.startswith('PR_Cabinet_Left_Badge'):bpy.data.objects.remove(o,do_unlink=True)
 lo,hi=bounds('Panel_Left');rl,rh=bounds('Panel_Rear');al,ah=bounds('Panel_Right')
 cl,ch=bounds('Rear_Centerline_Column')
 # Looking from +Y, screen-right corresponds to negative X.
 rear_x=(rl.x+cl.x)/2
 t=float(source.get('thickness',.00065));offset=t/2+.0002
 placements=[((lo.x-offset,center.y,center.z),(0,-1,0),(-1,0,0)),
             ((rear_x,rh.y+offset,(rl.z+rh.z)/2),(-1,0,0),(0,1,0)),
             ((ah.x+offset,(al.y+ah.y)/2,(al.z+ah.z)/2),(0,1,0),(1,0,0))]
 mesh=bpy.data.meshes.get('NP_Cabinet_Shared_Artwork')
 if mesh is None:
  mesh=source.data.copy();mesh.name='NP_Cabinet_Shared_Artwork'
  width=max(v.co.x for v in mesh.vertices)-min(v.co.x for v in mesh.vertices);scale=.200/width
  for v in mesh.vertices:v.co.x*=scale;v.co.y*=scale
 for name,(pos,right,normal) in zip(NAMES,placements):
  o=bpy.data.objects.get(name)
  if o is None:
   o=source.copy();o.name=name;bpy.data.collections['Labels_and_Badges'].objects.link(o)
  o.data=mesh;o.parent=root
  basis=Matrix((Vector(right),Vector((0,0,1)),Vector(normal))).transposed().to_4x4();basis.translation=Vector(pos)
  o.matrix_world=root.matrix_world@basis;o['cabinet_reference']={'NP_Cabinet_Left_Exact':'name_plate_1.jpeg: existing placeholder position','NP_Cabinet_Rear_Right_Area_Exact':'name_plate_3.jpeg: screen-right of rear column','NP_Cabinet_Right_Exact':'name_plate_4.jpeg: centered between louver banks'}[name]
 bpy.context.view_layer.update()
 assert all(signature(bpy.data.objects[n])==v for n,v in before.items())
 assert all(bpy.data.objects[n].data.materials[0]==source.data.materials[0] for n in NAMES)
 for image in bpy.data.images:
  if image.source=='FILE' and image.has_data and not image.packed_file:image.pack()
 bpy.context.scene['NP_three_cabinet_badges']=True
 json.dump({'protected':before,'placements':{n:[list(r) for r in bpy.data.objects[n].matrix_world] for n in NAMES},'width':.2,'source':source.name},open(os.path.join(F,'cabinet_nameplates_verification.json'),'w'),indent=2)
 return placements
def run():
 assert os.path.normcase(bpy.data.filepath)==os.path.normcase(os.path.join(F,'lapping_machine_blockout.blend'))
 apply()
 # Prove reruns reuse the same three objects and leave their placement unchanged.
 first={n:signature(bpy.data.objects[n]) for n in NAMES};count=len(bpy.data.objects)
 apply()
 assert len(bpy.data.objects)==count
 assert first=={n:signature(bpy.data.objects[n]) for n in NAMES}
 assert len([o for o in bpy.data.objects if o.name.startswith(NAMES)])==3
 for name,label in [('generate_blockout.py','LM_GENERATION_SCRIPT'),('cabinet_nameplates.py','LM_CABINET_NAMEPLATES_SCRIPT')]:
  t=bpy.data.texts.get(label) or bpy.data.texts.new(label);t.clear();t.write(open(os.path.join(F,name),encoding='utf-8-sig').read())
 old=bpy.context.preferences.filepaths.save_version;bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=os.path.join(F,'lapping_machine_blockout.blend'));bpy.context.preferences.filepaths.save_version=old
 s=bpy.context.scene;root=bpy.data.objects['LM_ROOT_Move_Complete_Machine']
 cam=bpy.data.objects.new('TEMP_Cabinet_Preview',bpy.data.cameras.new('TEMP_Cabinet_Preview'));s.collection.objects.link(cam);s.camera=cam
 cam.data.type='ORTHO';cam.data.ortho_scale=1.13
 s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True
 try:
  cp=bpy.context.preferences.addons['cycles'].preferences;cp.compute_device_type='CUDA';cp.get_devices()
  for d in cp.devices:d.use=d.type=='CUDA'
  s.cycles.device='GPU' if any(d.type=='CUDA' for d in cp.devices) else 'CPU'
 except Exception:s.cycles.device='CPU'
 s.render.resolution_x=480;s.render.resolution_y=350;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
 for side,eye,target in [('uno',(-2.5,0,.42),(0,0,.37)),('tres',(0,2.5,.42),(0,0,.37)),('quatro',(2.5,0,.42),(0,0,.37))]:
  cam.location=root.matrix_world@Vector(eye);cam.rotation_euler=(root.matrix_world@Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
  s.render.filepath=os.path.join(F,'cabinet_badge_'+side+'.png');bpy.ops.render.render(write_still=True)
 print('CABINET_NAMEPLATES_SAVED',flush=True)
if __name__=='__main__':run()
