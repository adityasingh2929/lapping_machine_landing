"""Three reference-style manual pneumatic valves, independently editable.
Visible valve silhouette based on supplied reference; hidden feed routing inferred.
"""
import bpy,math,os,json,hashlib
from mathutils import Vector,Matrix
FOLDER=os.path.dirname(os.path.abspath(__file__))
root=bpy.data.objects['LM_ROOT_Move_Complete_Machine'];ri=root.matrix_world.inverted()
col=bpy.data.collections.get('Reference_Valve_Assemblies')
if not col:
    col=bpy.data.collections.new('Reference_Valve_Assemblies');bpy.context.scene.collection.children.link(col)
def mat(name,c,metal=0,rough=.35):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*c,1)
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    return m
silver=mat('VP_Machined_Aluminium',(.48,.5,.52),.8)
black=mat('VP_Black_Moulded_Rubber',(.009,.011,.014),0,.48)
brass=mat('VP_Brass_Fittings',(.5,.29,.09),.78)
blue=bpy.data.materials['PN_Material_Air_Blue']
white=mat('VP_White_Label',(.78,.8,.8),0,.55)
labelblue=mat('VP_Blue_Label',(.004,.11,.34),0,.55)

def finish(o,name,m):
    o.name=name
    for c in list(o.users_collection):c.objects.unlink(o)
    col.objects.link(o);o.parent=root;o.matrix_parent_inverse=Matrix.Identity(4);o.data.materials.clear();o.data.materials.append(m)
    return o
def box(name,frame,center,dims,m,bevel=.0006):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o=finish(bpy.context.object,name,m);o.scale=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.matrix_basis=frame@Matrix.Translation(center)
    if bevel:b=o.modifiers.new('Manufactured edge radii','BEVEL');b.width=bevel;b.segments=3
    return o
def cyl(name,frame,a,b,r,m,n=32,r2=None):
    a=Vector(a);b=Vector(b)
    if r2 is None:bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=(b-a).length)
    else:bpy.ops.mesh.primitive_cone_add(vertices=n,radius1=r,radius2=r2,depth=(b-a).length)
    o=finish(bpy.context.object,name,m);o.matrix_basis=frame@Matrix.Translation((a+b)/2)@(b-a).to_track_quat('Z','Y').to_matrix().to_4x4()
    for p in o.data.polygons:p.use_smooth=len(p.vertices)==4 and n>8
    mod=o.modifiers.new('Fine edge bevel','BEVEL');mod.width=.0003;mod.segments=2
    return o
def hose(name,pts,r=.0028):
    old=bpy.data.objects.get(name)
    if old:bpy.data.objects.remove(old,do_unlink=True)
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=16;cu.bevel_depth=r;cu.bevel_resolution=4;cu.use_fill_caps=True
    s=cu.splines.new('BEZIER');s.bezier_points.add(len(pts)-1)
    for p,co in zip(s.bezier_points,pts):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,cu);col.objects.link(o);o.parent=root;cu.materials.append(blue);return o
def bounds(name):
    o=bpy.data.objects[name];pts=[ri@o.matrix_world@Vector(p) for p in o.bound_box]
    return Vector([min(p[k] for p in pts) for k in range(3)]),Vector([max(p[k] for p in pts) for k in range(3)])
def ends(name):
    o=bpy.data.objects[name];s=o.data.splines[0]
    return [ri@o.matrix_world@s.bezier_points[k].co for k in (0,-1)]
def relevant(n):return n.startswith(('VP_','PN_Rear_Valve_Tee_','PN_Hose_Regulator_To_Rear_Valve','PN_Hose_Approximate_Under_Beam_Link')) or any(n.startswith(f'PN_S{i}_Valve_') or n.startswith(f'PN_Hose_S{i}_') for i in (1,2,3))
def digest(o):
    d={'matrix':[list(r) for r in o.matrix_world],'hide':o.hide_render,'mats':[m.name for m in o.data.materials] if hasattr(o.data,'materials') else []}
    if o.type=='MESH':d['v']=[list(v.co) for v in o.data.vertices];d['f']=[list(p.vertices) for p in o.data.polygons]
    if o.type=='CURVE':d['s']=[[(list(p.co),list(p.handle_left),list(p.handle_right)) for p in s.bezier_points] for s in o.data.splines]
    return hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
def apply():
    if bpy.context.scene.get('VP_reference_valves'):return
    protected={o.name:digest(o) for o in bpy.data.objects if not relevant(o.name)}
    ports={i:(ends(f'PN_Hose_S{i}_Vertical_Cylinder_Run')[0],ends(f'PN_Hose_S{i}_Lower_Loop')[1]) for i in (1,2,3)}
    supply=bpy.data.objects['PN_Hose_Regulator_To_Rear_Valve'];supplypts=[ri@supply.matrix_world@p.co for p in supply.data.splines[0].bezier_points]
    for o in list(bpy.data.objects):
        if relevant(o.name):bpy.data.objects.remove(o,do_unlink=True)
    feeds={};frames={};report=[]
    for i in (1,2,3):
        lo,hi=bounds(f'S{i}_Cylinder_Body');c=(lo+hi)/2;sign=1 if i==3 else -1
        surface=(bounds('PROVISIONAL_Longitudinal_Spine')[0].x if i==1 else bounds(f'PROVISIONAL_S{i}_Lateral_Branch')[1 if sign>0 else 0].x)
        # Local X: horizontal across valve; local Y: up; local Z: outward from frame.
        f=Matrix(((0,0,sign,surface+sign*.014),(sign,0,0,c.y),(0,1,0,1.103),(0,0,0,1)));frames[i]=f
        pre=f'VP_S{i}_'
        box(pre+'Mount',f,(0,.001,-.011),(.032,.058,.004),black)
        box(pre+'Valve_Body',f,(0,0,0),(.030,.042,.019),silver)
        box(pre+'Top_End_Cap',f,(0,.027,0),(.032,.012,.021),black,.0013)
        box(pre+'Lower_End_Cap',f,(0,-.025,0),(.029,.009,.020),black,.001)
        # Small printed face panel, schematic markings; unreadable reference text is not invented.
        box(pre+'Face_Label',f,(.002,.001,.0097),(.017,.033,.0003),white,.00015)
        box(pre+'Label_Blue_Strip',f,(-.004,.001,.00995),(.005,.033,.00015),labelblue,.00005)
        for k,y in enumerate((-.010,-.002,.006,.013)):
            box(pre+f'Schematic_{k}',f,(.004,y,.0101),(.006,.00065,.00012),black,.00002)
        for k,y in enumerate((.027,-.025)):
            for j,x in enumerate((-.0105,.0105)):
                cyl(pre+f'Mount_Screw_{k}_{j}',f,(x,y,.010),(x,y,.0112),.0022,silver,24)
                cyl(pre+f'Screw_Socket_{k}_{j}',f,(x,y,.0112),(x,y,.0113),.001,black,6)
        # Downward manual lever with tapered rubber boot and rounded grip.
        cyl(pre+'Lever_Boot',f,(0,-.028,.001),(0,-.043,.005),.0105,black,48,.0045)
        cyl(pre+'Lever_Stem',f,(0,-.043,.005),(0,-.055,.009),.0035,silver)
        cyl(pre+'Lever_Grip',f,(0,-.051,.008),(0,-.078,.014),.0065,black,48,.005)
        def fit(tag,x,y,direction):
            a=Vector((x,y,.001));n=Vector((direction,0,0))
            cyl(pre+tag+'_Thread',f,a,a+n*.005,.005,brass,24)
            cyl(pre+tag+'_Hex',f,a+n*.004,a+n*.011,.006,silver,6)
            cyl(pre+tag+'_Collar',f,a+n*.011,a+n*.015,.0054,black)
            cyl(pre+tag+'_Release',f,a+n*.015,a+n*.017,.0048,blue)
            return f@(a+n*.017)
        top=fit('Upper_Cylinder_Port',-.015,.012,-1);bottom=fit('Lower_Cylinder_Port',-.015,-.008,-1)
        feed=fit('Supply_Port',.015,0,1);feeds[i]=feed
        for j,y in enumerate((.015,-.015)):
            cyl(pre+f'Brass_Plug_{j}',f,(.015,y,0),(.023,y,0),.0042,brass,12)
        normal=Vector((sign,0,0));left=Vector((0,-sign,0));a,b=ports[i]
        outer=surface+sign*.062
        hose(f'PN_Hose_S{i}_Vertical_Cylinder_Run',[a,a+normal*.018,Vector((outer,c.y,hi.z-.025)),Vector((outer,c.y,1.162)),top+left*.020+normal*.012,top+left*.009,top])
        hose(f'PN_Hose_S{i}_Lower_Loop',[bottom,bottom+left*.013,bottom+left*.031+normal*.017+Vector((0,0,-.020)),Vector((outer,c.y-sign*.055,1.157)),b+normal*.013,b])
        report.append({'station':i,'frame':[list(r) for r in f],'top':list(top),'bottom':list(bottom),'feed':list(feed)})
    # Common supply tee immediately outside station 2, with real joined tube endpoints.
    f=frames[2];tee=feeds[2]+Vector((0,-.018,0));cyl('VP_S2_Supply_Tee',Matrix.Identity(4),feeds[2],tee,.0055,silver,6)
    cyl('VP_S2_Tee_Cross',Matrix.Identity(4),tee+Vector((-.009,0,0)),tee+Vector((.009,0,0)),.0055,silver,6)
    # Preserve upstream regulator route, replace its approach to the new tee.
    hose('PN_Hose_Regulator_To_Rear_Valve',supplypts[:-3]+[Vector((-.30,.15,1.11)),tee+Vector((-.018,0,0)),tee+Vector((-.009,0,0))])
    hose('PN_Hose_Approximate_Under_Beam_Link',[tee+Vector((.009,0,0)),tee+Vector((.018,-.010,-.022)),Vector((-.285,.22,1.025)),Vector((0,.29,1.025)),Vector((.29,.22,1.025)),feeds[3]+Vector((.018,.025,-.006)),feeds[3]+Vector((0,.010,0)),feeds[3]])
    hose('VP_S1_Supply_Hose',[tee,Vector((-.29,.03,1.037)),Vector((-.30,-.26,1.037)),Vector((-.13,-.28,1.077)),feeds[1]+Vector((0,-.016,0)),feeds[1]])
    bpy.context.view_layer.update()
    assert all(digest(bpy.data.objects[n])==v for n,v in protected.items()),'Unrelated geometry changed'
    bpy.context.scene['VP_reference_valves']=True
    json.dump({'protected':protected,'stations':report,'note':'Three matching manual valves. Hidden supply distribution inferred.'},open(os.path.join(FOLDER,'valve_verification.json'),'w'),indent=2)
    print('VALVES_VERIFIED: three complete assemblies, unrelated objects unchanged')

def run():
    apply()
    # The widened diagonal frame and broad underside plates require stand-off brackets.
    # Keep every lever outside the plate envelope rather than cutting unrelated structure.
    if not bpy.context.scene.get('VP_clearance_brackets'):
        report=json.load(open(os.path.join(FOLDER,'valve_verification.json')))
        centers={};deltas={}
        for rec in report['stations']:
            i=rec['station'];f=Matrix(rec['frame']);sign=1 if i==3 else -1
            centers[i]=f.translation.copy();delta=Vector((sign*.060,0,0));deltas[i]=delta
            for o in list(bpy.data.objects):
                if o.name.startswith(f'VP_S{i}_') and o.type=='MESH':o.location+=delta
            for j,y in enumerate((-.018,.024)):
                box(f'VP_S{i}_Standoff_{j}',f,(0,y,.016),(.025,.008,.060),silver)
            rec['frame']=[list(row) for row in Matrix.Translation(delta)@f]
            for k in ('top','bottom','feed'):rec[k]=list(Vector(rec[k])+delta)
        # Move the tube approach points along with the fittings, keeping cylinder ends fixed.
        for o in bpy.data.objects:
            if o.type!='CURVE' or not relevant(o.name):continue
            inv=(ri@o.matrix_world).inverted();matrix=ri@o.matrix_world
            for spline in o.data.splines:
                for p in spline.bezier_points:
                    pos=matrix@p.co
                    delta=Vector((0,0,0))
                    for i,c in centers.items():
                        d=(pos-c).length;weight=max(0,min(1,(.14-d)/.08));delta+=deltas[i]*weight
                    p.co=inv@(pos+delta)
        # Explicit endpoint seating overrides the falloff at the three supply ports.
        for rec in report['stations']:
            i=rec['station'];feed=Vector(rec['feed'])
            top=bpy.data.objects[f'PN_Hose_S{i}_Vertical_Cylinder_Run'].data.splines[0].bezier_points
            bottom=bpy.data.objects[f'PN_Hose_S{i}_Lower_Loop'].data.splines[0].bezier_points
            top[-1].co=rec['top'];bottom[0].co=rec['bottom']
            if i==1:bpy.data.objects['VP_S1_Supply_Hose'].data.splines[0].bezier_points[-1].co=feed
            if i==3:bpy.data.objects['PN_Hose_Approximate_Under_Beam_Link'].data.splines[0].bezier_points[-1].co=feed
        bpy.context.view_layer.update()
        bpy.context.scene['VP_clearance_brackets']=True
        report['clearance']='Valve bodies moved 0.060 outward on metal stand-offs; levers clear diagonal frame and underside plates.'
        assert all(digest(bpy.data.objects[n])==v for n,v in report['protected'].items())
        json.dump(report,open(os.path.join(FOLDER,'valve_verification.json'),'w'),indent=2)
    # Cylinder-side endpoints stay on their original fittings after route adjustment.
    for i in (1,2,3):
        for port,route,idx in [('Top','Vertical_Cylinder_Run',0),('Lower','Lower_Loop',-1)]:
            lo,hi=bounds(f'PN_S{i}_Cylinder_{port}_Port_Release');p=(lo+hi)/2;p.x=hi.x if i==3 else lo.x
            bpy.data.objects[f'PN_Hose_S{i}_{route}'].data.splines[0].bezier_points[idx].co=p
    for filename,key in [('generate_blockout.py','LM_GENERATION_SCRIPT'),('valve_correction.py','LM_VALVE_CORRECTION_SCRIPT')]:
        t=bpy.data.texts.get(key) or bpy.data.texts.new(key);t.clear();t.write(open(os.path.join(FOLDER,filename),encoding='utf-8-sig').read())
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(FOLDER,'lapping_machine_blockout.blend'))
if __name__=='__main__':run()
