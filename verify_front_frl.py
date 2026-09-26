import bpy,os,json,runpy
from mathutils import Vector
from mathutils.geometry import interpolate_bezier
from mathutils.bvhtree import BVHTree
F=os.path.dirname(__file__);m=runpy.run_path(os.path.join(F,'relocate_frl.py'),run_name='verification');d=json.load(open(os.path.join(F,'front_frl_verification.json')))
assert all(m['sig'](bpy.data.objects[n])==v for n,v in d['protected'].items())
assert not bpy.data.objects.get('PN_Rear_Column_Mount')
assert not bpy.data.objects.get('PN_Hose_Short_External_Supply')
assert not any(o.name.startswith('PN_Supply_Tail_Connector_') for o in bpy.data.objects)
for old,record in d['appearance'].items():
 o=bpy.data.objects['PN_Front_Column_Mount' if old=='PN_Rear_Column_Mount' else old]
 assert max(abs(o.dimensions[k]-record['dimensions'][k]) for k in range(3))<1e-5,o.name
 if hasattr(o.data,'materials'):assert [mat.name if mat else None for mat in o.data.materials]==record['materials'],o.name
root=bpy.data.objects['LM_ROOT_Move_Complete_Machine'];ri=root.matrix_world.inverted()
h=bpy.data.objects['PN_Hose_Regulator_To_Rear_Valve'];bp=h.data.splines[0].bezier_points
assert (ri@h.matrix_world@bp[-1].co-Vector(d['destination'])).length<1e-6
points=[]
for a,b in zip(bp,bp[1:]):points.extend([h.matrix_world@p for p in interpolate_bezier(a.co,a.handle_right,b.handle_left,b.co,12)])
start,end=points[0],points[-1];points=[p for p in points if (p-start).length>.025 and (p-end).length>.025]
dep=bpy.context.evaluated_depsgraph_get();hits=[]
for o in bpy.data.objects:
 if o.type!='MESH' or o.hide_render:continue
 e=o.evaluated_get(dep);vs=[e.matrix_world@Vector(v) for v in e.bound_box]
 lo=Vector([min(v[k] for v in vs)-.005 for k in range(3)]);hi=Vector([max(v[k] for v in vs)+.005 for k in range(3)])
 near=[p for p in points if all(lo[k]<=p[k]<=hi[k] for k in range(3))]
 if not near:continue
 mesh=e.to_mesh();tree=BVHTree.FromPolygons([e.matrix_world@v.co for v in mesh.vertices],[list(f.vertices) for f in mesh.polygons])
 for p in near:
  hit=tree.find_nearest(p,h.data.bevel_depth+.0005)
  if hit[0] is not None:hits.append(o.name);break
 e.to_mesh_clear()
assert not hits,repr(hits)
assert bpy.data.texts['LM_GENERATION_SCRIPT'].as_string()==open(os.path.join(F,'generate_blockout.py'),encoding='utf-8-sig').read()
print('REOPEN VERIFIED: complete front assembly, no rear bracket or loose hose; feed destination unchanged; sampled hose surface clear; protected objects unchanged.')
