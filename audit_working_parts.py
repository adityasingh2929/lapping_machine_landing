import bpy,json,os
from mathutils import Vector
r=bpy.data.objects['LM_ROOT_Move_Complete_Machine'];ri=r.matrix_world.inverted();out=[]
for o in bpy.data.objects:
 if o.type=='MESH' and (any(k in o.name for k in ['Hollow_Ring','Head_Lower','Head_Raised','Head_Hub','Head_Flange','Circular_Working','Plate_','Perforated','Bracket_Radial','Roller_Bracket'])):
  ps=[ri@o.matrix_world@Vector(v) for v in o.bound_box]
  out.append({'name':o.name,'lo':[min(v[k] for v in ps) for k in range(3)],'hi':[max(v[k] for v in ps) for k in range(3)],'hidden':o.hide_render,'mods':[(m.name,m.type,m.object.name if m.type=='BOOLEAN' and m.object else '') for m in o.modifiers],'verts':len(o.data.vertices)})
print(json.dumps(out));json.dump(out,open(os.path.join(os.path.dirname(bpy.data.filepath),'working_parts_audit.json'),'w'),indent=2)
