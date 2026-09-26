"""Export the saved machine for the website. Never save edits to the source .blend."""
import bpy,os,math,json,sys,hashlib
from mathutils import Vector
F=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));OUT=os.path.join(F,'docs','assets')
os.makedirs(OUT,exist_ok=True)
blue='--blue' in sys.argv
slug='micro-blue' if blue else 'micro-mlp42'
source_hash=hashlib.sha256(open(bpy.data.filepath,'rb').read()).hexdigest()
if blue:assert bpy.context.scene.get('BM_working_parts_photo_match'), 'Blue source is missing the latest plate corrections'
s=bpy.context.scene;root=bpy.data.objects['LM_ROOT_Move_Complete_Machine']
if bpy.context.object and bpy.context.object.mode != 'OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
assert s.get('NP_supplied_nameplates') and s.get('VP_reference_valves')
# Bake the actual nameplate print shaders into portable base-color textures.
s.render.engine='CYCLES';s.cycles.samples=1;s.cycles.device='CPU'
for index in (1,2):
    mat=bpy.data.materials[f'NP_Exact_Plate_{index}'];nt=mat.node_tree
    bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL')
    target=next(o for o in bpy.data.objects if o.type=='MESH' and any(m==mat for m in o.data.materials))
    bpy.ops.object.select_all(action='DESELECT');target.hide_set(False);target.select_set(True);bpy.context.view_layer.objects.active=target
    imgs={}
    for label,socket in [('color','Base Color'),('metal','Metallic')]:
        cached=os.path.join(OUT,f'plate-{index}-{label}.png')
        if os.path.exists(cached):
            imgs[label]=bpy.data.images.load(cached)
            if label=='metal':imgs[label].colorspace_settings.name='Non-Color'
            continue
        img=bpy.data.images.new(f'Web_Plate_{index}_{label}',width=1024,height=624 if index==1 else 304,alpha=False)
        if label=='metal':img.colorspace_settings.name='Non-Color'
        tex=nt.nodes.new('ShaderNodeTexImage');tex.image=img;nt.nodes.active=tex
        em=nt.nodes.new('ShaderNodeEmission');src=bs.inputs[socket].links[0].from_socket
        nt.links.new(src,em.inputs[0]);nt.links.new(em.outputs[0],out.inputs[0])
        bpy.ops.object.bake(type='EMIT',margin=1,use_clear=True)
        img.filepath_raw=os.path.join(OUT,f'plate-{index}-{label}.png');img.file_format='PNG';img.save();imgs[label]=img
        nt.nodes.remove(em)
    nt.nodes.clear();bs=nt.nodes.new('ShaderNodeBsdfPrincipled');out=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(bs.outputs[0],out.inputs[0])
    tex=nt.nodes.new('ShaderNodeTexImage');tex.image=imgs['color'];nt.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    metal=nt.nodes.new('ShaderNodeTexImage');metal.image=imgs['metal'];sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(metal.outputs[0],sep.inputs[0]);nt.links.new(sep.outputs[2],bs.inputs['Metallic']);bs.inputs['Roughness'].default_value=.4
# Export only visible machine components. Boolean cutters, studio, lights and cameras stay out.
def belongs(o):
    p=o
    while p:
        if p==root:return True
        p=p.parent
    return False
objects=[o for o in bpy.data.objects if o.type in {'MESH','CURVE','FONT'} and belongs(o) and not o.hide_render]
for o in objects:
    o.hide_set(False);o.hide_viewport=False
    for m in o.modifiers:
        if m.type=='BEVEL':m.segments=min(m.segments,2)
    if o.type=='CURVE':o.data.resolution_u=6;o.data.bevel_resolution=min(o.data.bevel_resolution,2)
# Evaluated meshes include real insert holes and every other retained correction.
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.convert(target='MESH')
for o in bpy.context.selected_objects:
    if o.type=='MESH' and o.data.uv_layers:
        active=o.data.uv_layers.active
        for layer in list(o.data.uv_layers):
            if layer!=active:o.data.uv_layers.remove(layer)
        active.name='UVMap'
bpy.ops.object.join();model=bpy.context.object;model.name='Micro_MLP_42'
# Flatten procedural paint to its existing PBR base values for consistent browser rendering.
for mat in model.data.materials:
    if not mat or mat.name.startswith('NP_'):continue
    if mat.use_nodes:
        bs=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
        if bs:
            for key in ['Roughness','Normal']:
                for link in list(bs.inputs[key].links):mat.node_tree.links.remove(link)
# Collapse coplanar subdivisions while retaining curved surfaces and materials.
dec=model.modifiers.new('Web coplanar optimization','DECIMATE');dec.decimate_type='DISSOLVE';dec.angle_limit=.0087
bpy.ops.object.modifier_apply(modifier=dec.name)
model.data.calc_loop_triangles();print('WEB_TRIANGLES',len(model.data.loop_triangles),flush=True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,slug+'.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
json.dump({'source':os.path.basename(bpy.data.filepath),'source_sha256':source_hash,'triangles':len(model.data.loop_triangles),'objects_exported':len(objects)},open(os.path.join(OUT,slug+'-source.json'),'w'),indent=2)
print('WEB_GLB_BYTES',os.path.getsize(os.path.join(OUT,slug+'.glb')),flush=True)
