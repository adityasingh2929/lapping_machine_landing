import bpy,json
from mathutils import Vector
out=[]
for o in bpy.data.objects:
 if o.type in {'MESH','CURVE','FONT'}:
  pts=[o.matrix_world@Vector(p) for p in o.bound_box]
  out.append(dict(name=o.name,parent=o.parent.name if o.parent else None,collections=[c.name for c in o.users_collection],bounds=[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]))
open('site_tools/console_audit.json','w').write(json.dumps(out,indent=2))
print('ROOT',list(bpy.data.objects['LM_ROOT_Move_Complete_Machine'].matrix_world))
