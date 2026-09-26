import bpy,json,os
p=os.path.dirname(bpy.data.filepath)
out={'file':bpy.data.filepath,'version':bpy.app.version_string,'materials':[], 'cameras':[], 'scene':{}}
for m in bpy.data.materials:
    nodes=list(m.node_tree.nodes) if m.use_nodes else []
    bs=next((n for n in nodes if n.type=='BSDF_PRINCIPLED'),None)
    out['materials'].append({'name':m.name,'color':list(bs.inputs['Base Color'].default_value) if bs else list(m.diffuse_color),'users':[o.name for o in bpy.data.objects if any(s.material==m for s in o.material_slots)]})
for o in bpy.data.objects:
    if o.type=='CAMERA':out['cameras'].append({'name':o.name,'loc':list(o.location)})
s=bpy.context.scene
out['scene']={'camera':s.camera.name if s.camera else None,'engine':s.render.engine,'resolution':[s.render.resolution_x,s.render.resolution_y], 'objects':len(s.objects)}
open(os.path.join(p,'blue_material_audit.json'),'w').write(json.dumps(out,indent=2))
print('AUDIT_DONE',out['scene'])
