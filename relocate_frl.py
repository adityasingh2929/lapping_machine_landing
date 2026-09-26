"""User-directed front-post FRL placement; intentionally supersedes rear-reference location."""
import bpy,os,json,math,hashlib
from mathutils import Vector,Matrix
F=os.path.dirname(__file__)
def sig(o):
 d={'matrix':[list(r) for r in o.matrix_world],'hide':o.hide_render,'parent':o.parent.name if o.parent else None}
 if hasattr(o.data,'materials'):d['materials']=[m.name if m else None for m in o.data.materials]
 if o.type=='MESH':d['verts']=[list(v.co) for v in o.data.vertices]
 if o.type=='CURVE':d['points']=[[(list(p.co),list(p.handle_left),list(p.handle_right)) for p in s.bezier_points] for s in o.data.splines]
 return hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
def apply():
 s=bpy.context.scene
 if s.get('PN_FRL_front_operator_mount'):return
 root=bpy.data.objects['LM_ROOT_Move_Complete_Machine'];ri=root.matrix_world.inverted()
 prefixes=('PN_Filter_Regulator_','PN_Lubricator_','PN_FRL_','PN_Regulator_','PN_Knob_Grip_','PN_Gauge_','PN_Drain_','PR_Gauge_','PR_Lubricator_')
 group=[o for o in bpy.data.objects if o.name.startswith(prefixes) or o.name=='PN_Rear_Column_Mount']
 removed=[o for o in bpy.data.objects if o.name=='PN_Hose_Short_External_Supply' or o.name.startswith('PN_Supply_Tail_Connector_')]
 hose=bpy.data.objects['PN_Hose_Regulator_To_Rear_Valve']
 before={o.name:sig(o) for o in bpy.data.objects if o not in group+removed+[hose]}
 transform=root.matrix_world@Matrix.Rotation(math.pi,4,'Z')@ri
 matrices={o.name:o.matrix_world.copy() for o in group};group_set=set(group)
 appearance={o.name:{'dimensions':list(o.dimensions),'materials':[m.name if m else None for m in o.data.materials] if hasattr(o.data,'materials') else []} for o in group}
 for o in group:
  if o.parent not in group_set:o.matrix_world=transform@matrices[o.name]
 bpy.context.view_layer.update()
 for o in group:assert max(abs(o.matrix_world[r][c]-(transform@matrices[o.name])[r][c]) for r in range(4) for c in range(4))<1e-5,o.name
 mount=bpy.data.objects['PN_Rear_Column_Mount'];mount.name='PN_Front_Column_Mount'
 for o in removed:bpy.data.objects.remove(o,do_unlink=True)
 oldcurve=hose.data;sp=oldcurve.splines[0]
 original_start=ri@hose.matrix_world@sp.bezier_points[0].co
 end=ri@hose.matrix_world@sp.bezier_points[-1].co
 end_handle=ri@hose.matrix_world@sp.bezier_points[-1].handle_left
 start=Matrix.Rotation(math.pi,4,'Z')@original_start
 # Pass outside the front face below the nameplate, then along the machine's left exterior.
 pts=[start,Vector((.112,-.650,.918)),Vector((.13,-.675,1.018)),Vector((-.14,-.675,1.018)),Vector((-.325,-.60,1.105)),Vector((-.325,-.015,1.13)),end+(end_handle-end).normalized()*.022,end]
 curve=bpy.data.curves.new('PN_Front_FRL_Connected_Feed','CURVE');curve.dimensions='3D';curve.resolution_u=16;curve.bevel_depth=oldcurve.bevel_depth;curve.bevel_resolution=oldcurve.bevel_resolution;curve.use_fill_caps=True
 for mat in oldcurve.materials:curve.materials.append(mat)
 # Rounded polyline, bounded corners avoid spline overshoot into nearby parts.
 segments=[];cursor=pts[0]
 for i in range(1,len(pts)-1):
  a,p,b=pts[i-1:i+2];trim=min(.025,(p-a).length*.28,(b-p).length*.28)
  en=p+(a-p).normalized()*trim;ex=p+(b-p).normalized()*trim
  segments.extend([(cursor,en,None),(en,ex,p)]);cursor=ex
 segments.append((cursor,pts[-1],None));sp=curve.splines.new('BEZIER');sp.bezier_points.add(len(segments))
 inv=(ri@hose.matrix_world).inverted()
 for i,(a,b,corner) in enumerate(segments):
  p,q=sp.bezier_points[i:i+2];p.handle_left_type=p.handle_right_type=q.handle_left_type=q.handle_right_type='FREE'
  p.co=inv@a;q.co=inv@b;p.handle_right=inv@(a+(b-a)/3 if corner is None else a+(corner-a)*2/3);q.handle_left=inv@(b-(b-a)/3 if corner is None else b+(corner-b)*2/3)
 sp.bezier_points[0].handle_left=inv@start;sp.bezier_points[-1].handle_right=inv@end
 hose.data=curve
 if oldcurve.users==0:bpy.data.curves.remove(oldcurve)
 hose['start_fitting_point']=list(start);hose['end_fitting_point']=list(end);hose['routing']='Front-post FRL to unchanged rear valve tee destination; no loose supply tail.'
 bpy.context.view_layer.update()
 assert all(sig(bpy.data.objects[n])==v for n,v in before.items())
 assert (ri@hose.matrix_world@sp.bezier_points[-1].co-end).length<1e-6
 assert (bpy.data.objects['PN_Gauge_White_Face'].matrix_world.to_3x3()@Vector((0,0,1))).length>0
 s['PN_FRL_front_operator_mount']=True;s['PN_FRL_location_policy']='Intentional operator-side front post, below upper badge. Never restore rear photograph position. Loose external supply and tail connector removed.'
 json.dump({'protected':before,'moved':list(matrices),'appearance':appearance,'destination':list(end),'route':[list(p) for p in pts]},open(os.path.join(F,'front_frl_verification.json'),'w'),indent=2)
def run():
 apply()
 for file,label in [('generate_blockout.py','LM_GENERATION_SCRIPT'),('relocate_frl.py','LM_FRONT_FRL_SCRIPT')]:
  t=bpy.data.texts.get(label) or bpy.data.texts.new(label);t.clear();t.write(open(os.path.join(F,file),encoding='utf-8-sig').read())
 old=bpy.context.preferences.filepaths.save_version;bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=os.path.join(F,'lapping_machine_blockout.blend'));bpy.context.preferences.filepaths.save_version=old
 s=bpy.context.scene;cam=bpy.data.objects.new('TEMP_Front_FRL',bpy.data.cameras.new('TEMP_Front_FRL'));s.collection.objects.link(cam);s.camera=cam
 root=bpy.data.objects['LM_ROOT_Move_Complete_Machine'];cam.location=root.matrix_world@Vector((-.70,-1.85,1.23));target=root.matrix_world@Vector((-.035,-.48,.95));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=64
 s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True;s.render.resolution_x=640;s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=os.path.join(F,'front_frl_preview.png');bpy.ops.render.render(write_still=True)
 print('FRONT_FRL_SAVED',flush=True)
if __name__=='__main__':run()
