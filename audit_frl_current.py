import bpy,json
from mathutils import Vector
r=bpy.data.objects['LM_ROOT_Move_Complete_Machine'];ri=r.matrix_world.inverted()
print('FRONT_FLAG',bpy.context.scene.get('PN_FRL_front_operator_mount'))
for o in bpy.data.objects:
 if o.name in ['Front_Centerline_Column','Rear_Centerline_Column','PN_Rear_Column_Mount','PN_Front_Column_Mount','PN_Gauge_White_Face','PN_FRL_Inlet_Hex','PN_FRL_Outlet_Hex','PR_Front_Beam_Badge_Exact','Console_Projecting_Upper_Housing','PN_Filter_Regulator_Body','PN_Lubricator_Body'] or o.name.startswith('PN_Hose_'):
  pts=[ri@o.matrix_world@Vector(v) for v in o.bound_box]
  d={'name':o.name,'parent':o.parent.name if o.parent else None,'lo':[min(p[k] for p in pts) for k in range(3)],'hi':[max(p[k] for p in pts) for k in range(3)]}
  if o.type=='CURVE':d['points']=[[list(ri@o.matrix_world@p.co) for p in s.bezier_points] for s in o.data.splines]
  print(json.dumps(d))
