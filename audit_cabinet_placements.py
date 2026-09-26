import bpy,json
from mathutils import Vector
r=bpy.data.objects['LM_ROOT_Move_Complete_Machine'];ri=r.matrix_world.inverted()
for o in bpy.data.objects:
 if o.name in ['Panel_Left','Panel_Right','Panel_Rear','Panel_Front','Rear_Centerline_Column','Front_Centerline_Column','Console_Lower_Cabinet','PR_Console_Fascia_Badge_Exact'] or o.name.startswith(('NP_Cabinet','PR_Cabinet_Left_Badge')):
  pts=[ri@o.matrix_world@Vector(v) for v in o.bound_box]
  print(json.dumps({'name':o.name,'min':[min(p[k] for p in pts) for k in range(3)],'max':[max(p[k] for p in pts) for k in range(3)],'center':list(ri@o.matrix_world.translation),'materials':[s.material.name if s.material else None for s in o.material_slots],'props':dict(o.items())},default=str))
print('PACKED',[(i.name,bool(i.packed_file)) for i in bpy.data.images if i.source=='FILE'])
