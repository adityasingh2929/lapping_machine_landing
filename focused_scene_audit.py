import bpy,json,os,hashlib
from mathutils import Vector
b=os.path.dirname(os.path.abspath(__file__));root=bpy.data.objects['LM_ROOT_Move_Complete_Machine'];ri=root.matrix_world.inverted()
r={'flags':{k:str(v) for k,v in bpy.context.scene.items()},'cameras':[o.name for o in bpy.data.objects if o.type=='CAMERA'],'objects':{}}
for o in bpy.data.objects:
 if o.type not in {'MESH','CURVE','FONT'}:continue
 pts=[ri@o.matrix_world@Vector(v) for v in o.bound_box]
 d={'bounds':[[min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]],'matrix':[list(row) for row in ri@o.matrix_world],'modifiers':[{'name':m.name,'type':m.type,'object':m.object.name if m.type=='BOOLEAN' and m.object else None} for m in o.modifiers]}
 if o.type=='MESH':d['vertices']=[list(ri@o.matrix_world@v.co) for v in o.data.vertices] if o.name in ['S1_Roller_Bracket','Circular_Working_Plate','S1_Aligned_Shaft','S1_Head_Hub'] else []
 r['objects'][o.name]=d
r['blend_sha256']=hashlib.sha256(open(bpy.data.filepath,'rb').read()).hexdigest()
json.dump(r,open(os.path.join(b,'focused_scene_audit.json'),'w'),indent=2)
print('FLAGS',r['flags']);print('CAMS',r['cameras'])
