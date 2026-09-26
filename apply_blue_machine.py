import bpy,os,runpy,json,hashlib
folder=os.path.dirname(bpy.data.filepath)
def geometry_digest():
    h=hashlib.sha256()
    for o in sorted(bpy.data.objects,key=lambda x:x.name):
        h.update(repr((o.name,o.type,[list(r) for r in o.matrix_world],o.hide_render)).encode())
        if o.type=='MESH':
            h.update(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons])).encode())
        if o.type=='CURVE':
            h.update(repr([(s.type,[tuple(p.co) for p in s.points],[(tuple(p.co),tuple(p.handle_left),tuple(p.handle_right)) for p in s.bezier_points]) for s in o.data.splines]).encode())
    return h.hexdigest()
before=geometry_digest()
runpy.run_path(os.path.join(folder,'blue_machine_materials.py'))['apply']()
assert before==geometry_digest(),'Geometry changed unexpectedly'
for filename,textname in [('generate_blockout.py','LM_GENERATION_SCRIPT'),('blue_machine_materials.py','BM_MATERIAL_SCRIPT')]:
    t=bpy.data.texts.get(textname) or bpy.data.texts.new(textname)
    t.clear();t.write(open(os.path.join(folder,filename),encoding='utf-8-sig').read())
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
json.dump({'geometry_sha256':before,'objects':len(bpy.data.objects),'palette':'RAL 5002 digital approximation #00387B; photo-estimated secondary finishes'},open(os.path.join(folder,'blue_machine_verification.json'),'w'),indent=2)
print('BLUE_SAVED_GEOMETRY_UNCHANGED',before,flush=True)
