import bpy,json,os
from mathutils import Vector
F=os.path.dirname(os.path.abspath(__file__))
o=bpy.data.objects['IF_S1_Perforated_Insert'];s=bpy.context.scene
pts=[o.matrix_world@Vector(v) for v in o.bound_box];lo=Vector([min(p[k] for p in pts) for k in range(3)]);hi=Vector([max(p[k] for p in pts) for k in range(3)]);c=(lo+hi)/2
report={'insert':o.name,'bounds':[list(lo),list(hi)],'matrix':[list(r) for r in o.matrix_world],'modifiers':[{'name':m.name,'type':m.type,'object':m.object.name if m.type=='BOOLEAN' and m.object else None} for m in o.modifiers],'overlapping_candidates':[]}
for ob in bpy.data.objects:
 if ob.type!='MESH' or ob==o or ob.hide_render:continue
 p=[ob.matrix_world@Vector(v) for v in ob.bound_box];a=Vector([min(v[k] for v in p) for k in range(3)]);b=Vector([max(v[k] for v in p) for k in range(3)])
 if all(a[k]<hi[k] and b[k]>lo[k] for k in range(3)):report['overlapping_candidates'].append({'name':ob.name,'bounds':[list(a),list(b)]})
json.dump(report,open(os.path.join(F,'insert_pattern_inspection.json'),'w'),indent=2);print(json.dumps(report),flush=True)
for ob in s.objects:
 if ob.type not in {'LIGHT','CAMERA'}:ob.hide_render=ob!=o
cam=bpy.data.objects.new('IP_Temporary_Top',bpy.data.cameras.new('IP_Temporary_Top'));s.collection.objects.link(cam);cam.location=(c.x,c.y,hi.z+.5);cam.rotation_euler=(0,0,0);cam.data.type='ORTHO';cam.data.ortho_scale=(hi.x-lo.x)*1.16;s.camera=cam
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD';s.world.color=(.55,.55,.55)
s.render.resolution_x=512;s.render.resolution_y=512;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=os.path.join(F,'insert_top_preview.png');bpy.ops.render.render(write_still=True)
