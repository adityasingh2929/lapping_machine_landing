"""Working assemblies matched to blue_machine/6.jpeg, 7.jpeg, 8.jpeg."""
import bpy,math,os,json,hashlib
from mathutils import Vector
F=os.path.dirname(__file__)
def signature(o):
 d={'matrix':[list(r) for r in o.matrix_world],'hide':o.hide_render,'materials':[m.name if m else None for m in o.data.materials] if hasattr(o.data,'materials') else [],'mods':[(m.name,m.type,m.object.name if m.type=='BOOLEAN' and m.object else None) for m in o.modifiers]}
 if o.type=='MESH':d['vertices']=[list(v.co) for v in o.data.vertices];d['faces']=[list(p.vertices) for p in o.data.polygons]
 return hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
def apply():
 s=bpy.context.scene
 if s.get('BM_working_parts_photo_match'):return
 root=bpy.data.objects['LM_ROOT_Move_Complete_Machine'];ri=root.matrix_world.inverted()
 def bounds(o):
  ps=[ri@o.matrix_world@Vector(v) for v in o.bound_box]
  return Vector([min(p[k] for p in ps) for k in range(3)]),Vector([max(p[k] for p in ps) for k in range(3)])
 targets={'Circular_Working_Plate','IF_S1_Perforated_Insert'}
 for o in bpy.data.objects:
  if any(k in o.name for k in ('_Hollow_Ring','_Head_Lower_Disk','_Disk_Rim_Hole','_Ring_Groove_','_Ring_Vertical_Slot_','_Carrier_Ring_Clearance','_Bracket_Radial_Arm','_Bracket_Support')) or o.name.startswith('IF_S1_Insert_Opening_'):targets.add(o.name)
 protected={o.name:signature(o) for o in bpy.data.objects if o.name not in targets}
 # Remove the old loose perforated workpiece and its private cutters.
 for o in list(bpy.data.objects):
  if o.name=='IF_S1_Perforated_Insert' or o.name.startswith('IF_S1_Insert_Opening_'):bpy.data.objects.remove(o,do_unlink=True)
 for i in (1,2,3):
  ring=bpy.data.objects[f'S{i}_Hollow_Ring'];lo,hi=bounds(ring);center=(lo+hi)/2
  for mod in list(ring.modifiers):
   if mod.type=='BOOLEAN' and mod.object and '_Ring_Groove_' in mod.object.name:
    cutter=mod.object;ring.modifiers.remove(mod);bpy.data.objects.remove(cutter,do_unlink=True)
  # Existing narrow slots continue through the ring wall and open at the bottom.
  for o in list(bpy.data.objects):
   if o.name.startswith(f'MD_S{i}_Ring_Vertical_Slot_'):
    mat=ri@o.matrix_world;inv=mat.inverted();a,b=bounds(o);mid=(a+b)/2
    direction=Vector((mid.x-center.x,mid.y-center.y,0)).normalized()
    for v in o.data.vertices:
     p=mat@v.co;rel=p-center;rad=rel.dot(direction)
     p+=direction*((rad-.135)*1.6+.135-rad)
     p.z=lo.z-.002+(p.z-a.z)/(b.z-a.z)*.045;v.co=inv@p
  # Extend the existing ring-clearance cuts below the carrier's underside.
  o=bpy.data.objects[f'MD_S{i}_Carrier_Ring_Clearance'];a,b=bounds(o);mat=ri@o.matrix_world;inv=mat.inverted()
  for v in o.data.vertices:
   p=mat@v.co;p.z=.735+(p.z-a.z)/(b.z-a.z)*.12;v.co=inv@p
  # Remove obsolete support prisms that crossed the clear ring interiors.
  for suffix in ('Bracket_Radial_Arm','Bracket_Support'):
   o=bpy.data.objects.get(f'S{i}_{suffix}')
   if o:
    for j in (1,2,3):
     mod=o.modifiers.new(f'Blue ring interior clearance {j}','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=bpy.data.objects[f'MD_S{j}_Carrier_Ring_Clearance']
  disk=bpy.data.objects[f'S{i}_Head_Lower_Disk'];a,b=bounds(disk);c=(a+b)/2;mat=ri@disk.matrix_world;inv=mat.inverted()
  for v in disk.data.vertices:
   p=mat@v.co;p.x=c.x+(p.x-c.x)*(.280/(b.x-a.x));p.y=c.y+(p.y-c.y)*(.280/(b.y-a.y));p.z=b.z-.014+(p.z-a.z)/(b.z-a.z)*.014;v.co=inv@p
  o=bpy.data.objects[f'MD_S{i}_Disk_Rim_Hole'];mat=ri@o.matrix_world;inv=mat.inverted()
  for v in o.data.vertices:
   p=mat@v.co;p.x=c.x+(p.x-c.x)*(.280/.252);p.y=c.y+(p.y-c.y)*(.280/.252);p.z+=.006;v.co=inv@p
 # Shallow radial scoring across the shared working plate, as visible through all rings.
 plate=bpy.data.objects['Circular_Working_Plate'];a,b=bounds(plate)
 for mod in list(plate.modifiers):
  if mod.type=='BOOLEAN' and mod.object and mod.object.name=='MD_Plate_Visible_Division':plate.modifiers.remove(mod)
 for i in range(8):
  angle=i*math.tau/8+.12;radius=.188
  name=f'BM_Working_Radial_Score_{i}';mesh=bpy.data.meshes.new(name)
  mesh.from_pydata([(x,y,z) for x in (-.5,.5) for y in (-.5,.5) for z in (-.5,.5)],[],[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]);mesh.update()
  o=bpy.data.objects.new(name,mesh);s.collection.objects.link(o);o.parent=root
  o.location=(radius*math.cos(angle),radius*math.sin(angle),b.z-.0003);o.rotation_euler.z=angle;o.scale=(.285,.00065,.0013)
  o.hide_render=True;o.hide_set(True)
  mod=plate.modifiers.new(f'Radial surface score {i}','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=o
 # Subtle metal variation, retaining the existing warm-steel and silver palette.
 for name,rough,scale,strength in [('BM_Conditioning_Ring_Warm_Steel',.42,190,.10),('BM_Lapping_Plate_Machined_Steel',.36,110,.08)]:
  m=bpy.data.materials[name];nt=m.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Roughness'].default_value=rough
  tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=2
  bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=strength;bump.inputs['Distance'].default_value=.00004
  nt.links.new(tex.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
 bpy.context.view_layer.update()
 assert all(signature(bpy.data.objects[n])==v for n,v in protected.items())
 s['BM_working_parts_photo_match']=True
 json.dump({'protected':protected,'notes':'Plain slotted rings, continuous scored working plate, removed perforated insert and carrier intrusions, thinner broader pressure discs. Dimensions inferred visually, not measured.'},open(os.path.join(F,'blue_working_verification.json'),'w'),indent=2)
def run():
 apply()
 import bmesh
 for o in bpy.data.objects:
  if o.name.startswith('BM_Working_Radial_Score_'):
   bm=bmesh.new();bm.from_mesh(o.data)
   if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(o.data);o.data.update()
   bm.free()
 for file,label in [('generate_blockout.py','LM_GENERATION_SCRIPT'),('match_blue_working_parts.py','BM_WORKING_PARTS_SCRIPT'),('blue_machine_materials.py','BM_MATERIAL_SCRIPT')]:
  t=bpy.data.texts.get(label) or bpy.data.texts.new(label);t.clear();t.write(open(os.path.join(F,file),encoding='utf-8-sig').read())
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=os.path.join(F,'lapping_machine_blockout.blend'))
if __name__=='__main__':run()
