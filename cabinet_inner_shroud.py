"""Recessed opaque enclosure behind the tabletop gap; no exterior geometry changes."""
import bpy,os,json,hashlib
from mathutils import Vector
F=os.path.dirname(__file__)
NAME='CI_Recessed_Inner_Shroud'
def sig(o):
 d={'matrix':[list(r) for r in o.matrix_world],'hide':o.hide_render}
 if o.type=='MESH':d['vertices']=[list(v.co) for v in o.data.vertices]
 return hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
def apply():
 # Withdrawn at the user's request: do not recreate the physical shroud.
 return
 before={o.name:sig(o) for o in bpy.data.objects if o.name!=NAME}
 root=bpy.data.objects['LM_ROOT_Move_Complete_Machine'];ri=root.matrix_world.inverted()
 def bounds(name):
  o=bpy.data.objects[name];p=[ri@o.matrix_world@Vector(v) for v in o.bound_box]
  return Vector([min(q[k] for q in p) for k in range(3)]),Vector([max(q[k] for q in p) for k in range(3)])
 lo,hi=bounds('Tabletop_Clipped_Corners');dl,dh=bounds('Exposed_Under_Table_Drum')
 material=bpy.data.materials.get('CI_Matte_Charcoal') or bpy.data.materials.new('CI_Matte_Charcoal');material.use_nodes=True
 material.diffuse_color=(.008,.009,.010,1)
 p=material.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.008,.009,.010,1);p.inputs['Metallic'].default_value=0;p.inputs['Roughness'].default_value=1;p.inputs['Specular IOR Level'].default_value=.08;p.inputs['Alpha'].default_value=1
 o=bpy.data.objects.get(NAME)
 if not o:
  # 35 cm half-width: recessed 15 cm from cabinet faces and behind all four spacers.
  # Closed corners and caps prevent oblique sightlines into the empty enclosure.
  a=.350;bottom=.610;top=lo.z+.0003;t=.002
  verts=[];faces=[]
  def panel(x0,x1,y0,y1,z0,z1):
   n=len(verts);verts.extend([(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)])
   faces.extend([tuple(n+k for k in f) for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]])
  panel(-a,-a+t,-a,a,bottom,top);panel(a-t,a,-a,a,bottom,top)
  panel(-a+t,a-t,-a,-a+t,bottom,top);panel(-a+t,a-t,a-t,a,bottom,top)
  panel(-a+t,a-t,-a+t,a-t,bottom,bottom+t);panel(-a+t,a-t,-a+t,a-t,top-t,top)
  mesh=bpy.data.meshes.new(NAME);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(NAME,mesh);bpy.context.scene.collection.objects.link(o);o.parent=root
  o.data.materials.append(material)
 o['purpose']='Opaque recessed background behind tabletop gap; preserves external spacers and drum projection.'
 bpy.context.view_layer.update();assert all(sig(bpy.data.objects[n])==v for n,v in before.items())
 bpy.context.scene['CI_inner_shroud']=True
 json.dump({'protected':before,'half_width':.35,'material':'opaque matte charcoal'},open(os.path.join(F,'inner_shroud_verification.json'),'w'),indent=2)
def run():
 apply()
 for f,label in [('generate_blockout.py','LM_GENERATION_SCRIPT'),('cabinet_inner_shroud.py','LM_INNER_SHROUD_SCRIPT')]:
  t=bpy.data.texts.get(label) or bpy.data.texts.new(label);t.clear();t.write(open(os.path.join(F,f),encoding='utf-8-sig').read())
 old=bpy.context.preferences.filepaths.save_version;bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=os.path.join(F,'lapping_machine_blockout.blend'));bpy.context.preferences.filepaths.save_version=old
 s=bpy.context.scene;cam=bpy.data.objects.new('TEMP_Shroud_Preview',bpy.data.cameras.new('TEMP_Shroud_Preview'));s.collection.objects.link(cam);s.camera=cam
 root=bpy.data.objects['LM_ROOT_Move_Complete_Machine'];cam.location=root.matrix_world@Vector((-2.6,-.07,.98));target=root.matrix_world@Vector((0,0,.695));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.17
 s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True;s.render.resolution_x=720;s.render.resolution_y=270;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=os.path.join(F,'inner_shroud_preview.png');bpy.ops.render.render(write_still=True)
 print('INNER_SHROUD_SAVED; protected geometry unchanged.',flush=True)
if __name__=='__main__':run()
