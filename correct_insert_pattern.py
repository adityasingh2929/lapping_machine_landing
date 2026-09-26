"""Complete only the existing S1 insert: inferred center + six-hole circular pattern."""
import bpy,bmesh,math,os,json,hashlib
from mathutils import Matrix,Vector
FOLDER=os.path.dirname(os.path.abspath(__file__))
INSERT='IF_S1_Perforated_Insert'
PREFIX='IF_S1_Insert_Opening_'
def protected_digest(o):
    d={'matrix':[list(r) for r in o.matrix_world],'parent':o.parent.name if o.parent else None,'hide':[o.hide_render,o.hide_viewport,o.hide_get()], 'materials':[m.name for m in o.data.materials] if hasattr(o.data,'materials') else [],'modifiers':[(m.name,m.type,m.object.name if m.type=='BOOLEAN' and m.object else None) for m in o.modifiers]}
    if o.type=='MESH':d['vertices']=[list(v.co) for v in o.data.vertices];d['faces']=[list(p.vertices) for p in o.data.polygons]
    elif o.type=='CURVE':d['splines']=[[(list(p.co),list(p.handle_left),list(p.handle_right)) for p in sp.bezier_points] for sp in o.data.splines]
    return hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
def run():
    s=bpy.context.scene;o=bpy.data.objects[INSERT]
    before={q.name:protected_digest(q) for q in bpy.data.objects if q!=o and not q.name.startswith(PREFIX)}
    original_matrix=o.matrix_world.copy();original_vertices=[tuple(v.co) for v in o.data.vertices]
    bounds=[Vector(p) for p in o.bound_box];radius=(max(p.x for p in bounds)-min(p.x for p in bounds))/2;thickness=max(p.z for p in bounds)-min(p.z for p in bounds)
    hole_radius=radius*(.029/.126);pitch=radius*(.080/.126)
    centers=[(0,0)]+[(pitch*math.cos(math.radians(a)),pitch*math.sin(math.radians(a))) for a in (180,0,240,300,60,120)]
    for m in list(o.modifiers):
        if m.type=='BOOLEAN' and m.object and m.object.name.startswith(PREFIX):o.modifiers.remove(m)
    for i,(x,y) in enumerate(centers):
        name=PREFIX+str(i);c=bpy.data.objects.get(name)
        me=bpy.data.meshes.new(name+'_Through_Cutter');bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=96,radius1=hole_radius,radius2=hole_radius,depth=thickness*4);bm.to_mesh(me);bm.free()
        if c:
            old=c.data;c.data=me
            if old.users==0:bpy.data.meshes.remove(old)
        else:
            c=bpy.data.objects.new(name,me);o.users_collection[0].objects.link(c);c.parent=o.parent
        c.matrix_world=o.matrix_world@Matrix.Translation((x,y,0));c.hide_render=True;c.hide_set(True);c.display_type='WIRE'
        mod=o.modifiers.new('Through hole '+str(i+1),'BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=c
    bpy.context.view_layer.update()
    assert o.matrix_world==original_matrix and [tuple(v.co) for v in o.data.vertices]==original_vertices
    assert len([q for q in bpy.data.objects if q.name==INSERT])==1
    assert len([q for q in bpy.data.objects if q.name.startswith(PREFIX)])==7
    # Test both directions through every opening, and positive hits on rim and webs.
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    for x,y in centers:
        assert not ev.ray_cast(Vector((x,y,thickness*3)),Vector((0,0,-1)))[0]
        assert not ev.ray_cast(Vector((x,y,-thickness*3)),Vector((0,0,1)))[0]
    assert ev.ray_cast(Vector((radius*.94,0,thickness*3)),Vector((0,0,-1)))[0]
    assert ev.ray_cast(Vector((pitch/2,0,thickness*3)),Vector((0,0,-1)))[0]
    bm=bmesh.new();bm.from_mesh(ev.data);assert all(e.is_manifold for e in bm.edges);bm.free()
    assert pitch-2*hole_radius>0 and radius-pitch-hole_radius>0
    assumption='Seven holes assumed: one center plus six on an equally spaced circular pitch. Two hidden rear holes inferred from work.jpeg; diameter and spacing regularized from visible arrangement.'
    o['evidence']=assumption;s['REF_insert_full_pattern']=assumption
    s['REF_insert_frame_assumptions']='S1 insert full seven-hole pattern inferred from work.jpeg; original thickness and outer diameter preserved. Existing cylinder/frame corrections unchanged.'
    t=bpy.data.texts.get('LM_GENERATION_SCRIPT') or bpy.data.texts.new('LM_GENERATION_SCRIPT');t.clear();t.write(open(os.path.join(FOLDER,'generate_blockout.py'),encoding='utf-8-sig').read())
    t=bpy.data.texts.get('LM_INSERT_PATTERN_SCRIPT') or bpy.data.texts.new('LM_INSERT_PATTERN_SCRIPT');t.clear();t.write(open(__file__,encoding='utf-8-sig').read())
    # Temporary isolation only: restore every visibility and presentation setting before saving.
    visibility={q.name:q.hide_render for q in s.objects};oldcam=s.camera
    renderkeys=('engine','resolution_x','resolution_y','resolution_percentage','filepath','film_transparent')
    oldrender={k:getattr(s.render,k) for k in renderkeys};oldformat=s.render.image_settings.file_format
    shading=s.display.shading;keys=('light','color_type','single_color','show_shadows','show_cavity','background_type');oldsh={k:(tuple(getattr(shading,k)) if k=='single_color' else getattr(shading,k)) for k in keys};oldworld=tuple(s.world.color)
    cam=bpy.data.objects.new('IP_Temporary_Top',bpy.data.cameras.new('IP_Temporary_Top'));s.collection.objects.link(cam)
    try:
        for q in s.objects:
            if q.type not in {'LIGHT','CAMERA'}:q.hide_render=q!=o
        cam.matrix_world=o.matrix_world@Matrix.Translation((0,0,.5));cam.data.type='ORTHO';cam.data.ortho_scale=radius*2.3;s.camera=cam
        s.render.engine='BLENDER_WORKBENCH';shading.light='STUDIO';shading.color_type='SINGLE';shading.single_color=(.12,.16,.20);shading.show_shadows=True;shading.show_cavity=True;shading.background_type='WORLD';s.world.color=(.72,.72,.72)
        s.render.resolution_x=512;s.render.resolution_y=512;s.render.resolution_percentage=100;s.render.film_transparent=False;s.render.image_settings.file_format='PNG';s.render.filepath=os.path.join(FOLDER,'insert_top_preview.png');bpy.ops.render.render(write_still=True)
    finally:
        s.camera=oldcam;cd=cam.data;bpy.data.objects.remove(cam,do_unlink=True);bpy.data.cameras.remove(cd)
        for name,value in visibility.items():bpy.data.objects[name].hide_render=value
        for k,v in oldrender.items():setattr(s.render,k,v)
        for k,v in oldsh.items():setattr(shading,k,v)
        s.world.color=oldworld;s.render.image_settings.file_format=oldformat
    assert all(protected_digest(bpy.data.objects[n])==v for n,v in before.items()),'Unrelated object or visibility changed'
    report={'hole_count':7,'hole_radius':hole_radius,'pitch_radius':pitch,'minimum_web':pitch-2*hole_radius,'outer_rim':radius-pitch-hole_radius,'outer_diameter':radius*2,'thickness':thickness,'assumption':assumption,'both_directions_open':True,'manifold':True,'normal_visibility_restored':True,'protected':before}
    json.dump(report,open(os.path.join(FOLDER,'insert_pattern_verification.json'),'w'),indent=2)
    versions=bpy.context.preferences.filepaths.save_version;bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(FOLDER,'lapping_machine_blockout.blend'));bpy.context.preferences.filepaths.save_version=versions
    print('INSERT_COMPLETE seven through-holes; dimensions and all unrelated objects preserved; assembly visibility restored',flush=True)
if __name__=='__main__':run()
