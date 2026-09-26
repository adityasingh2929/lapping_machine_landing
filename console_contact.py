"""Close the console/support gap without changing machine geometry."""
import bpy,os,json
from mathutils import Vector
F=os.path.dirname(os.path.abspath(__file__))
def apply():
 s=bpy.context.scene
 if s.get('CC_console_contact'):return
 if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
 root=bpy.data.objects['LM_ROOT_Move_Complete_Machine'];ri=root.matrix_world.inverted()
 def bounds(o):return [ri@o.matrix_world@Vector(v) for v in o.bound_box]
 housing=bpy.data.objects['Console_Projecting_Upper_Housing'];column=bpy.data.objects['Front_Centerline_Column']
 delta=min(p.y for p in bounds(column))-max(p.y for p in bounds(housing))
 assert 0<=delta<.05,delta
 tops=[o for o in bpy.data.objects if o.name.startswith('Console_') and o.type=='MESH']
 tops += [o for o in bpy.data.objects if o.name.startswith('PR_Console_Fascia_Badge')]
 topset=set(tops)
 def belongs(o):
  while o:
   if o in topset:return True
   o=o.parent
  return False
 affected=[o for o in bpy.data.objects if belongs(o)]
 before={o.name:o.matrix_world.copy() for o in bpy.data.objects}
 shift=root.matrix_world.to_3x3()@Vector((0,delta,0))
 for o in tops:
  if o.parent not in topset:
   m=o.matrix_world.copy();m.translation+=shift;o.matrix_world=m
 bpy.context.view_layer.update()
 for o in bpy.data.objects:
  expected=before[o.name].copy()
  if o in affected:expected.translation+=shift
  assert max(abs(o.matrix_world[r][c]-expected[r][c]) for r in range(4) for c in range(4))<1e-5,o.name
 gap=min(p.y for p in bounds(column))-max(p.y for p in bounds(housing))
 assert abs(gap)<1e-6
 s['CC_console_contact']=True;s['CC_console_contact_shift_y']=delta
 print('CONSOLE_CONTACT',json.dumps({'shift_m':delta,'gap_m':gap,'moved_objects':len(affected),'unrelated_transforms_unchanged':True}),flush=True)

if __name__=='__main__':
 apply()
 t=bpy.data.texts.get('LM_GENERATION_SCRIPT') or bpy.data.texts.new('LM_GENERATION_SCRIPT');t.clear();t.write(open(os.path.join(F,'generate_blockout.py'),encoding='utf8').read())
 bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=os.path.join(F,'lapping_machine_blockout.blend'),check_existing=False)
 # One temporary side preview; presentation settings in the saved file are preserved.
 s=bpy.context.scene;cam=s.camera;cam.location=(-3,-.13,1.1);cam.rotation_euler=(Vector((0,-.22,.72))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.95
 s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.device='CPU';s.render.resolution_x=720;s.render.resolution_y=600;s.render.resolution_percentage=100
 s.render.filepath=os.path.join(F,'console_contact_preview.png');bpy.ops.render.render(write_still=True)
