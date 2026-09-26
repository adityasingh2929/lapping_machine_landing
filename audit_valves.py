import bpy,json
from mathutils import Vector
r=bpy.data.objects['LM_ROOT_Move_Complete_Machine'];ri=r.matrix_world.inverted()
a=[]
for o in bpy.data.objects:
 if 'Valve' in o.name or o.name.startswith('PN_Hose_S') or o.name.startswith('IF_') and ('Port' in o.name or 'Elbow' in o.name) or o.name.startswith('PROVISIONAL_'):
  d={'name':o.name,'type':o.type,'bounds':[list(ri@o.matrix_world@Vector(v)) for v in o.bound_box]}
  if o.type=='CURVE':d['points']=[[list(ri@o.matrix_world@p.co) for p in s.bezier_points] for s in o.data.splines]
  a.append(d)
json.dump(a,open('C:/Users/2023a/Downloads/lapping_machine/blender_models/valve_audit.json','w'),indent=2)
print('AUDITED',len(a))
