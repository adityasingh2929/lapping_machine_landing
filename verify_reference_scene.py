"""Read-only Blender verification and withheld-feature projection. Never saves the .blend."""
import bpy,json,hashlib,os,math
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
BASE=os.path.dirname(os.path.abspath(__file__))
scene=bpy.context.scene;root=bpy.data.objects['LM_ROOT_Move_Complete_Machine'];ri=root.matrix_world.inverted()
fits=json.load(open(os.path.join(BASE,'reference_cameras.json')))
initial=json.load(open(os.path.join(BASE,'reference_inventory.json')))
def bounds(o):
    pts=[ri@o.matrix_world@Vector(v) for v in o.bound_box]
    return [min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]
def digest():
    h=hashlib.sha256()
    for o in sorted(bpy.data.objects,key=lambda ob:ob.name):
        if o.type not in {'MESH','CURVE','FONT'}:continue
        h.update(o.name.encode());h.update(str([list(r) for r in o.matrix_world]).encode())
        if o.type=='MESH':h.update(str([tuple(v.co) for v in o.data.vertices]).encode())
        elif o.type=='CURVE':h.update(str([[(tuple(p.co),tuple(p.handle_left),tuple(p.handle_right)) for p in s.bezier_points] for s in o.data.splines]).encode())
    return h.hexdigest()
report={'blend_path':bpy.data.filepath,'blend_sha256':hashlib.sha256(open(bpy.data.filepath,'rb').read()).hexdigest(),'geometry_sha256':digest(),'flags':{k:str(scene[k]) for k in scene.keys() if k.startswith('REF_')},'missing_preexisting_objects':sorted(set(initial)-set(bpy.data.objects.keys())),'reference_cameras':{},'stations':{},'bounds':{o.name:bounds(o) for o in bpy.data.objects if o.type in {'MESH','CURVE','FONT'}},'embedded_script_matches':bpy.data.texts['LM_GENERATION_SCRIPT'].as_string()==open(os.path.join(BASE,'generate_blockout.py'),encoding='utf-8').read()}
for i in range(1,17):
    n=f'REF_{i:02d}';o=bpy.data.objects.get(n);fit=fits[str(i)]
    assert o and o.type=='CAMERA',n
    expected=(Matrix(fit['world_to_cv']).transposed()@Matrix.Diagonal((1,-1,-1))).to_4x4();expected.translation=Vector(fit['camera_location'])
    actual=ri@o.matrix_world
    error=max(abs(actual[r][c]-expected[r][c]) for r in range(4) for c in range(4))
    report['reference_cameras'][n]={'source':o.get('reference_photo'),'original_size':[o.get('reference_width'),o.get('reference_height')],'matrix_max_error':error,'lens_mm':o.data.lens}
    assert o.get('reference_photo')==f'{i}.jpeg' and error<.00001
    expected_size=[3120,4160] if i<15 else [4160,3120]
    assert report['reference_cameras'][n]['original_size']==expected_size
    assert abs(o.data.lens-fit['focal_preview_px']*36/fit['preview_size'][0])<.0001
for i in range(1,4):
    parts={s:bounds(bpy.data.objects[f'S{i}_{s}']) for s in ['Hollow_Ring','Head_Lower_Disk','Head_Raised_Step','Cylinder_Body','Underside_Mount']}
    centers={s:[(a+b)/2 for a,b in zip(*bb)] for s,bb in parts.items()}
    report['stations'][str(i)]={'parts':parts,'centers':centers,'clearance':parts['Head_Lower_Disk'][0][2]-parts['Hollow_Ring'][1][2],'xy_alignment_error':max(math.dist(centers['Hollow_Ring'][:2],centers[s][:2]) for s in ['Head_Lower_Disk','Cylinder_Body','Underside_Mount'])}
    assert report['stations'][str(i)]['xy_alignment_error']<.0001
    assert abs(report['stations'][str(i)]['clearance']-.111)<.0001
# These observations were not used by the camera solver. They are diagnostic, not acceptance scores.
holdouts=json.load(open(os.path.join(BASE,'reference_holdouts.json')))
report['withheld_features']={}
for ns,items in holdouts.items():
    cam=bpy.data.objects[f'REF_{int(ns):02d}'];w,h=fits[ns]['preview_size']
    scene.camera=cam;scene.render.resolution_x=w;scene.render.resolution_y=h;scene.render.resolution_percentage=100
    rows=[]
    for item in items:
        o=bpy.data.objects[item['object']];lo,hi=bounds(o);p=Vector([(a+b)/2 for a,b in zip(lo,hi)])
        if item.get('point')=='top':p.z=hi[2]
        q=world_to_camera_view(scene,cam,root.matrix_world@p);uv=[q.x*w,(1-q.y)*h]
        row=dict(item);row['projected']=uv;row['root_point']=list(p);row['error_preview_px']=math.dist(uv,item['photo']);rows.append(row)
    report['withheld_features'][ns]=rows
report['hose_controls']={o.name:[[list(ri@o.matrix_world@p.co) for p in s.bezier_points] for s in o.data.splines] for o in bpy.data.objects if o.type=='CURVE' and o.name.startswith('PN_Hose_')}
assert not report['missing_preexisting_objects']
assert report['embedded_script_matches']
json.dump(report,open(os.path.join(BASE,'reference_saved_verification.json'),'w'),indent=2)
print('REFERENCE_REOPEN_VERIFIED',json.dumps({'reference_cameras':len(report['reference_cameras']),'missing_objects':report['missing_preexisting_objects'],'stations':{i:{k:v for k,v in s.items() if k in ('clearance','xy_alignment_error')} for i,s in report['stations'].items()},'embedded_script_matches':report['embedded_script_matches'],'geometry_sha256':report['geometry_sha256']},indent=2))
