"""Incremental mechanical, console and pneumatic maintenance for the SINGLE working lapping_machine_blockout.blend.
Blender 5.2. Open that file, then run this script. No machine regeneration.
Existing named objects (including manually edited controls) are never replaced.
Delete a particular CC_, PN_ or MD_ detail if you deliberately want it rebuilt from its defaults.
"""
import math, os, json, hashlib, sys

def apply_reference_corrections(scene,root):
    """One-time evidence-backed edits, common to all sixteen views. Preserve existing object data."""
    import bpy,re
    from mathutils import Matrix,Vector
    if scene.get('REF_geometry_pass_1'):return
    # Missing flags alone are not proof that geometry is uncorrected.
    ri_check=root.matrix_world.inverted()
    pts=[ri_check@bpy.data.objects['S1_Hollow_Ring'].matrix_world@Vector(v) for v in bpy.data.objects['S1_Hollow_Ring'].bound_box]
    if abs((min(p.y for p in pts)+max(p.y for p in pts))/2+.19)>.0001:
        raise RuntimeError('Unflagged station geometry differs from the audited baseline; inspect before applying corrections.')
    ri=root.matrix_world.inverted();shift=.033;radial=.936
    stations={1:Vector((0,-.19,0)),2:Vector((-.164545,.095,0)),3:Vector((.164545,.095,0))}
    changed=[]
    for o in list(bpy.data.objects):
        if o.type not in {'MESH','CURVE','FONT'}:continue
        n=o.name
        station=re.search(r'(?:^|_)S([123])_',n)
        m=ri@o.matrix_world
        if n in ('Front_Centerline_Column','Rear_Centerline_Column'):
            inv=m.inverted()
            for v in o.data.vertices:
                p=m@v.co
                if p.z>1.0:p.z+=shift
                v.co=inv@p
            changed.append(n);continue
        if station:
            i=int(station.group(1));delta=stations[i]*(radial-1)
            # Entire ring/roller/bracket groups move together; upper station groups retain shaft alignment.
            lo=min((m@Vector(v)).z for v in o.bound_box)
            if lo>.89:delta.z=shift
            m.translation+=delta;o.matrix_world=root.matrix_world@m;changed.append(n)
        elif n.startswith('PROVISIONAL_'):
            m.translation.z+=shift
            if 'Lateral_Branch' in n:
                i=2 if 'S2' in n else 3
                inv=m.inverted(); anchor=-.0425 if i==2 else .0425
                for v in o.data.vertices:
                    p=m@v.co;p.x=anchor+(p.x-anchor)*(.174014/.184545);p.y+=stations[i].y*(radial-1)
                    v.co=inv@p
            o.matrix_world=root.matrix_world@m;changed.append(n)
        elif n in ('Front_Column_Cap','Rear_Column_Cap') or n.startswith(('MD_Front_Cap','MD_Rear_Cap','PR_Front_Beam_Badge')):
            m.translation.z+=shift;o.matrix_world=root.matrix_world@m;changed.append(n)
        elif n=='PN_Hose_Approximate_Under_Beam_Link':
            inv=m.inverted()
            for s in o.data.splines:
                for b in s.bezier_points:
                    for attr in ('co','handle_left','handle_right'):
                        p=m@getattr(b,attr);p.x*=radial;p.y*=radial;p.z+=shift;setattr(b,attr,inv@p)
            changed.append(n)
        elif n=='PN_Hose_Regulator_To_Rear_Valve':
            inv=m.inverted()
            for s in o.data.splines:
                for b in s.bezier_points:
                    for attr in ('co','handle_left','handle_right'):
                        p=m@getattr(b,attr);t=max(0,min(1,(p.z-.95)/.10));p+=Vector((-.164545*(radial-1),.095*(radial-1),shift))*t;setattr(b,attr,inv@p)
            changed.append(n)
        elif n.startswith('PN_Rear_Valve_Tee_'):
            m.translation+=Vector((-.164545*(radial-1),.095*(radial-1),shift));o.matrix_world=root.matrix_world@m;changed.append(n)
    bpy.context.view_layer.update()
    scene['REF_geometry_pass_1']=True
    scene['REF_upper_translation']=shift;scene['REF_station_radius_scale']=radial
    scene['REF_geometry_evidence']='Upper separation and station spacing: joint structural landmark fit across 1-11,15,16; review gallery for remaining residuals.'
    folder=os.path.dirname(os.path.abspath(__file__))
    json.dump({'upper_translation':shift,'station_radius_scale':radial,'head_clearance_before':.073,'head_clearance_after':.106,'objects_changed':changed},open(os.path.join(folder,'reference_geometry_changes.json'),'w'),indent=2)

def refine_reference_corrections(scene,root):
    import bpy,re
    from mathutils import Matrix,Vector
    if scene.get('REF_geometry_pass_2'):return
    ri=root.matrix_world.inverted();beam_delta=-.0275;head_delta=.005
    stations={1:Vector((0,-.19,0)),2:Vector((-.164545,.095,0)),3:Vector((.164545,.095,0))}
    changed=[]
    def stretch_z(z):
        return z+head_delta+(beam_delta-head_delta)*max(0,min(1,(z-1.032)/.044))
    def cylinder_z(z):
        return z+beam_delta+(head_delta-beam_delta)*max(0,min(1,(z-1.191)/.219))
    for o in list(bpy.data.objects):
        if o.type not in {'MESH','CURVE','FONT'}:continue
        n=o.name;m=ri@o.matrix_world;station=re.search(r'(?:^|_)S([123])_',n)
        if n.startswith('PROVISIONAL_'):station=None
        if n in ('Front_Centerline_Column','Rear_Centerline_Column'):
            inv=m.inverted()
            for v in o.data.vertices:
                p=m@v.co
                if p.z>1:p.z+=beam_delta
                v.co=inv@p
            changed.append(n);continue
        if station:
            i=int(station.group(1));delta=stations[i]*.010
            transform=None
            if 'Cylinder_Body' in n or 'Cylinder_Tie_Rod' in n or n.startswith('PN_Hose_'):transform=cylinder_z
            elif 'Aligned_Shaft' in n or '_Shaft_' in n:transform=stretch_z
            elif 'Cylinder_End_Cap.001' in n or 'Blue_Cylinder_Band' in n or 'Cylinder_Top_Port' in n:delta.z=head_delta
            elif 'Cylinder_End_Cap' in n or 'Cylinder_Lower_Port' in n or '_Valve_' in n or '_Mount' in n:delta.z=beam_delta
            elif '_Head_' in n or '_Flange_' in n or '_Disk_Rim_' in n:delta.z=head_delta
            inv=m.inverted()
            if transform:
                if o.type=='MESH':
                    for v in o.data.vertices:
                        p=m@v.co;p.z=transform(p.z);v.co=inv@p
                elif o.type=='CURVE':
                    for s in o.data.splines:
                        for b in s.bezier_points:
                            for attr in ('co','handle_left','handle_right'):
                                p=m@getattr(b,attr);p.z=transform(p.z);setattr(b,attr,inv@p)
            # Ratios checked against the head and ring silhouettes in photos 15 and 16.
            size=1
            if 'Head_Lower_Disk' in n or '_Disk_Rim_Hole' in n:size=.9
            elif 'Head_Raised_Step' in n:size=.737
            elif 'Head_Flange' in n or '_Flange_Bolt_' in n or 'Head_Hub' in n:size=.85
            if size!=1:
                anchor=stations[i]*.936
                for v in o.data.vertices:
                    p=m@v.co;p.x=anchor.x+(p.x-anchor.x)*size;p.y=anchor.y+(p.y-anchor.y)*size;v.co=inv@p
            if 'Underside_Mount' in n or '_Mount_Slot_' in n or '_Mount_Bolt_' in n:
                anchor=stations[i]*.936
                center=m.translation.copy()
                for v in o.data.vertices:
                    p=m@v.co
                    if '_Mount_Bolt_' in n:
                        p.x=anchor.x+(center.x-anchor.x)*1.84+(p.x-center.x)*1.25
                        p.y=anchor.y+(center.y-anchor.y)*1.69+(p.y-center.y)*1.25
                    else:
                        p.x=anchor.x+(p.x-anchor.x)*1.84;p.y=anchor.y+(p.y-anchor.y)*1.69
                    v.co=inv@p
            m.translation+=delta;o.matrix_world=root.matrix_world@m;changed.append(n)
        elif n.startswith('PROVISIONAL_') or n in ('Front_Column_Cap','Rear_Column_Cap') or n.startswith(('MD_Front_Cap','MD_Rear_Cap','PR_Front_Beam_Badge')):
            if 'Lateral_Branch' in n:
                inv=m.inverted();i=2 if 'S2' in n else 3
                xs=[(m@v.co).x for v in o.data.vertices];inner=min(abs(x) for x in xs);outer=max(abs(x) for x in xs)
                sign=-1 if i==2 else 1
                for v in o.data.vertices:
                    p=m@v.co;p.x=sign*(.0425+(abs(p.x)-inner)/(outer-inner)*(.164545*.946+.0625-.0425));p.y+=.095*.010;v.co=inv@p
            m.translation.z+=beam_delta;o.matrix_world=root.matrix_world@m;changed.append(n)
        elif n in ('PN_Hose_Approximate_Under_Beam_Link','PN_Hose_Regulator_To_Rear_Valve'):
            inv=m.inverted()
            for s in o.data.splines:
                for b in s.bezier_points:
                    for attr in ('co','handle_left','handle_right'):
                        p=m@getattr(b,attr);t=1 if 'Under_Beam' in n else max(0,min(1,(p.z-.95)/.10));p.z+=beam_delta*t;setattr(b,attr,inv@p)
            changed.append(n)
        elif n.startswith('PN_Rear_Valve_Tee_'):
            m.translation+=Vector((-.164545*.010,.095*.010,beam_delta));o.matrix_world=root.matrix_world@m;changed.append(n)
        elif n=='PN_Regulator_Adjustment_Knob' or n.startswith('PN_Knob_Grip_'):
            inv=m.inverted()
            for v in o.data.vertices:
                p=m@v.co;p.z+=.019*max(0,min(1,(p.z-.943)/.039));v.co=inv@p
            changed.append(n)
    # One shared console correction, constrained to keep both floor rails on the floor.
    A=Matrix.Diagonal((.94,.826,.9,1));A.translation.y=-.84*(1-.826)+.069
    originals={o.name:o.matrix_world.copy() for o in bpy.data.objects}
    def is_console(o):
        q=o
        while q:
            if q.name.startswith('Console_'):return True
            q=q.parent
        return False
    items=[o for o in bpy.data.objects if is_console(o)]
    items.sort(key=lambda o:0 if o.name.startswith('Console_') else 1)
    for o in items:
        old=ri@originals[o.name];new=A@old
        if not o.name.startswith('Console_'):
            # Keep knobs, buttons, latches and text dimensions; relocate them with their supporting surfaces.
            loc,rot,_=new.decompose();_,_,scale=old.decompose();new=Matrix.LocRotScale(loc,rot,scale)
        o.matrix_world=root.matrix_world@new;changed.append(o.name)
    bpy.context.view_layer.update()
    scene['REF_geometry_pass_2']=True
    scene['REF_upper_translation']=.038;scene['REF_station_radius_scale']=.946
    scene['REF_beam_translation']=.0055
    scene['REF_console_transform']='width .94, depth .826, Y +.069 about Y=-.84, height .9, floor unchanged'
    folder=os.path.dirname(os.path.abspath(__file__))
    path=os.path.join(folder,'reference_geometry_changes.json');report=json.load(open(path))
    report['refinement']={'head_z_from_original':.038,'beam_z_from_original':.0055,'cylinder_top_z_from_original':.038,'station_radius_scale_from_original':.946,'head_disk_diameter':.252,'head_step_diameter':.14003,'head_clearance':.111,'underside_mount_dimensions':[.230,.2197,.012],'regulator_knob_height_added':.019,'console_transform':scene['REF_console_transform'],'objects_changed':changed}
    json.dump(report,open(path,'w'),indent=2)

def correct_reference_roller_carriers(scene,root):
    import bpy,re
    from mathutils import Matrix,Vector
    if scene.get('REF_geometry_pass_3'):return
    ri=root.matrix_world.inverted();rot=Matrix.Rotation(math.pi/2,4,'Z');carrier_rot=Matrix.Rotation(math.radians(74),4,'Z');changed=[]
    A=Matrix.Diagonal((.94,.826,.9,1));A.translation.y=-.84*(1-.826)+.069
    for o in bpy.data.objects:
        if o.name.startswith('PR_Console_Fascia_Badge'):
            o.matrix_world=root.matrix_world@A@ri@o.matrix_world;changed.append(o.name)
    for o in bpy.data.objects:
        n=o.name;match=re.search(r'(?:^|_)S([123])_',n)
        if not match or o.type!='MESH' or not any(k in n for k in ('Roller','Bracket')):continue
        i=int(match.group(1));ring=bpy.data.objects[f'S{i}_Hollow_Ring'];pts=[ri@ring.matrix_world@Vector(v) for v in ring.bound_box]
        center=Vector(((min(p.x for p in pts)+max(p.x for p in pts))/2,(min(p.y for p in pts)+max(p.y for p in pts))/2,0))
        radial=center.normalized();tangent=Vector((-radial.y,radial.x,0));m=ri@o.matrix_world;inv=m.inverted()
        roller=re.search(r'_Roller_[12](?:_|$)',n)
        if roller:
            p=m.translation-center;r=p.dot(radial);t=p.dot(tangent)
            new=radial*.063+tangent*(.150 if t>0 else -.150)
            m.translation+=new-Vector((p.x,p.y,0))
        elif n.endswith('_Roller_Bracket'):
            for v in o.data.vertices:
                p=m@v.co-center;r=p.dot(radial);t=p.dot(tangent)
                q=center+radial*(.063+(r-.13066)*2.16)+tangent*(t*1.2);q.z=p.z;v.co=inv@q
        elif any(k in n for k in ('Adjustment_Plate','Long_Slot','Raised_Block')):
            scale=2 if 'Raised_Block' in n else 3
            for v in o.data.vertices:
                p=m@v.co-center;t=p.dot(tangent);p+=tangent*t*(scale-1);v.co=inv@(p+center)
        elif 'Bracket_Bolt' in n:
            p=m.translation-center;m.translation+=tangent*p.dot(tangent)
        turn=rot if roller else carrier_rot
        if not roller:m.translation+=radial*(-.054)+tangent*(-.04)
        o.matrix_world=root.matrix_world@Matrix.Translation(center)@turn@Matrix.Translation(-center)@m
        changed.append(n)
    bpy.context.view_layer.update();scene['REF_geometry_pass_3']=True
    scene['REF_roller_evidence']='Photos 15/16 cap positions and separate carrier edges: rollers rotated 90 degrees at radial .063 / tangent +/- .150; carrier rotated 74 degrees and translated locally (-.054,-.040). Recheck other stations in overview photos.'
    folder=os.path.dirname(os.path.abspath(__file__));path=os.path.join(folder,'reference_geometry_changes.json');report=json.load(open(path))
    report['roller_carriers']={'roller_rotation_degrees':90,'carrier_rotation_degrees':74,'carrier_radial_translation':-.054,'carrier_tangential_translation':-.040,'roller_center_radial':.063,'roller_center_tangent':.150,'supporting_photos':[1,3,4,9,10,15,16],'objects_changed':changed};json.dump(report,open(path,'w'),indent=2)

def correct_reference_review_details(scene,root):
    """Review-driven common-scene corrections. Cameras remain fixed."""
    import bpy,re
    from mathutils import Vector
    if scene.get('REF_geometry_pass_4'):return
    ri=root.matrix_world.inverted();changed=[]
    # Both side views support rearward / upward vents. Use a shared compromise,
    # not independent per-camera placements: 9/10 on right, 4/5/13 on left.
    for o in bpy.data.objects:
        match=re.match(r'CC_(Left|Right)_Grille_([12])_',o.name)
        if match:
            m=ri@o.matrix_world;m.translation+=Vector((0,.040,.085 if match[2]=='2' else .040))
            o.matrix_world=root.matrix_world@m;changed.append(o.name)
    # S1 is directly resolved by both close-ups. Fasteners slide along the slot;
    # preserve Z rather than adopting inconsistent free 3-D triangulations.
    targets=[Vector((.11738628,-.37281727,0)),Vector((.13524150,-.30702104,0))]
    for j,target in enumerate(targets):
        head=bpy.data.objects[f'MD_S1_Bracket_Bolt_{j}_Socket_Head']
        pts=[ri@head.matrix_world@Vector(v) for v in head.bound_box]
        center=Vector([(min(p[k] for p in pts)+max(p[k] for p in pts))/2 for k in range(3)])
        delta=target-center;delta.z=0
        for o in bpy.data.objects:
            if o.name.startswith(f'MD_S1_Bracket_Bolt_{j}_'):
                m=ri@o.matrix_world;m.translation+=delta;o.matrix_world=root.matrix_world@m;changed.append(o.name)
    # Keep the visible slot and support under the relocated pair; retain the
    # original support mesh and its height because the hidden section is uncertain.
    old=Vector((.12739620,-.25788200,0));new=(targets[0]+targets[1])/2
    axis=Vector((math.sin(math.radians(16)),math.cos(math.radians(16)),0))
    for name in ('MD_S1_Bracket_Long_Slot','MD_S1_Bracket_Raised_Block'):
        o=bpy.data.objects[name];m=ri@o.matrix_world;inv=m.inverted()
        for v in o.data.vertices:
            p=m@v.co;p+=axis*((p-old).dot(axis))*(-.36);v.co=inv@p
        m.translation+=new-old;o.matrix_world=root.matrix_world@m;changed.append(name)
    bpy.context.view_layer.update();scene['REF_geometry_pass_4']=True
    scene['REF_detail_review']='Grille displacement shared across sides: photos 4,5,9,10,13. Front fastener/slot placement: fixed cameras 15,16; support shape remains provisional.'
    path=os.path.join(os.path.dirname(os.path.abspath(__file__)),'reference_geometry_changes.json')
    report=json.load(open(path));report['review_details']={'grille_delta_y':.040,'upper_grille_delta_z':.085,'lower_grille_delta_z':.040,'front_bolt_xy':[list(p)[:2] for p in targets],'slot_support_axial_scale':.64,'support_shape_uncertain':True,'objects_changed':changed}
    json.dump(report,open(path,'w'),indent=2)

def focused_working_corrections(scene,root):
    """One circular plate and repeated mechanical assemblies; never per-view edits."""
    import bpy,re
    from mathutils import Vector,Matrix
    if scene.get('REF_focused_working_pass'):return
    ri=root.matrix_world.inverted()
    def relevant(n):
        return bool(re.search(r'(?:^|_)S[123]_',n)) or n.startswith(('PROVISIONAL_','MD_Front_Cap','MD_Rear_Cap')) or n in ('Front_Centerline_Column','Rear_Centerline_Column','Front_Column_Cap','Rear_Column_Cap','PN_Hose_Approximate_Under_Beam_Link','PN_Hose_Regulator_To_Rear_Valve') or n.startswith('PN_Rear_Valve_Tee_')
    # The resumed file was audited against the pre-correction inventory. Restore
    # documented working geometry only; keep unrelated saved manual details intact.
    protected={}
    for o in bpy.data.objects:
        if o.type not in {'MESH','CURVE','FONT'} or relevant(o.name):continue
        protected[o.name]=(o.matrix_world.copy(),[v.co.copy() for v in o.data.vertices] if o.type=='MESH' else None)
    if not scene.get('REF_geometry_pass_1'):
        apply_reference_corrections(scene,root);refine_reference_corrections(scene,root)
        correct_reference_roller_carriers(scene,root);correct_reference_review_details(scene,root)
        for n,(m,vs) in protected.items():
            o=bpy.data.objects[n]
            if vs:
                for v,p in zip(o.data.vertices,vs):v.co=p
        # Restore parent transforms first, then children.
        def depth(o):return 0 if o.parent is None else 1+depth(o.parent)
        for n in sorted(protected,key=lambda n:depth(bpy.data.objects[n])):bpy.data.objects[n].matrix_world=protected[n][0]
        scene['REF_grille_mount_review']=True # retained current unrelated state, deliberately not restored
        scene['REF_hose_clearance_review']=True
        if 'REF_console_transform' in scene:del scene['REF_console_transform']
        scene['REF_restoration_scope']='Working assembly and connected supports only. Current saved console/cabinet/regulator retained; prior gallery was not current saved state.'
    bpy.context.view_layer.update()
    metal=bpy.data.objects['S1_Roller_Bracket'].data.materials[0]
    silver=bpy.data.objects['MD_S1_Bracket_Bolt_0_Washer'].data.materials[0]
    coll=bpy.data.collections['Mechanical_Details'];cutters=bpy.data.collections['Mechanical_Cutters']
    changed=[]
    def mesh(name,verts,faces,material=metal,bevel=0):
        o=bpy.data.objects.get(name)
        if o is None:
            o=bpy.data.objects.new(name,bpy.data.meshes.new(name));coll.objects.link(o);o.parent=root;o.matrix_parent_inverse=Matrix.Identity(4)
        o.data.clear_geometry();o.data.from_pydata(verts,[],faces);o.data.update();o.matrix_world=root.matrix_world.copy()
        o.data.materials.clear();o.data.materials.append(material)
        # Keep object identity and boolean relations; reset only this rebuilt part's bevel.
        for mod in list(o.modifiers):
            if mod.type in {'BEVEL','WEIGHTED_NORMAL'}:o.modifiers.remove(mod)
        if bevel:
            m=o.modifiers.new('Focused edge finish','BEVEL');m.width=bevel;m.segments=3
            o.modifiers.new('Focused normals','WEIGHTED_NORMAL')
        changed.append(name);return o
    def prism(name,poly,z0,z1,bevel=.001):
        poly=list(poly)
        if sum(poly[k][0]*poly[(k+1)%len(poly)][1]-poly[(k+1)%len(poly)][0]*poly[k][1] for k in range(len(poly)))<0:poly.reverse()
        N=len(poly);v=[(x,y,z) for z in (z0,z1) for x,y in poly]
        faces=[tuple(reversed(range(N))),tuple(range(N,N*2))]+[(k,(k+1)%N,(k+1)%N+N,k+N) for k in range(N)]
        return mesh(name,v,faces,bevel=bevel)
    def cyl(name,c,r,z0,z1,N=64,material=metal):
        p=[(c[0]+r*math.cos(2*math.pi*k/N),c[1]+r*math.sin(2*math.pi*k/N)) for k in range(N)]
        o=prism(name,p,z0,z1,.0004);o.data.materials.clear();o.data.materials.append(material);return o
    def cut(target,cutter):
        for c in list(cutter.users_collection):c.objects.unlink(cutter)
        cutters.objects.link(cutter);cutter.hide_render=True;cutter.hide_set(True);cutter.display_type='WIRE'
        m=next((m for m in target.modifiers if m.type=='BOOLEAN' and m.object==cutter),None)
        if m is None:m=target.modifiers.new('Focused '+cutter.name,'BOOLEAN')
        m.operation='DIFFERENCE';m.solver='EXACT';m.object=cutter
        # Boolean before finish bevel.
        bpy.context.view_layer.objects.active=target
        while list(target.modifiers).index(m)>0:bpy.ops.object.modifier_move_up(modifier=m.name)
    def capsule(name,a,b,r,z0,z1):
        a=Vector(a);b=Vector(b);ang=math.atan2(b.y-a.y,b.x-a.x);poly=[]
        for c,start in [(b,ang-math.pi/2),(a,ang+math.pi/2)]:
            for j in range(17):
                t=start+math.pi*j/16;poly.append((c.x+r*math.cos(t),c.y+r*math.sin(t)))
        return prism(name,poly,z0,z1,0)
    # Conservative common circular radius: all three rings remain within the rim.
    plate=bpy.data.objects['Circular_Working_Plate'];m=ri@plate.matrix_world;inv=m.inverted()
    for v in plate.data.vertices:
        p=m@v.co;p.x*=.330/.365;p.y*=.330/.365;v.co=inv@p
    changed.append(plate.name)
    # Source front carrier: chamfered external outline with a circular ring clearance.
    base_center=Vector((0,-.17974,0));poly=[(.1604,-.4324),(.1071,-.4137),(.042,-.352),(.040,-.014),(.100,.004),(.1542,-.1356),(.2345,-.1686),(.2532,-.1896)]
    a=Vector((.15813,-.40796,0));b=Vector((.19187,-.29838,0));axis=(b-a).normalized();normal=Vector((axis.y,-axis.x,0))
    station_centers=[Vector((0,-.17974,0)),Vector((-.15565957,.08987,0)),Vector((.15565957,.08987,0))]
    for i,c in enumerate(station_centers,1):
        angle=math.atan2(c.y,c.x)+math.pi/2;rot=Matrix.Rotation(angle,3,'Z')
        def p(v):return c+rot@(Vector(v)-base_center)
        outline=[p((x,y,0))[:2] for x,y in poly]
        main=prism(f'S{i}_Roller_Bracket',outline,.784,.798,.002)
        cut(main,cyl(f'MD_S{i}_Carrier_Ring_Clearance',c,.1458,.775,.805))
        # Reuse extension as the real slotted front strip, continuous with the carrier.
        mid=(a+b)/2;L=.153;W=.035
        corners=[mid+axis*u+normal*v for u,v in [(-L/2,-W/2),(L/2,-W/2),(L/2,W/2),(-L/2,W/2)]]
        ext=prism(f'MD_S{i}_Bracket_Adjustment_Plate',[p(v)[:2] for v in corners],.784,.798,.0015)
        cut(main,prism(f'MD_S{i}_Carrier_Strip_Clearance',[p(v)[:2] for v in corners],.779,.804,0))
        slot=capsule(f'MD_S{i}_Bracket_Long_Slot',p(a)[:2],p(b)[:2],.0045,.779,.804)
        cut(ext,slot);cut(main,slot)
        # Block base on the tabletop; its exposed ledge carries two counterbores.
        bc=Vector((.1701,-.352,0));L=.108;W=.046
        corners=[bc+axis*u+normal*v for u,v in [(-L/2,-W/2),(L/2,-W/2),(L/2,W/2),(-L/2,W/2)]]
        block=prism(f'MD_S{i}_Bracket_Raised_Block',[p(v)[:2] for v in corners],.735,.784,.001)
        for j,t in enumerate((.25,.75)):
            q=p(a+(b-a)*t)
            washer=cyl(f'MD_S{i}_Bracket_Bolt_{j}_Washer',q,.0135,.798,.800,material=metal)
            head=cyl(f'MD_S{i}_Bracket_Bolt_{j}_Socket_Head',q,.0085,.800,.812,material=metal)
            recess=cyl(f'MD_S{i}_Bracket_Bolt_{j}_Hex_Recess',q,.004,.806,.815,6)
            cut(head,recess);cut(washer,cyl(f'MD_S{i}_Bracket_Bolt_{j}_Washer_Bore',q,.005,.797,.802))
            q=p(bc+axis*(-.033 if j==0 else .033)+normal*.014)
            cut(block,cyl(f'MD_S{i}_Support_Through_Hole_{j}',q,.0055,.732,.789))
            cut(block,cyl(f'MD_S{i}_Support_Counterbore_{j}',q,.0105,.778,.789))
        # Contact rollers share the ring tangent and rest on the carrier plane.
        for j,off in [(1,-.150),(2,.150)]:
            q=p((.063,-.17974+off,0))
            cyl(f'S{i}_Roller_{j}',q,.0175,.798,.821)
            cyl(f'MD_S{i}_Roller_{j}_Neck',q,.0145,.821,.8228)
            cyl(f'MD_S{i}_Roller_{j}_Top_Cap',q,.0175,.8228,.827,material=silver)
        # Replace the overcompressed visible shaft fittings without moving heads.
        hub=bpy.data.objects[f'S{i}_Head_Hub'];hm=ri@hub.matrix_world;hinv=hm.inverted()
        zs=[(hm@v.co).z for v in hub.data.vertices];lo=min(zs);hi=max(zs)
        for v in hub.data.vertices:
            q=hm@v.co;q.z=lo+(q.z-lo)*((1.030-lo)/(hi-lo));v.co=hinv@q
        cyl(f'S{i}_Aligned_Shaft',c,.0105,1.030,1.0485,material=silver)
        cyl(f'MD_S{i}_Shaft_Hex_Coupling',c,.014,1.030,1.0405,6,material=silver)
        cyl(f'MD_S{i}_Shaft_Upper_Collar',c,.029,1.0405,1.0485,material=silver)
        # Turned grooves: move the existing cutters, keeping the ring OD unchanged.
        for j,z in enumerate((.791,.802)):
            o=bpy.data.objects[f'MD_S{i}_Ring_Groove_{j}'];om=ri@o.matrix_world
            pts=[om@Vector(v) for v in o.bound_box];center=Vector([(min(q[k] for q in pts)+max(q[k] for q in pts))/2 for k in range(3)])
            inv=om.inverted()
            for v in o.data.vertices:
                q=om@v.co;rho=math.hypot(q.x-center.x,q.y-center.y);newrho=.145+(rho-.145)*.60
                q.x=center.x+(q.x-center.x)*newrho/rho;q.y=center.y+(q.y-center.y)*newrho/rho;q.z=z+(q.z-center.z)*.60;v.co=inv@q
        # Clear observed S3 sectors are not evenly spaced. Other obscured sectors
        # retain prior cuts rather than inventing a repeating slot distribution.
        if i==3:
            for j,degrees in enumerate((-50.42,-8.93)):
                old=bpy.data.objects[f'MD_S{i}_Ring_Vertical_Slot_{j}'];ang=math.radians(degrees);rad=Vector((math.cos(ang),math.sin(ang),0));tan=Vector((-rad.y,rad.x,0));mid=c+rad*.137
                corners=[mid+rad*u+tan*v for u,v in [(-.013,-.0015),(.013,-.0015),(.013,.0015),(-.013,.0015)]]
                prism(old.name,[v[:2] for v in corners],.743,.793,.00035)
    bpy.context.view_layer.update()
    scene['REF_focused_working_pass']=True
    scene['REF_focused_camera_policy']='All sixteen camera matrices/lenses unchanged from previous comparison JSON; no per-view geometry.'
    scene['REF_focused_plate_radius']=.330
    folder=os.path.dirname(os.path.abspath(__file__))
    json.dump({'plate_radius':.330,'plate_center':[0,0],'plate_z':[.735,.747],'carrier_z':[.784,.798],'support_z':[.735,.784],'support_footprint':[.108,.046],'support_counterbore_diameter':.021,'slot_radius':.0045,'bolt_head_diameter':.017,'bolt_head_height':.012,'s3_visible_slot_angles':[-50.42,-8.93],'unchanged_camera_json':True,'restoration_scope':scene.get('REF_restoration_scope','Prior corrected working geometry retained'),'objects_changed':changed},open(os.path.join(folder,'focused_geometry_changes.json'),'w'),indent=2)

def refine_focused_seating(scene,root):
    import bpy
    from mathutils import Matrix,Vector
    if not scene.get('REF_focused_working_pass') or scene.get('REF_focused_seating_review'):return
    ri=root.matrix_world.inverted();base=Vector((0,-.17974,0))
    camera=Vector((.508284,-.494507,.956213));ratio=(.785-camera.z)/(.798-camera.z)
    centers=[Vector((0,-.17974,0)),Vector((-.15565957,.08987,0)),Vector((.15565957,.08987,0))]
    cutters=bpy.data.collections['Mechanical_Cutters']
    def boolean(target,cutter,operation='DIFFERENCE'):
        cutter.hide_render=True;cutter.hide_set(True);cutter.display_type='WIRE'
        mod=target.modifiers.new('Focused seating '+cutter.name,'BOOLEAN');mod.object=cutter;mod.operation=operation;mod.solver='EXACT'
        bpy.context.view_layer.objects.active=target
        bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0)
    for i,c in enumerate(centers,1):
        rot=Matrix.Rotation(math.atan2(c.y,c.x)+math.pi/2,3,'Z');invrot=rot.transposed()
        def rotate(p):return c+rot@(Vector(p)-base)
        # Lower the carrier plane while retaining the observed top contour.
        for o in list(bpy.data.objects):
            n=o.name
            if not (n==f'S{i}_Roller_Bracket' or n==f'MD_S{i}_Carrier_Strip_Clearance' or (n.startswith(f'MD_S{i}_Bracket_') and 'Raised_Block' not in n)):continue
            if o.type!='MESH':continue
            m=ri@o.matrix_world;inv=m.inverted()
            for v in o.data.vertices:
                q=m@v.co;p=base+invrot@(q-c);p.x=camera.x+(p.x-camera.x)*ratio;p.y=camera.y+(p.y-camera.y)*ratio;p.z-=.013
                v.co=inv@rotate(p)
        main=bpy.data.objects[f'S{i}_Roller_Bracket'];block=bpy.data.objects[f'MD_S{i}_Bracket_Raised_Block']
        # Recess the rear of the block below the carrier, leaving the tall exposed
        # front ledge and its mounting counterbores at the photographed elevation.
        for suffix,source in [('Carrier',main),('Strip',bpy.data.objects[f'MD_S{i}_Bracket_Adjustment_Plate'])]:
            name=f'MD_S{i}_Support_{suffix}_Rebate';o=bpy.data.objects.new(name,source.data.copy());cutters.objects.link(o);o.parent=root;o.matrix_world=root.matrix_world.copy()
            for v in o.data.vertices:v.co.z=.771 if v.co.z<.780 else .805
            boolean(block,o)
        # Six tangent rollers, with the inter-ring rollers outside both rings.
        # The old positions slightly intersected their neighbouring rings.
        near=Vector((.063,-.150,0));near*=.1625/near.length
        for j,local in [(1,base+near),(2,Vector((.1183,-.0683,0)))]:
            target=rotate(local)
            for name,z0,z1 in [(f'S{i}_Roller_{j}',.785,.809),(f'MD_S{i}_Roller_{j}_Neck',.809,.8108),(f'MD_S{i}_Roller_{j}_Top_Cap',.8108,.815)]:
                o=bpy.data.objects[name];m=ri@o.matrix_world;inv=m.inverted();pts=[m@v.co for v in o.data.vertices];center=Vector([(min(p[k] for p in pts)+max(p[k] for p in pts))/2 for k in range(3)]);lo=min(p.z for p in pts);hi=max(p.z for p in pts)
                for v in o.data.vertices:
                    q=m@v.co;q.x+=target.x-center.x;q.y+=target.y-center.y;q.z=z0+(q.z-lo)*(z1-z0)/(hi-lo);v.co=inv@q
            # Small seating pad unites with the carrier; ring-clearance booleans
            # below keep the pad out of all ring envelopes.
            N=48;verts=[(target.x+.022*math.cos(2*math.pi*k/N),target.y+.022*math.sin(2*math.pi*k/N),z) for z in (.771,.785) for k in range(N)]
            faces=[tuple(reversed(range(N))),tuple(range(N,2*N))]+[(k,(k+1)%N,(k+1)%N+N,k+N) for k in range(N)]
            data=bpy.data.meshes.new(f'MD_S{i}_Roller_{j}_Seat');data.from_pydata(verts,[],faces)
            o=bpy.data.objects.new(data.name,data);cutters.objects.link(o);o.parent=root;o.matrix_world=root.matrix_world.copy();boolean(main,o,'UNION')
        for k in range(1,4):
            cutter=bpy.data.objects[f'MD_S{k}_Carrier_Ring_Clearance']
            # Existing clearance cut must run after seating-pad unions.
            for target in [main,bpy.data.objects[f'MD_S{i}_Bracket_Adjustment_Plate']]:
                old=next((m for m in target.modifiers if m.type=='BOOLEAN' and m.object==cutter),None)
                if old:target.modifiers.remove(old)
                mod=target.modifiers.new('Ring envelope '+str(k),'BOOLEAN');mod.object=cutter;mod.operation='DIFFERENCE';mod.solver='EXACT'
                bpy.context.view_layer.objects.active=target
                idx=next((j for j,m in enumerate(target.modifiers) if m.type in {'BEVEL','WEIGHTED_NORMAL'}),len(target.modifiers)-1)
                bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=idx)
    bpy.context.view_layer.update();scene['REF_focused_seating_review']=True
    path=os.path.join(os.path.dirname(os.path.abspath(__file__)),'focused_geometry_changes.json');j=json.load(open(path))
    j.update({'carrier_z':[.771,.785],'bolt_head_z':[.787,.799],'support_front_ledge_z':.784,'support_rear_seat_z':.771,'roller_body_z':[.785,.809],'roller_contact':'outer tangency .1625 from ring center; inter-ring roller moved to external circle intersection','seating_review':'Contour at fixed camera 16 retained; independently checked in 15 and overviews.'})
    json.dump(j,open(path,'w'),indent=2)

def finish_front_support(scene,root):
    import bpy
    from mathutils import Vector
    if scene.get('REF_front_support_finish'):return
    ri=root.matrix_world.inverted();axis=Vector((.03374,.10958,0)).normalized();normal=Vector((axis.y,-axis.x,0));center=Vector((.1701,-.352,0))
    block=bpy.data.objects['MD_S1_Bracket_Raised_Block'];m=ri@block.matrix_world;inv=m.inverted()
    for v in block.data.vertices:
        p=m@v.co;p+=axis*((p-center).dot(axis))*(.100/.108-1);v.co=inv@p
    for j in range(2):
        for kind in ['Through_Hole','Counterbore']:
            o=bpy.data.objects[f'MD_S1_Support_{kind}_{j}'];m=ri@o.matrix_world;inv=m.inverted();pts=[m@v.co for v in o.data.vertices];c=Vector([(min(p[k] for p in pts)+max(p[k] for p in pts))/2 for k in range(3)])
            for v in o.data.vertices:
                p=m@v.co
                if kind=='Counterbore':p.x=c.x+(p.x-c.x)*(.009/.0105);p.y=c.y+(p.y-c.y)*(.009/.0105)
                p-=normal*.005;v.co=inv@p
    main=bpy.data.objects['S1_Roller_Bracket'];ext=bpy.data.objects['MD_S1_Bracket_Adjustment_Plate']
    for mod in list(main.modifiers):
        if mod.type=='BOOLEAN' and mod.object and mod.object.name=='MD_S1_Carrier_Strip_Clearance':main.modifiers.remove(mod)
    mod=main.modifiers.new('Continuous slotted carrier','BOOLEAN');mod.object=ext;mod.operation='UNION';mod.solver='EXACT'
    bpy.context.view_layer.objects.active=main;bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0)
    ext.hide_render=True;ext.hide_set(True)
    bpy.context.view_layer.update();scene['REF_front_support_finish']=True
    scene['REF_front_support_note']='Front block length .100, height .049 with recessed rear seat. Closed counterbores diameter .018; continuous carrier .014 thick. Plate/cameras/other assemblies retained at narrowed-scope state.'

def reference_comparison_pass():
    """Explicit reference workflow; does not regenerate or reset existing machine details."""
    import bpy
    from mathutils import Matrix, Vector
    folder=os.path.dirname(os.path.abspath(__file__))
    working=os.path.join(folder,'lapping_machine_blockout.blend')
    if os.path.normcase(bpy.data.filepath)!=os.path.normcase(working):
        raise RuntimeError('Reference pass must load the single working file.')
    scene=bpy.context.scene
    root=bpy.data.objects['LM_ROOT_Move_Complete_Machine']
    if '--focused-working-pass' in sys.argv:focused_working_corrections(scene,root)
    refine_focused_seating(scene,root)
    if '--front-support-pass' in sys.argv:finish_front_support(scene,root)
    if '--apply-reference-corrections' in sys.argv:
        apply_reference_corrections(scene,root)
        refine_reference_corrections(scene,root)
        correct_reference_roller_carriers(scene,root)
        correct_reference_review_details(scene,root)
    if scene.get('REF_geometry_pass_4') and not scene.get('REF_grille_mount_review'):
        # Upper grilles straddle the console hood side. Moving them up on the
        # recessed lower-cabinet plane occludes them; bring their faces onto the
        # hood exterior and extend their frame backs to the original mounting plane.
        for o in bpy.data.objects:
            if o.name.startswith(('CC_Left_Grille_2_','CC_Right_Grille_2_')):
                sign=-1 if '_Left_' in o.name else 1
                m=root.matrix_world.inverted()@o.matrix_world;m.translation.x+=sign*.018
                o.matrix_world=root.matrix_world@m
                if o.name.endswith('_Frame'):
                    inv=m.inverted();xs=[(m@v.co).x for v in o.data.vertices]
                    back=max(xs) if sign<0 else min(xs)
                    for v in o.data.vertices:
                        p=m@v.co
                        if abs(p.x-back)<.00001:p.x-=sign*.018
                        v.co=inv@p
        bpy.context.view_layer.update();scene['REF_grille_mount_review']=True
        path=os.path.join(folder,'reference_geometry_changes.json');report=json.load(open(path))
        report['review_details']['upper_grille_outward_offset']=.018
        json.dump(report,open(path,'w'),indent=2)
    if scene.get('REF_geometry_pass_4') and not scene.get('REF_hose_clearance_review'):
        ri=root.matrix_world.inverted()
        for name in ('PN_Hose_S1_Lower_Loop','PN_Hose_Approximate_Under_Beam_Link'):
            o=bpy.data.objects[name];m=ri@o.matrix_world;inv=m.inverted()
            shifts=([0,-.012,-.025,-.025,-.025,-.025,-.012,-.005,0,0]
                    if 'S1' in name else [0,-.020,-.027,-.027,-.015,0,0,0,0,.015,.027,.027,.020,.010,.005,0])
            for p,dx in zip(o.data.splines[0].bezier_points,shifts):
                for attr in ('co','handle_left','handle_right'):
                    q=m@getattr(p,attr);q.x+=dx;setattr(p,attr,inv@q)
            if 'Under_Beam' in name:o.data.bevel_depth=.0025
        bpy.context.view_layer.update();scene['REF_hose_clearance_review']=True
        path=os.path.join(folder,'reference_geometry_changes.json');report=json.load(open(path))
        report['hose_clearance']={'note':'S1 loop and approximate cross-link bent outside enlarged plates, endpoints retained; cross-link diameter .005. Exact hidden routing remains uncertain.','objects':['PN_Hose_S1_Lower_Loop','PN_Hose_Approximate_Under_Beam_Link']}
        json.dump(report,open(path,'w'),indent=2)
    fits=json.load(open(os.path.join(folder,'reference_cameras.json')))
    coll=bpy.data.collections.get('Reference_Cameras')
    if coll is None:
        coll=bpy.data.collections.new('Reference_Cameras');scene.collection.children.link(coll)
    for ns,fit in fits.items():
        name=f'REF_{int(ns):02d}'
        cam=bpy.data.objects.get(name)
        if cam is None:
            cam=bpy.data.objects.new(name,bpy.data.cameras.new(name));coll.objects.link(cam)
        rot=Matrix(fit['world_to_cv']).transposed()@Matrix.Diagonal((1,-1,-1))
        m=rot.to_4x4();m.translation=Vector(fit['camera_location'])
        cam.matrix_world=root.matrix_world@m
        w,h=fit['preview_size']
        cam.data.type='PERSP';cam.data.sensor_fit='HORIZONTAL';cam.data.sensor_width=36
        cam.data.lens=fit['focal_preview_px']*36/w
        cam.data.shift_x=0;cam.data.shift_y=0;cam.data.clip_start=.002;cam.data.clip_end=200
        cam['reference_photo']=f'{ns}.jpeg';cam['reference_width']=3120 if int(ns)<15 else 4160
        cam['reference_height']=4160 if int(ns)<15 else 3120
        cam['landmark_rms_preview_px']=fit['rms_preview_px']
        cam['alignment_note']='Manual structural correspondences; camera-only fit. Residual is not fidelity certification.'
        cam.hide_set(True)
    scene['REF_acceptance']='Visual agreement across photographs 1-16; reconstruction remains under review.'
    text=bpy.data.texts.get('LM_GENERATION_SCRIPT') or bpy.data.texts.new('LM_GENERATION_SCRIPT')
    text.clear();text.write(open(__file__,encoding='utf-8').read())
    previous=bpy.context.preferences.filepaths.save_version;bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=working,check_existing=False)
    bpy.context.preferences.filepaths.save_version=previous
    if '--no-render' in sys.argv:return
    def geometry_digest():
        digest=hashlib.sha256()
        for o in sorted(bpy.data.objects,key=lambda ob:ob.name):
            if o.type not in {'MESH','CURVE','FONT'}:continue
            digest.update(o.name.encode());digest.update(str([list(r) for r in o.matrix_world]).encode())
            if o.type=='MESH':digest.update(str([tuple(v.co) for v in o.data.vertices]).encode())
            elif o.type=='CURVE':
                digest.update(str([[(tuple(p.co),tuple(p.handle_left),tuple(p.handle_right)) for p in s.bezier_points] for s in o.data.splines]).encode())
        return digest.hexdigest()
    common_geometry=geometry_digest()
    focused_preview='--focused-preview' in sys.argv
    draft='--reference-draft' in sys.argv or focused_preview
    out=os.path.join(folder,'reference_comparisons');os.makedirs(out,exist_ok=True)
    scene.render.engine='CYCLES';scene.cycles.samples=8 if draft else 24;scene.cycles.use_denoising=True
    try:
        cp=bpy.context.preferences.addons['cycles'].preferences;cp.compute_device_type='CUDA';cp.get_devices()
        for d in cp.devices:d.use=d.type=='CUDA'
        scene.cycles.device='GPU'
    except Exception:scene.cycles.device='CPU'
    floor=bpy.data.objects.get('Studio_Floor')
    if floor:floor.hide_render=True
    scene.render.film_transparent=True
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
    scene.render.resolution_percentage=100
    selected={'15','16'} if focused_preview else None
    for arg in sys.argv:
        if arg.startswith('--reference-views='):selected=set(arg.split('=')[1].split(','))
    manifest_path=os.path.join(out,'front_preview_manifest.json' if focused_preview else 'render_manifest.json')
    manifest=json.load(open(manifest_path)) if os.path.exists(manifest_path) else {}
    for ns,fit in fits.items():
        if selected and ns not in selected:continue
        scene.camera=bpy.data.objects[f'REF_{int(ns):02d}']
        scene.render.resolution_x=(390 if draft else 936) if int(ns)<15 else (520 if draft else 1248)
        scene.render.resolution_y=(520 if draft else 1248) if int(ns)<15 else (390 if draft else 936)
        scene.render.filepath=os.path.join(out,('front_preview_' if focused_preview else ('baseline_' if draft else ''))+f'REF_{int(ns):02d}.png')
        bpy.ops.render.render(write_still=True)
        assert geometry_digest()==common_geometry,'Geometry changed between reference renders'
        source=os.path.join(folder,'..',f'{ns}.jpeg')
        manifest[ns]={'camera':scene.camera.name,'source':f'{ns}.jpeg','source_sha256':hashlib.sha256(open(source,'rb').read()).hexdigest(),'geometry_sha256':common_geometry,'blend_sha256':hashlib.sha256(open(working,'rb').read()).hexdigest(),'camera_matrix':[list(row) for row in scene.camera.matrix_world],'lens_mm':scene.camera.data.lens,'resolution':[scene.render.resolution_x,scene.render.resolution_y],'transparent_background':True,'image_sha256':hashlib.sha256(open(scene.render.filepath,'rb').read()).hexdigest()}
        json.dump(manifest,open(manifest_path,'w'),indent=2)
        print('REFERENCE_RENDERED',ns,flush=True)
    # Render state is deliberately temporary; saved scene retains presentation state and all reference cameras.

def small_flange_gap_pass():
    """Bounded, idempotent clearance correction from ll1/ll2/ll3 close-ups."""
    import bpy
    from mathutils import Vector
    folder=os.path.dirname(os.path.abspath(__file__))
    working=os.path.join(folder,'lapping_machine_blockout.blend')
    assert os.path.normcase(os.path.abspath(bpy.data.filepath))==os.path.normcase(working)
    scene=bpy.context.scene;root=bpy.data.objects['LM_ROOT_Move_Complete_Machine']
    ri=root.matrix_world.inverted()
    def bounds(o):
        p=[ri@o.matrix_world@Vector(v) for v in o.bound_box]
        return Vector([min(v[k] for v in p) for k in range(3)]),Vector([max(v[k] for v in p) for k in range(3)])
    def snapshot(o):
        d={'matrix':[list(r) for r in o.matrix_world],'hide_render':o.hide_render}
        if o.type=='MESH':d['vertices']=[list(v.co) for v in o.data.vertices]
        if o.type=='CAMERA':d['camera']=[o.data.lens,o.data.shift_x,o.data.shift_y,o.data.sensor_width]
        return hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
    allowed={f'S{i}_Head_{part}' for i in (1,2,3) for part in ('Flange','Hub')}
    allowed.update(o.name for o in bpy.data.objects if any(o.name.startswith(f'MD_S{i}_Flange_Bolt_') for i in (1,2,3)))
    protected={o.name:snapshot(o) for o in bpy.data.objects if o.name not in allowed}
    if not scene.get('REF_small_flange_clearance'):
        for i in (1,2,3):
            flange=bpy.data.objects[f'S{i}_Head_Flange'];hub=bpy.data.objects[f'S{i}_Head_Hub']
            fl,fh=bounds(flange);hl,hh=bounds(hub)
            sl,sh=bounds(bpy.data.objects[f'S{i}_Head_Raised_Step'])
            assert abs(fl.z-sh.z)<.0001,'Unexpected existing clearance; inspect before applying'
            gap=(fh.z-fl.z)*.5
            m=ri@flange.matrix_world;m.translation.z+=gap;flange.matrix_world=root.matrix_world@m
            # Preserve shaft seat and total head envelope; only hub lower boundary rises.
            m=ri@hub.matrix_world;inv=m.inverted()
            for v in hub.data.vertices:
                p=m@v.co;p.z=hl.z+gap+(p.z-hl.z)*(hh.z-hl.z-gap)/(hh.z-hl.z);v.co=inv@p
            hub.data.update()
            def neck(name,x,y,r):
                bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=r,depth=gap+.0004)
                o=bpy.context.object;o.name=name;o.parent=root;o.location=(x,y,sh.z+gap/2)
                o.data.materials.append(hub.data.materials[0])
                for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
                return o
            center=(fl+fh)/2
            neck(f'MD_S{i}_Flange_Central_Neck',center.x,center.y,(hh.x-hl.x)*.35)
            # Keep the existing peripheral bolt pattern; expose only their short shanks.
            # No additional spring, bearing, or concealed linkage is inferred.
            for j in range(4):
                w=bpy.data.objects[f'MD_S{i}_Flange_Bolt_{j}_Washer'];wl,wh=bounds(w);wc=(wl+wh)/2
                neck(f'MD_S{i}_Flange_Bolt_{j}_Exposed_Shank',wc.x,wc.y,.0022)
                for suffix in ('Washer','Socket_Head','Hex_Recess'):
                    o=bpy.data.objects[f'MD_S{i}_Flange_Bolt_{j}_{suffix}'];m=ri@o.matrix_world;m.translation.z+=gap;o.matrix_world=root.matrix_world@m
            flange['reference_gap']=gap
        scene['REF_small_flange_clearance']=True
        scene['REF_small_flange_evidence']='ll1/ll2/ll3: clearance 0.5 flange thickness; central neck and existing bolt shanks only. Lower disks, stages, shafts, station centers unchanged.'
    bpy.context.view_layer.update()
    assert all(snapshot(bpy.data.objects[n])==v for n,v in protected.items()),'Out-of-scope geometry or camera changed'
    records=[]
    for i in (1,2,3):
        fl,fh=bounds(bpy.data.objects[f'S{i}_Head_Flange']);sl,sh=bounds(bpy.data.objects[f'S{i}_Head_Raised_Step'])
        assert abs((fl.z-sh.z)/(fh.z-fl.z)-.5)<.001
        records.append({'station':i,'gap':fl.z-sh.z,'flange_thickness':fh.z-fl.z})
    # Persist fingerprints so reopening can independently verify every untouched object.
    if not os.path.exists(os.path.join(folder,'flange_gap_verification.json')):
        json.dump({'heads':records,'protected':protected},open(os.path.join(folder,'flange_gap_verification.json'),'w'),indent=2)
    cam=bpy.data.objects.get('Flange_Gap_Preview')
    if not cam:
        cam=bpy.data.objects.new('Flange_Gap_Preview',bpy.data.cameras.new('Flange_Gap_Preview'));scene.collection.objects.link(cam)
    fl,fh=bounds(bpy.data.objects['S1_Head_Flange']);center=(fl+fh)/2
    target=root.matrix_world@Vector((center.x,center.y,center.z+.005))
    cam.location=root.matrix_world@Vector((center.x+.11,center.y-.54,center.z-.018))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=85
    txt=bpy.data.texts.get('LM_GENERATION_SCRIPT') or bpy.data.texts.new('LM_GENERATION_SCRIPT');txt.clear();txt.write(open(__file__,encoding='utf-8-sig').read())
    versions=bpy.context.preferences.filepaths.save_version;bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=working);bpy.context.preferences.filepaths.save_version=versions
    if '--no-render' not in sys.argv:
        scene.camera=cam;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
        scene.render.resolution_x=640;scene.render.resolution_y=480;scene.render.resolution_percentage=100
        scene.render.image_settings.file_format='PNG';scene.render.filepath=os.path.join(folder,'flange_gap_preview.png')
        bpy.ops.render.render(write_still=True)
    print('FLANGE_GAP_VERIFIED',records,flush=True)

def flange_stage_screw_pass():
    """Seat existing peripheral screws outside the raised flange, without adding screws."""
    import bpy
    from mathutils import Vector
    folder=os.path.dirname(os.path.abspath(__file__))
    working=os.path.join(folder,'lapping_machine_blockout.blend')
    assert os.path.normcase(os.path.abspath(bpy.data.filepath))==os.path.normcase(working)
    scene=bpy.context.scene;root=bpy.data.objects['LM_ROOT_Move_Complete_Machine'];ri=root.matrix_world.inverted()
    assert scene.get('REF_small_flange_clearance'),'Inspect the saved flange gap before screw correction'
    def bounds(o):
        p=[ri@o.matrix_world@Vector(v) for v in o.bound_box]
        return Vector([min(v[k] for v in p) for k in range(3)]),Vector([max(v[k] for v in p) for k in range(3)])
    def snapshot(o):
        d={'matrix':[list(r) for r in o.matrix_world],'hide_render':o.hide_render}
        if o.type=='MESH':d['vertices']=[list(v.co) for v in o.data.vertices]
        if o.type=='CAMERA':d['camera']=[o.data.lens,o.data.shift_x,o.data.shift_y,o.data.sensor_width]
        return hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
    screws={o.name for o in bpy.data.objects if any(o.name.startswith(f'MD_S{i}_Flange_Bolt_') for i in (1,2,3))}
    protected={o.name:snapshot(o) for o in bpy.data.objects if o.name not in screws}
    if not scene.get('REF_flange_screws_on_stage'):
        for i in (1,2,3):
            fl,fh=bounds(bpy.data.objects[f'S{i}_Head_Flange']);sl,sh=bounds(bpy.data.objects[f'S{i}_Head_Raised_Step'])
            c=(fl+fh)/2;fr=(fh.x-fl.x)/2
            for j in range(4):
                prefix=f'MD_S{i}_Flange_Bolt_{j}'
                w=bpy.data.objects[prefix+'_Washer'];wl,wh=bounds(w);old=(wl+wh)/2;old.z=wl.z
                radial=Vector((old.x-c.x,old.y-c.y,0)).normalized()
                # Existing four fasteners only. Reference heads are outside the flange;
                # leave 1 mm model-space clearance from the washer to the flange rim.
                radius=fr+(wh.x-wl.x)*.5*1.25+.001
                new=Vector((c.x,c.y,sh.z))+radial*radius
                for suffix in ('Washer','Socket_Head','Hex_Recess'):
                    o=bpy.data.objects[prefix+'_'+suffix];m=ri@o.matrix_world;inv=m.inverted()
                    for v in o.data.vertices:
                        p=m@v.co-old;p.x*=1.25;p.y*=1.25;v.co=inv@(new+p)
                    o.data.update()
                    if suffix=='Socket_Head':o['seated_at']=list(new);o['seat_normal']=[0,0,1]
                o=bpy.data.objects[prefix+'_Exposed_Shank'];lo,hi=bounds(o);m=ri@o.matrix_world;inv=m.inverted()
                # These are now screw stems entering the stage, not flange-gap supports.
                for v in o.data.vertices:
                    p=m@v.co;p.x=new.x+(p.x-old.x)*1.25;p.y=new.y+(p.y-old.y)*1.25
                    p.z=sh.z-.0048+(p.z-lo.z)/(hi.z-lo.z)*.005;v.co=inv@p
                o.data.update();o['role']='Existing screw stem seated into wider stage'
        scene['REF_flange_screws_on_stage']=True
        scene['REF_flange_screw_evidence']='ll1/ll2: existing screws seated on wider stage outside small flange. No additional screws. Gap and central neck unchanged.'
    bpy.context.view_layer.update()
    assert all(snapshot(bpy.data.objects[n])==v for n,v in protected.items())
    checks=[]
    for i in (1,2,3):
        fl,fh=bounds(bpy.data.objects[f'S{i}_Head_Flange']);sl,sh=bounds(bpy.data.objects[f'S{i}_Head_Raised_Step']);c=(fl+fh)/2
        for j in range(4):
            wl,wh=bounds(bpy.data.objects[f'MD_S{i}_Flange_Bolt_{j}_Washer']);wc=(wl+wh)/2
            r=Vector((wc.x-c.x,wc.y-c.y,0)).length
            assert abs(wl.z-sh.z)<1e-5
            assert r-(wh.x-wl.x)/2-(fh.x-fl.x)/2>.0009
            assert r+(wh.x-wl.x)/2<(sh.x-sl.x)/2
        checks.append({'station':i,'gap':fl.z-sh.z,'screw_radius':r,'seat_z':sh.z})
    json.dump({'protected':protected,'checks':checks},open(os.path.join(folder,'flange_screw_verification.json'),'w'),indent=2)
    txt=bpy.data.texts.get('LM_GENERATION_SCRIPT');txt.clear();txt.write(open(__file__,encoding='utf-8-sig').read())
    versions=bpy.context.preferences.filepaths.save_version;bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=working);bpy.context.preferences.filepaths.save_version=versions
    if '--no-render' not in sys.argv:
        scene.camera=bpy.data.objects['Flange_Gap_Preview'];scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
        scene.render.resolution_x=640;scene.render.resolution_y=480;scene.render.resolution_percentage=100
        scene.render.image_settings.file_format='PNG';scene.render.filepath=os.path.join(folder,'flange_screw_preview.png')
        bpy.ops.render.render(write_still=True)
    print('FLANGE_SCREWS_VERIFIED',checks,flush=True)

def insert_frame_pass():
    """Local pass1/pass3/pass4/holes evidence; no reconstruction or camera refit."""
    import bpy
    from mathutils import Vector
    folder=os.path.dirname(os.path.abspath(__file__));working=os.path.join(folder,'lapping_machine_blockout.blend')
    assert os.path.normcase(os.path.abspath(bpy.data.filepath))==os.path.normcase(working)
    scene=bpy.context.scene;root=bpy.data.objects['LM_ROOT_Move_Complete_Machine'];ri=root.matrix_world.inverted()
    assert scene.get('REF_flange_screws_on_stage')
    def bounds(o):
        p=[ri@o.matrix_world@Vector(v) for v in o.bound_box]
        return Vector([min(v[k] for v in p) for k in range(3)]),Vector([max(v[k] for v in p) for k in range(3)])
    def digest(o):
        d={'matrix':[list(r) for r in o.matrix_world],'hide':o.hide_render}
        if o.type=='MESH':d.update(vertices=[list(v.co) for v in o.data.vertices],materials=[m.name if m else None for m in o.data.materials])
        if o.type=='CURVE':d['points']=[[list(p.co) for p in s.bezier_points] for s in o.data.splines]
        if o.type=='CAMERA':d['lens']=[o.data.lens,o.data.shift_x,o.data.shift_y]
        return hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
    def local(o):
        n=o.name
        return n.startswith(('PROVISIONAL_','IF_')) or any(t in n for t in ('Cylinder_Body','Cylinder_End_Cap','Cylinder_Tie_Rod'))
    protected={o.name:digest(o) for o in bpy.data.objects if not local(o)}
    def material(name,color,metal,rough):
        m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
        return m
    silver=material('IF_Neutral_Silver',(.52,.55,.57),.82,.28)
    dark=material('IF_Dark_Insert',(.045,.049,.052),.55,.33)
    black=material('IF_Fitting_Black',(.018,.021,.024),.2,.34)
    frame_mat=bpy.data.objects['PROVISIONAL_Longitudinal_Spine'].data.materials[0]
    def finish(o,name,mat):
        o.name=name;o.parent=root;o.data.materials.clear();o.data.materials.append(mat);return o
    def cyl(name,x,y,z,r,h,mat,n=64):
        bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=h,location=(x,y,z))
        o=finish(bpy.context.object,name,mat)
        for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
        return o
    def box(name,center,size,mat,bevel=0):
        bpy.ops.mesh.primitive_cube_add(size=1,location=center);o=finish(bpy.context.object,name,mat);o.scale=size
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        if bevel:m=o.modifiers.new('Small manufactured edge','BEVEL');m.width=bevel;m.segments=3
        return o
    def cut(o,c):
        m=o.modifiers.new('Opening '+c.name,'BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=c
        c.hide_render=True;c.hide_set(True);c.display_type='WIRE'
    def member(name,a,b,width,z,h):
        a=Vector(a);b=Vector(b);c=(a+b)/2
        o=box(name,(c.x,c.y,z),(width,(b-a).length,h),frame_mat,.0008)
        o.rotation_euler.z=-math.atan2(b.x-a.x,b.y-a.y);return o
    if not scene.get('REF_insert_frame_pass'):
        # Console is negative Y; S1 is the nearest station, independent of image left/right.
        rl,rh=bounds(bpy.data.objects['S1_Hollow_Ring']);c=(rl+rh)/2
        pl,ph=bounds(bpy.data.objects['Circular_Working_Plate'])
        insert=cyl('IF_S1_Perforated_Insert',c.x,c.y,ph.z+.004,.126,.008,dark,128)
        # Full S1 pattern: center + six peripheral holes. Rear pair inferred from work.jpeg.
        for j,(dx,dy,r) in enumerate(([(0,0,.029)]+[(.080*math.cos(math.radians(a)),.080*math.sin(math.radians(a)),.029) for a in (180,0,240,300,60,120)])):
            cut(insert,cyl(f'IF_S1_Insert_Opening_{j}',c.x+dx,c.y+dy,ph.z+.004,r,.03,dark))
        insert['evidence']='work.jpeg: S1 only; seven equal through-holes, center plus six evenly spaced around it; hidden rear pair inferred. Thickness .008 retained.'
        # Replace only the provisional beam meshes. Original objects remain editable with real bay booleans.
        for name in ('PROVISIONAL_Longitudinal_Spine','PROVISIONAL_S2_Lateral_Branch','PROVISIONAL_S3_Lateral_Branch'):
            o=bpy.data.objects[name];lo,hi=bounds(o);m=ri@o.matrix_world;inv=m.inverted()
            for v in o.data.vertices:
                p=m@v.co
                if name.endswith('Spine'):p.x*=.13/.085
                else:p.y=(lo.y+hi.y)/2+(p.y-(lo.y+hi.y)/2)*(.13/.085)
                v.co=inv@p
            o.data.update()
        spine=bpy.data.objects['PROVISIONAL_Longitudinal_Spine']
        for j,(a,b) in enumerate(((-.588,-.345),(-.315,-.030),(.000,.315),(.345,.588))):
            cut(spine,box(f'IF_Spine_Bay_{j}',(0,(a+b)/2,1.103),(.098,b-a,.13),frame_mat))
        for i in (2,3):
            sign=-1 if i==2 else 1
            branch=bpy.data.objects[f'PROVISIONAL_S{i}_Lateral_Branch']
            cut(branch,box(f'IF_S{i}_Branch_Bay',(sign*.141,.08987,1.103),(.118,.098,.13),frame_mat))
            # Diagonal side walls enclose real triangular spaces beside each branch.
            for j,y in enumerate((-.235,.365)):
                member(f'IF_S{i}_Diagonal_{j}',(sign*.058,y),(sign*.214,.08987),.016,1.103,.085)
        for i in (1,2,3):
            body=bpy.data.objects[f'S{i}_Cylinder_Body'];lo,hi=bounds(body);x=(lo.x+hi.x)/2;y=(lo.y+hi.y)/2
            body.data.materials.clear();body.data.materials.append(silver)
            # Keep the original cylinder envelope/axis and cap seat. Cross saddles bridge each open bay.
            if i==1:
                for dy in (-.032,.032):box(f'IF_S{i}_Seat_{dy}',(x,y+dy,1.1415),(.13,.016,.008),frame_mat)
            else:
                for dx in (-.032,.032):box(f'IF_S{i}_Seat_{dx}',(x+dx,y,1.1415),(.016,.13,.008),frame_mat)
            # Existing underside mounting plates remain attached to the lower frame walls.
            for suffix in ('Cylinder_End_Cap','Cylinder_End_Cap.001'):
                cap=bpy.data.objects[f'S{i}_{suffix}'];cl,ch=bounds(cap)
                cap.data.materials.clear();cap.data.materials.append(silver)
                for mod in cap.modifiers:
                    if mod.type=='BEVEL':mod.width=.005;mod.segments=4
                if not any(m.type=='BEVEL' for m in cap.modifiers):
                    mod=cap.modifiers.new('Rounded cast cap corners','BEVEL');mod.width=.005;mod.segments=4
                if suffix.endswith('.001'):
                    # Shallow four-lobed cap pockets surrounding the central boss, not black paint.
                    for j,(dx,dy) in enumerate(((-.021,0),(.021,0),(0,-.021),(0,.021))):
                        cut(cap,box(f'IF_S{i}_Cap_Pocket_{j}',(x+dx,y+dy,ch.z-.002),(.021 if dx else .023,.023 if dx else .021,.009),silver,.003))
                    boss=cyl(f'IF_S{i}_Cap_Center',x,y,ch.z+.0007,.0125,.0014,silver)
                    cut(boss,cyl(f'IF_S{i}_Cap_Center_Recess',x,y,ch.z+.0015,.007,.0015,silver))
                    for j,(dx,dy) in enumerate(((-.0312,-.0312),(-.0312,.0312),(.0312,-.0312),(.0312,.0312))):
                        o=cyl(f'IF_S{i}_Cap_Corner_Boss_{j}',x+dx,y+dy,ch.z+.003,.0075,.006,silver)
                        cut(o,cyl(f'IF_S{i}_Cap_Fastener_Socket_{j}',x+dx,y+dy,ch.z+.005,.0033,.004,silver,6))
            for o in bpy.data.objects:
                if o.name.startswith(f'S{i}_Cylinder_Tie_Rod'):
                    a,b=bounds(o);cc=(a+b)/2;m=ri@o.matrix_world;inv=m.inverted()
                    for v in o.data.vertices:
                        p=m@v.co;p.x=cc.x+(p.x-cc.x)*.68;p.y=cc.y+(p.y-cc.y)*.68;v.co=inv@p
                    o.data.materials.clear();o.data.materials.append(silver)
            # Black side elbows meet the existing silver port and blue hose endpoint.
            sign=1 if x>0 else -1
            box(f'IF_S{i}_Top_Elbow',(x+sign*.053,y,hi.z+.006),(.012,.013,.017),black,.003)
            # Frame widening leaves S1 valve slightly inside the new wall: recess the wall locally.
        cut(spine,box('IF_S1_Valve_Wall_Recess',(-.054,-.17974,1.103),(.025,.041,.060),frame_mat))
        scene['REF_insert_frame_pass']=True
        scene['REF_insert_frame_assumptions']='S1 insert seven-hole full pattern; hidden rear pair inferred from work.jpeg; .008 thickness retained. Cylinder cap pocket depths and concealed frame saddle details inferred. Cylinder axes/envelopes and underside plates preserved.'
    bpy.context.view_layer.update()
    assert all(digest(bpy.data.objects[n])==v for n,v in protected.items()),'Unrelated object changed'
    json.dump({'protected':protected,'assumptions':scene['REF_insert_frame_assumptions']},open(os.path.join(folder,'insert_frame_verification.json'),'w'),indent=2)
    for name,eye,target,lens in (
        ('IF_Preview_Insert',(-.32,-.60,1.39),(-.025,-.195,.772),72),
        ('IF_Preview_Frame',(.95,-1.15,2.40),(0,0,1.22),58)):
        cam=bpy.data.objects.get(name)
        if not cam:cam=bpy.data.objects.new(name,bpy.data.cameras.new(name));scene.collection.objects.link(cam)
        cam.location=root.matrix_world@Vector(eye);cam.rotation_euler=(root.matrix_world@Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
    txt=bpy.data.texts['LM_GENERATION_SCRIPT'];txt.clear();txt.write(open(__file__,encoding='utf-8-sig').read())
    versions=bpy.context.preferences.filepaths.save_version;bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=working);bpy.context.preferences.filepaths.save_version=versions
    if '--no-render' not in sys.argv:
        scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
        scene.render.resolution_x=720;scene.render.resolution_y=540;scene.render.resolution_percentage=100
        scene.render.image_settings.file_format='PNG'
        for name,file in (('IF_Preview_Insert','insert_preview.png'),('IF_Preview_Frame','frame_preview.png')):
            if '--insert-only-preview' in sys.argv and name!='IF_Preview_Insert':continue
            scene.camera=bpy.data.objects[name];scene.render.filepath=os.path.join(folder,file);bpy.ops.render.render(write_still=True)
    print('INSERT_FRAME_PASS_SAVED',flush=True)

if '--console-contact-pass' in sys.argv:
    import runpy
    runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'console_contact.py'), run_name='__main__')
    raise SystemExit(0)

if '--inner-shroud-pass' in sys.argv:
    import runpy
    runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cabinet_inner_shroud.py'), run_name='__main__')
    raise SystemExit(0)

if '--front-frl-pass' in sys.argv:
    import runpy
    runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'relocate_frl.py'), run_name='__main__')
    raise SystemExit(0)

if '--cabinet-nameplates-pass' in sys.argv:
    import runpy
    runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cabinet_nameplates.py'), run_name='__main__')
    raise SystemExit(0)

if '--full-insert-pass' in sys.argv:
    import runpy
    runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'correct_insert_pattern.py'), run_name='__main__')
    raise SystemExit(0)

if '--valve-pass' in sys.argv:
    import runpy
    runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'valve_correction.py'), run_name='__main__')
    raise SystemExit(0)

if '--nameplate-pass' in sys.argv:
    import runpy
    runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nameplates.py'), run_name='__main__')
    raise SystemExit(0)

if '--insert-frame-pass' in sys.argv:
    insert_frame_pass()
    raise SystemExit(0)

if '--flange-screw-pass' in sys.argv:
    flange_stage_screw_pass()
    raise SystemExit(0)

if '--flange-gap-pass' in sys.argv:
    small_flange_gap_pass()
    raise SystemExit(0)

if '--reference-pass' in sys.argv:
    reference_comparison_pass()
    raise SystemExit(0)

import bpy
from mathutils import Vector, Matrix

FOLDER=os.path.dirname(os.path.abspath(__file__))
WORKING=os.path.join(FOLDER,'lapping_machine_blockout.blend')
RENDER='--no-render' not in sys.argv
DETAILS='Console_Control_Details'
PRESENTATION='Console_Detail_Previews'
if os.path.normcase(os.path.abspath(bpy.data.filepath)) != os.path.normcase(WORKING):
    raise RuntimeError('Open the existing lapping_machine_blockout.blend first. This script never replaces another open scene.')
panel=bpy.data.objects['Console_Sloping_Cream_Panel']
body=bpy.data.objects['Console_Lower_Cabinet']
door=bpy.data.objects['Console_Cream_Front_Door']

def fingerprint(o):
    data={'matrix':[list(row) for row in o.matrix_world], 'parent':o.parent.name if o.parent else None,
          'materials':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else []}
    if o.type=='MESH':
        data['vertices']=[tuple(v.co) for v in o.data.vertices]
        data['faces']=[tuple(p.vertices) for p in o.data.polygons]
    elif o.type=='CURVE':
        data['bevel_depth']=o.data.bevel_depth
        data['splines']=[[(tuple(p.co),tuple(p.handle_left),tuple(p.handle_right))
                         for p in s.bezier_points] for s in o.data.splines]
    return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
original={o.name:fingerprint(o) for o in bpy.data.objects}

def collection(name):
    col=bpy.data.collections.get(name)
    if not col:
        col=bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col
col=collection(DETAILS)

def mat(name,rgb,metal=0,rough=.35):
    name='CC_Material_'+name
    m=bpy.data.materials.get(name)
    if m:return m
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*rgb,1)
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    return m
black=mat('Black',(.012,.015,.018));silver=mat('Silver',(.48,.52,.56),.7)
red=mat('Red',(.65,.008,.016));yellow=mat('Yellow',(.95,.55,.004))
blue=mat('Blue',(.008,.12,.70));green=mat('Green',(.015,.32,.15))
white=mat('Grille_White',(.78,.80,.78));screen=mat('Display_Glass',(.023,.035,.045),.1)
digit=mat('Unlit_Display_Segments',(.09,.105,.11))

def bounds(o):
    return [min(v.co[k] for v in o.data.vertices) for k in range(3)], [max(v.co[k] for v in o.data.vertices) for k in range(3)]
pmin,pmax=bounds(panel);bmin,bmax=bounds(body);dmin,dmax=bounds(door)
pw=pmax[0]-pmin[0];ph=pmax[1]-pmin[1]
I=Matrix.Identity(4)
# Local surface frames: controls' +Z is the outward normal of their parent surface.
LEFT=Vector((0,0,1)).rotation_difference(Vector((-1,0,0))).to_matrix().to_4x4()
RIGHT=Vector((0,0,1)).rotation_difference(Vector((1,0,0))).to_matrix().to_4x4()
FRONT=Matrix.Rotation(math.pi/2,4,'X')

def position(parent,base,rotation,offset):
    return Matrix.Translation(Vector(base)) @ rotation @ Matrix.Translation(Vector(offset))

def part(name,parent,base,rotation,offset,size,material,kind='BOX',bevel=.001):
    name='CC_'+name
    if bpy.data.objects.get(name):return bpy.data.objects[name]
    if kind=='BOX':bpy.ops.mesh.primitive_cube_add(size=1)
    else:bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.5,depth=1)
    o=bpy.context.object;o.name=name;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for c in list(o.users_collection):c.objects.unlink(o)
    col.objects.link(o)
    o.parent=parent;o.matrix_parent_inverse=Matrix.Identity(4)
    o.matrix_basis=position(parent,base,rotation,offset)
    o.data.materials.append(material)
    if bevel:
        m=o.modifiers.new('Small edge radius','BEVEL');m.width=bevel;m.segments=3
        o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    o['console_detail']=True
    return o

def panel_base(u,v):return (pmin[0]+u*pw,pmin[1]+v*ph,pmax[2])
def button(name,u,v,color,diam=.028):
    b=panel_base(u,v)
    part(name+'_Bezel',panel,b,I,(0,0,.002),(diam+.005,diam+.005,.004),silver,'CYL')
    part(name+'_Rim',panel,b,I,(0,0,.0045),(diam+.002,diam+.002,.004),black,'CYL')
    part(name+'_Cap',panel,b,I,(0,0,.0075),(diam,diam,.006),color,'CYL')

def add_details():
    # Photograph 14 read 90 degrees counterclockwise: operator is at panel -Y.
    t=panel_base(.18,.72)
    part('Timer_Bezel',panel,t,I,(0,0,.003),(.102,.097,.006),black)
    part('Timer_Face',panel,t,I,(0,0,.0068),(.093,.088,.002),silver)
    part('Timer_Inset',panel,t,I,(0,0,.008),(.086,.080,.002),screen)
    part('Timer_Display_Window',panel,t,I,(0,.021,.0095),(.060,.023,.0015),black)
    # Unlit seven-segment geometry indicates a display, not a tiny text label.
    for i in range(3):
        x=-.020+i*.020
        for j,y in enumerate([.013,.021,.029]):
            part(f'Timer_Digit_{i}_H{j}',panel,t,I,(x,y,.0105),(.010,.0013,.0007),digit,bevel=.0002)
        for j,(dx,dy) in enumerate([(-.005,.025),(.005,.025),(-.005,.017),(.005,.017)]):
            part(f'Timer_Digit_{i}_V{j}',panel,t,I,(x+dx,dy,.0105),(.0013,.006,.0007),digit,bevel=.0002)
    for i in range(3):part(f'Timer_Setting_Key_{i}',panel,t,I,(-.016+i*.016,-.017,.010),(.011,.014,.003),black)
    for name,u,color in [('Red',.42,red),('Yellow',.56,yellow),('Blue',.70,blue)]:
        button('Indicator_'+name,u,.85,color)
    for i,u in enumerate([.42,.56],1):
        b=panel_base(u,.62)
        part(f'Selector_{i}_Base',panel,b,I,(0,0,.003),(.034,.034,.006),silver,'CYL')
        part(f'Selector_{i}_Body',panel,b,I,(0,0,.008),(.028,.028,.010),black,'CYL')
        r=Matrix.Rotation(-.60,4,'Z')
        part(f'Selector_{i}_Handle',panel,b,r,(0,0,.016),(.009,.032,.014),black)
        part(f'Selector_{i}_Pointer',panel,b,r,(0,.008,.0235),(.002,.010,.001),white,bevel=.0002)
    button('Pushbutton_Green',.70,.62,green)
    button('Pushbutton_Red_Start',.56,.39,red)
    button('Pushbutton_Red_Stop',.70,.39,red)
    b=panel_base(.42,.39)
    part('Emergency_Yellow_Backing',panel,b,I,(0,0,.002),(.054,.054,.004),yellow,'CYL')
    part('Emergency_Red_Stem',panel,b,I,(0,0,.012),(.026,.026,.020),red,'CYL')
    part('Emergency_Mushroom',panel,b,I,(0,0,.025),(.041,.041,.012),red,'CYL',.003)
    b=panel_base(.855,.62)
    part('Speed_Dial_Backing',panel,b,I,(0,0,.002),(.048,.048,.004),black,'CYL')
    part('Speed_Knob_Collar',panel,b,I,(0,0,.006),(.030,.030,.007),silver,'CYL')
    part('Speed_Knob',panel,b,I,(0,0,.015),(.023,.023,.016),black,'CYL')
    part('Speed_Red_Top',panel,b,I,(0,0,.0235),(.019,.019,.002),red,'CYL')
    for i,u in enumerate([.08,.92],1):
        b=panel_base(u,.10)
        part(f'Panel_Latch_{i}_Collar',panel,b,I,(0,0,.002),(.025,.025,.004),silver,'CYL')
        part(f'Panel_Latch_{i}_Wing',panel,b,I,(0,0,.007),(.011,.033,.008),black)
    for i,v in enumerate([.12,.90],1):
        b=(dmin[0]+.91*(dmax[0]-dmin[0]),dmin[1],dmin[2]+v*(dmax[2]-dmin[2]))
        part(f'Door_Latch_{i}_Collar',door,b,FRONT,(0,0,.002),(.026,.026,.004),silver,'CYL')
        part(f'Door_Latch_{i}_Wing',door,b,FRONT,(0,0,.006),(.033,.012,.008),black)
    # Both sides have white vents; sockets and isolator are on operator's LEFT only.
    for side,x,rot in [('Left',bmin[0],LEFT),('Right',bmax[0],RIGHT)]:
        # These frames have local X along +/-Z, and local Y along cabinet Y.
        # Build grilles with local X height, local Y width.
        for j,z in enumerate([.125,.415],1):
            b=(x,0,z-body.location.z)
            part(f'{side}_Grille_{j}_Frame',body,b,rot,(0,0,.004),(.115,.125,.008),white)
            part(f'{side}_Grille_{j}_Shadow',body,b,rot,(0,0,.0085),(.103,.111,.002),black)
            for k in range(15):
                part(f'{side}_Grille_{j}_Slat_{k:02d}',body,b,rot,(-.049+k*.007,0,.011),(.0045,.113,.006),white,bevel=.0006)
    b=(bmin[0],0,.325-body.location.z)
    part('Left_Isolator_Yellow_Plate',body,b,LEFT,(0,0,.003),(.043,.047,.006),yellow)
    part('Left_Isolator_Red_Hub',body,b,LEFT,(0,0,.010),(.027,.027,.014),red,'CYL')
    part('Left_Isolator_Red_Handle',body,b,LEFT,(0,0,.019),(.011,.035,.013),red)
    for j,y in enumerate([-.058,.058],1):
        b=(bmin[0],y,.255-body.location.z)
        part(f'Left_Socket_{j}_Flange',body,b,LEFT,(0,0,.003),(.043,.046,.006),silver)
        part(f'Left_Socket_{j}_Body',body,b,LEFT,(0,0,.012),(.037,.037,.018),blue,'CYL')
        part(f'Left_Socket_{j}_Closed_Cap',body,b,LEFT,(0,0,.023),(.043,.043,.006),blue,'CYL')
        part(f'Left_Socket_{j}_Hinge',body,b,LEFT,(.021,0,.020),(.009,.028,.010),silver)

# ---------------- PNEUMATICS: ADD ONLY MISSING NAMED PARTS ----------------
root=body.parent
pcol=collection('Pneumatics')
root_inv=root.matrix_world.inverted()
def rb(name):
    o=bpy.data.objects[name]
    pts=[root_inv@o.matrix_world@Vector(v) for v in o.bound_box]
    return Vector([min(v[k] for v in pts) for k in range(3)]),Vector([max(v[k] for v in pts) for k in range(3)])

def pmaterial(name,color,metal=0,rough=.32,glass=False):
    name='PN_Material_'+name
    m=bpy.data.materials.get(name)
    if m:return m
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*color,1)
    n.inputs['Metallic'].default_value=metal;n.inputs['Roughness'].default_value=rough
    if glass:n.inputs['Transmission Weight'].default_value=1;n.inputs['IOR'].default_value=1.46
    return m
ps=pmaterial('Silver',(.48,.53,.58),.75)
pb=pmaterial('Black',(.012,.016,.019))
pblue=pmaterial('Air_Blue',(.003,.26,.78),.0,.25)
pwhite=pmaterial('Gauge_Face',(.85,.85,.81),0,.55)
pglass=pmaterial('Transparent_Polycarbonate',(.91,.97,.99),0,.12,True)
pinner=pmaterial('Bowl_Interior',(.12,.14,.12),.1,.45)

def pf(o,name,material,bevel=.0007):
    o.name='PN_'+name
    for c in list(o.users_collection):c.objects.unlink(o)
    pcol.objects.link(o);o.parent=root;o.matrix_parent_inverse=Matrix.Identity(4)
    o.data.materials.append(material)
    if bevel:
        b=o.modifiers.new('Soft machined edges','BEVEL');b.width=bevel;b.segments=3
        o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return o

def pbox(name,center,size,material):
    if bpy.data.objects.get('PN_'+name):return bpy.data.objects['PN_'+name]
    bpy.ops.mesh.primitive_cube_add(size=1)
    o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    pf(o,name,material);o.location=center
    return o

def pcyl(name,a,b,r,material,vertices=64):
    if bpy.data.objects.get('PN_'+name):return bpy.data.objects['PN_'+name]
    a=Vector(a);b=Vector(b)
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=(b-a).length)
    o=pf(bpy.context.object,name,material);o.location=(a+b)/2
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o

def fitting(name,anchor,normal,length=.015):
    a=Vector(anchor);n=Vector(normal).normalized();end=a+n*length
    pcyl(name+'_Hex',a,a+n*(length-.004),.0065,ps,6)
    pcyl(name+'_Collar',a+n*(length-.005),end,.0055,pb)
    pcyl(name+'_Release',end-n*.002,end,.0048,pblue)
    return tuple(end)

routes={}
def hose(name,points,radius=.0033):
    name='PN_Hose_'+name
    if bpy.data.objects.get(name):return bpy.data.objects[name]
    points=[Vector(p) for p in points]
    # Explicit rounded polyline: straight spans and tangent quadratic corner arcs.
    segments=[];cursor=points[0]
    for i in range(1,len(points)-1):
        prev,p,nxt=points[i-1:i+2]
        trim=min(.018,(p-prev).length*.30,(nxt-p).length*.30)
        entry=p+(prev-p).normalized()*trim;exit=p+(nxt-p).normalized()*trim
        segments.append((cursor,entry,None));segments.append((entry,exit,p));cursor=exit
    segments.append((cursor,points[-1],None))
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=16
    cu.bevel_depth=radius;cu.bevel_resolution=5;cu.use_fill_caps=True
    sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(segments))
    sp.bezier_points[0].co=segments[0][0]
    for i,(a,b,corner) in enumerate(segments):
        pa=sp.bezier_points[i];pbp=sp.bezier_points[i+1]
        pa.handle_left_type=pa.handle_right_type='FREE';pbp.handle_left_type=pbp.handle_right_type='FREE'
        pbp.co=b
        pa.handle_right=a+(b-a)/3 if corner is None else a+(corner-a)*2/3
        pbp.handle_left=b-(b-a)/3 if corner is None else b+(corner-b)*2/3
    sp.bezier_points[0].handle_left=points[0]
    sp.bezier_points[-1].handle_right=points[-1]
    o=bpy.data.objects.new(name,cu);pcol.objects.link(o);o.parent=root;cu.materials.append(pblue)
    o['routing']='Visible exterior approximation; not a verified hidden circuit'
    o['start_fitting_point']=list(points[0]);o['end_fitting_point']=list(points[-1])
    return o

def boolean_cut(obj,cutter):
    bpy.context.view_layer.update()
    mod=obj.modifiers.new('Inspection opening','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
    bpy.context.view_layer.objects.active=obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter,do_unlink=True)

def guard(name,x,y,z):
    if bpy.data.objects.get('PN_'+name):return
    outer=pcyl(name,(x,y,z),(x,y,z+.060),.020,ps)
    # Apply bevel only after the shell and openings are cut.
    outer.modifiers.clear()
    inner=pcyl(name+'_CUT_INNER',(x,y,z-.002),(x,y,z+.062),.0178,ps)
    boolean_cut(outer,inner)
    for axis in range(2):
        for row in range(2):
            cutter=pbox(name+f'_CUT_{axis}_{row}',(x,y,z+.017+row*.028),
                        (.011,.055,.019) if axis==0 else (.055,.011,.019),ps)
            cutter.modifiers.clear()
            m=cutter.modifiers.new('Rounded window corners','BEVEL');m.width=.0045;m.segments=5
            bpy.context.view_layer.objects.active=cutter;bpy.ops.object.modifier_apply(modifier=m.name)
            boolean_cut(outer,cutter)
    m=outer.modifiers.new('Guard edge bevel','BEVEL');m.width=.0007;m.segments=3
    outer.modifiers.new('Weighted normals','WEIGHTED_NORMAL')

rearmin,rearmax=rb('Rear_Centerline_Column')
beammin,beammax=rb('PROVISIONAL_Longitudinal_Spine')
ry=rearmax.y+.027
unit_z=beammin.z-.137

def add_pneumatics():
    if bpy.context.scene.get('VP_reference_valves'):return  # Preserve corrected reference assemblies.
    # Seen from rear, regulator is image-left (+X), lubricator image-right (-X).
    pbox('Rear_Column_Mount',(0,rearmax.y+.005,unit_z),(.026,.010,.100),ps)
    pbox('FRL_Bridge',(0,ry-.010,unit_z),(.097,.022,.026),ps)
    for x,label in [(.031,'Filter_Regulator'),(-.031,'Lubricator')]:
        pbox(label+'_Body',(x,ry,unit_z),(.047,.033,.035),ps)
        pcyl(label+'_Inner_Bowl',(x,ry,unit_z-.077),(x,ry,unit_z-.019),.0173,pglass)
        pcyl(label+'_Inner_Core',(x,ry,unit_z-.075),(x,ry,unit_z-.028),.010,pinner)
        guard(label+'_Silver_Guard',x,ry,unit_z-.078)
        pcyl(label+'_Bowl_Base',(x,ry,unit_z-.081),(x,ry,unit_z-.076),.018,ps)
    pcyl('Regulator_Knob_Base',(.031,ry,unit_z+.017),(.031,ry,unit_z+.025),.024,pb)
    pcyl('Regulator_Adjustment_Knob',(.031,ry,unit_z+.025),(.031,ry,unit_z+.064),.017,pb)
    for i in range(12):
        a=2*math.pi*i/12
        pcyl(f'Knob_Grip_{i}',(.031+.017*math.cos(a),ry+.017*math.sin(a),unit_z+.031),
             (.031+.017*math.cos(a),ry+.017*math.sin(a),unit_z+.061),.001,pb)
    pcyl('Lubricator_Clear_Upper',(-.031,ry,unit_z+.020),(-.031,ry,unit_z+.049),.0085,pglass)
    pcyl('Lubricator_Upper_Base',(-.031,ry,unit_z+.017),(-.031,ry,unit_z+.026),.010,ps)
    pcyl('Lubricator_Adjuster',(-.048,ry+.004,unit_z+.017),(-.048,ry+.004,unit_z+.025),.006,pb)
    pbox('Drain_Elbow',(.031,ry,unit_z-.091),(.022,.018,.017),pb)
    pcyl('Drain_Outlet',(.020,ry,unit_z-.093),(.009,ry,unit_z-.093),.004,ps)
    # Gauge face points outward +Y, directly opposite console.
    gx=.031;gz=unit_z;gy=ry+.026
    pcyl('Gauge_Neck',(gx,ry+.015,gz),(gx,gy,gz),.009,ps)
    pcyl('Gauge_Silver_Case',(gx,gy-.004,gz),(gx,gy+.010,gz),.031,ps)
    pcyl('Gauge_Black_Inner_Rim',(gx,gy+.010,gz),(gx,gy+.011,gz),.0286,pb)
    pcyl('Gauge_White_Face',(gx,gy+.011,gz),(gx,gy+.012,gz),.027,pwhite)
    for k in range(41):
        a=math.radians(-135+270*k/40);r=.024
        # Gauge-plane vertical is +Z. Major/minor ticks; no branding.
        long=k%4==0;length=.004 if long else .002
        a1=(gx+(r-length)*math.sin(a),gy+.0125,gz+(r-length)*math.cos(a))
        a2=(gx+r*math.sin(a),gy+.0125,gz+r*math.cos(a))
        pcyl(f'Gauge_Tick_{k:02d}',a1,a2,.00032 if long else .00018,pb,8)
    pcyl('Gauge_Needle',(gx,gy+.013,gz),(gx+.022,gy+.013,gz+.002),.00065,pb,12)
    pcyl('Gauge_Pivot',(gx,gy+.012,gz),(gx,gy+.015,gz),.0025,ps)
    inlet=fitting('FRL_Inlet',(.055,ry,unit_z),(1,0,0))
    outlet=fitting('FRL_Outlet',(-.055,ry,unit_z),(-1,0,0))
    tail=(.12,ry+.11,unit_z-.12)
    hose('Short_External_Supply',[inlet,(.11,ry,unit_z),(.14,ry+.065,unit_z-.03),tail],.0038)
    # Unconnected supply end is intentional: short external presentation tail.
    fitting('Supply_Tail_Connector',tail,(0,0,-1),.011)
    valve_inlets=[]
    for i in range(1,4):
        cmin,cmax=rb(f'S{i}_Cylinder_Body');x=(cmin.x+cmax.x)/2;y=(cmin.y+cmax.y)/2
        sign=1 if x>0 else -1
        mountmin,mountmax=rb(f'S{i}_Underside_Mount')
        surface=beammin.x if i==1 else (mountmax.x if sign>0 else mountmin.x)
        vx=surface+sign*.009;vz=(beammin.z+beammax.z)/2
        pbox(f'S{i}_Valve_Mount',(surface+sign*.002,y,vz),(.004,.036,.055),pb)
        pbox(f'S{i}_Valve_Block',(vx,y,vz),(.014,.027,.042),ps)
        pcyl(f'S{i}_Valve_Black_Actuator',(vx,y,vz-.023),(vx+sign*.025,y,vz-.023),.010,pb)
        inv=fitting(f'S{i}_Valve_Inlet',(vx,y+.0135,vz),(0,1,0),.015)
        valve_inlets.append(inv)
        topport=fitting(f'S{i}_Cylinder_Top_Port',(x+sign*.040,y,cmax.z+.009),(sign,0,0))
        bottomport=fitting(f'S{i}_Cylinder_Lower_Port',(x+sign*.040,y,cmin.z-.009),(sign,0,0))
        vtop=fitting(f'S{i}_Valve_Upper_Port',(vx+sign*.007,y,vz+.012),(sign,0,0))
        vbottom=fitting(f'S{i}_Valve_Lower_Port',(vx+sign*.007,y,vz-.006),(sign,0,0))
        outer=surface+sign*.062
        hose(f'S{i}_Vertical_Cylinder_Run',[topport,(x+sign*.075,y,cmax.z-.006),
              (x+sign*.075,y,beammax.z+.034),(outer,y,beammax.z+.020),
              (outer,y,vz+.012),vtop])
        hose(f'S{i}_Lower_Loop',[vbottom,(outer,y,vz-.020),(outer,y-.062,beammin.z-.022),
              (outer,y-.085,beammax.z+.019),(x+sign*.067,y-.05,beammax.z+.020),bottomport])
        # Thin annular blue band wraps the existing silver body, without editing it.
        name=f'PN_S{i}_Blue_Cylinder_Band'
        if not bpy.data.objects.get(name):
            n=96;r=(cmax.x-cmin.x)/2+.00035;z=cmax.z-.013
            verts=[(x+rr*math.cos(k*2*math.pi/n),y+rr*math.sin(k*2*math.pi/n),zz)
                   for rr,zz in [(r,z),(r,z+.012),(r-.00025,z),(r-.00025,z+.012)] for k in range(n)]
            faces=[]
            for k in range(n):
                j=(k+1)%n
                faces.extend([(k,j,j+n,k+n),(2*n+j,2*n+k,3*n+k,3*n+j),
                              (k+n,j+n,j+3*n,k+3*n),(j,k,k+2*n,j+2*n)])
            me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
            o=bpy.data.objects.new(name,me);pcol.objects.link(o);o.parent=root;me.materials.append(pblue)
    # External feed follows rear column and the side of the beam, not through it.
    end=valve_inlets[1]
    hose('Regulator_To_Rear_Valve',[outlet,(-.105,ry+.025,unit_z+.02),(-.13,ry+.040,beammin.z-.014),
          (-.28,.43,beammin.z+.018),(-.28,.20,end[2]),(end[0],end[1]+.025,end[2]),end])
    # One visible under-structure link. The hidden distribution circuit is omitted.
    t=Vector(valve_inlets[1]);anchor=t-Vector((0,.006,0))
    branch=fitting('Rear_Valve_Tee_Branch',anchor,(-1,0,0),.018)
    end=valve_inlets[2]
    hose('Approximate_Under_Beam_Link',[branch,(-.28,.17,t.z),(-.28,.20,beammin.z-.026),(-.08,.25,beammin.z-.026),
          (.13,.25,beammin.z-.026),(.28,.19,beammin.z-.026),(.28,.16,end[2]),
          (end[0],end[1]+.025,end[2]),end])

# Mechanical maintenance: non-destructive cuts preserve source meshes/manual edits.
mcol=collection('Mechanical_Details');cutcol=collection('Mechanical_Cutters')
metal=bpy.data.objects['S1_Hollow_Ring'].data.materials[0]
paint=bpy.data.objects['Panel_Left'].data.materials[0]
changed_hoses=set()
def mf(o,name,material,bevel=.0005):
    o.name='MD_'+name
    for c in list(o.users_collection):c.objects.unlink(o)
    mcol.objects.link(o);o.parent=root;o.matrix_parent_inverse=Matrix.Identity(4)
    o.data.materials.append(material)
    if bevel:
        b=o.modifiers.new('Detail edge bevel','BEVEL');b.width=bevel;b.segments=3
    return o

def mb(name,center,size,material=metal,angle=0,bevel=.0005):
    if bpy.data.objects.get('MD_'+name):return bpy.data.objects['MD_'+name]
    bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    mf(o,name,material,bevel);o.location=center;o.rotation_euler.z=angle;return o

def mc(name,a,b,r,material=metal,n=48):
    if bpy.data.objects.get('MD_'+name):return bpy.data.objects['MD_'+name]
    a=Vector(a);b=Vector(b)
    bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=(b-a).length)
    o=mf(bpy.context.object,name,material);o.location=(a+b)/2;o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def cut(target,cutter):
    tag='MD_Cut_'+cutter.name
    if not target.modifiers.get(tag):
        m=target.modifiers.new(tag,'BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cutter
    for c in list(cutter.users_collection):c.objects.unlink(cutter)
    cutcol.objects.link(cutter);cutter.hide_render=True;cutter.hide_set(True);cutter.display_type='WIRE'

def tor(name,center,r,t,material=metal):
    if bpy.data.objects.get('MD_'+name):return bpy.data.objects['MD_'+name]
    bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=t,major_segments=96,minor_segments=8)
    o=mf(bpy.context.object,name,material,0);o.location=center
    for f in o.data.polygons:f.use_smooth=True
    return o

def bolt(name,seat,normal=(0,0,1),r=.006):
    a=Vector(seat);n=Vector(normal)
    w=mc(name+'_Washer',a,a+n*.0015,r*1.4,ps)
    h=mc(name+'_Socket_Head',a+n*.0015,a+n*(.0015+r),r,pb)
    c=mc(name+'_Hex_Recess',a+n*(r*.65+.0015),a+n*(r+.003),r*.51,pb,6)
    cut(h,c)
    h['seated_at']=list(a);h['seat_normal']=list(n)

def slot(target,name,center,size,angle=0):
    o=mb(name,center,size,pb,angle,0)
    if not o.modifiers.get('Rounded slot'):
        b=o.modifiers.new('Rounded slot','BEVEL');b.width=min(size)*.48;b.segments=6
    cut(target,o)

def add_mechanical():
    for i in range(1,4):
        ring=bpy.data.objects[f'S{i}_Hollow_Ring'];lo,hi=rb(ring.name);x=(lo.x+hi.x)/2;y=(lo.y+hi.y)/2;r=(hi.x-lo.x)/2
        radial=Vector((x,y,0)).normalized();tangent=Vector((-radial.y,radial.x,0))
        def pos(u,v,z):return Vector((x,y,z))+radial*u+tangent*v
        angle=math.atan2(radial.y,radial.x)
        if not bpy.context.scene.get('BM_working_parts_photo_match'):
            for j,frac in enumerate((.57,.76)):
                cut(ring,tor(f'S{i}_Ring_Groove_{j}',(x,y,lo.z+(hi.z-lo.z)*frac),r,.0011))
        # Three visible-sector lower slots; concealed repetition deliberately not assumed.
        for j,a in enumerate((angle-.7,angle,angle+.7)):
            center=(x+(r-.006)*math.cos(a),y+(r-.006)*math.sin(a),lo.z+.021)
            cut(ring,mb(f'S{i}_Ring_Vertical_Slot_{j}',center,(.021,.0022,.043),pb,a,.0002))
        for j in (1,2):
            lo2,hi2=rb(f'S{i}_Roller_{j}');cx=(lo2.x+hi2.x)/2;cy=(lo2.y+hi2.y)/2
            mc(f'S{i}_Roller_{j}_Neck',(cx,cy,hi2.z),(cx,cy,hi2.z+.0018),.0145,pb)
            mc(f'S{i}_Roller_{j}_Top_Cap',(cx,cy,hi2.z+.0018),(cx,cy,hi2.z+.006),.0175,ps)
        # Existing curved carrier remains; add the photographed slotted outer extension.
        bracket=bpy.data.objects[f'S{i}_Roller_Bracket'];bl,bh=rb(bracket.name)
        ext=mb(f'S{i}_Bracket_Adjustment_Plate',pos(.198,0,bh.z-.003),(.053,.108,.010),metal,angle,.003)
        # Support block reaches the underside of the extension, outside the working plate.
        block=mb(f'S{i}_Bracket_Raised_Block',pos(.198,0,(.735+bh.z-.008)/2),(.040,.090,bh.z-.008-.735),metal,angle,.001)
        slot(ext,f'S{i}_Bracket_Long_Slot',pos(.198,0,bh.z-.003),(.008,.082,.030),angle)
        for j,v in enumerate((-.027,.027)):bolt(f'S{i}_Bracket_Bolt_{j}',pos(.198,v,bh.z+.002))
        # Shallow corner chamfers on the carrier are handled by its existing bevel.
        fl,fh=rb(f'S{i}_Head_Flange')
        for j,a in enumerate((0,math.pi/2,math.pi,3*math.pi/2)):
            bolt(f'S{i}_Flange_Bolt_{j}',(x+.048*math.cos(a),y+.048*math.sin(a),fh.z),r=.004)
        sl,sh=rb(f'S{i}_Aligned_Shaft')
        mc(f'S{i}_Shaft_Hex_Coupling',(x,y,sl.z+.002),(x,y,sl.z+.012),.015,ps,6)
        mc(f'S{i}_Shaft_Upper_Collar',(x,y,sh.z-.016),(x,y,sh.z),.020,metal)
        ml,mh=rb(f'S{i}_Underside_Mount')
        for k,(dx,dy) in enumerate([(-.047,-.049),(.047,-.049),(-.047,.049),(.047,.049)]):
            slot(bpy.data.objects[f'S{i}_Underside_Mount'],f'S{i}_Mount_Slot_{k}',(x+dx,y+dy,(ml.z+mh.z)/2),(.028,.008,.030))
            bolt(f'S{i}_Mount_Bolt_{k}',(x+dx,y+dy,ml.z),(0,0,-1),.005)
        dl,dh=rb(f'S{i}_Head_Lower_Disk')
        a=angle;v=Vector((math.cos(a),math.sin(a),0));c=Vector((x,y,(dl.z+dh.z)/2))
        cut(bpy.data.objects[f'S{i}_Head_Lower_Disk'],mc(f'S{i}_Disk_Rim_Hole',c+v*.132,c+v*.146,.0032,pb))
    # One short, directly visible division in the exposed plate sector.
    plate=bpy.data.objects['Circular_Working_Plate'];pl,ph=rb(plate.name)
    if not bpy.context.scene.get('BM_working_parts_photo_match'):
        cut(plate,mb('Plate_Visible_Division',(.305,0,ph.z),(.12,.0008,.0012),pb,0,0))
    for name in ('Panel_Front','Panel_Rear','Panel_Left','Panel_Right'):
        lo,hi=rb(name);side=name in ('Panel_Left','Panel_Right');sign=-1 if name in ('Panel_Left','Panel_Front') else 1
        normal=(sign,0,0) if side else (0,sign,0)
        surf=(lo.x if sign<0 else hi.x) if side else (lo.y if sign<0 else hi.y)
        for k,(h,z) in enumerate([(-.45,lo.z+.025),(.45,lo.z+.025),(-.45,hi.z-.025),(.45,hi.z-.025)]):
            seat=(surf,h,z) if side else (h,surf,z);bolt(name+f'_Fastener_{k}',seat,normal,.0036)
        if side:
            for bank,y in enumerate((-.30,.30)):
                for j in range(5):
                    z=.185+j*.032
                    # Cut opening plus rounded projecting hood with downward-facing mouth.
                    cut(bpy.data.objects[name],mb(name+f'_Louver_Aperture_{bank}_{j}',(surf,y,z),(.030,.092,.006),pb,0,.002))
                    hood=mb(name+f'_Louver_Hood_{bank}_{j}',(surf+sign*.003,y,z+.004),(.010,.098,.012),paint,0,.005)
    for idx,o in enumerate([o for o in bpy.data.objects if o.name.startswith('Table_Spacer')]):
        lo,hi=rb(o.name);x=(lo.x+hi.x)/2;y=(lo.y+hi.y)/2
        for j in range(18):tor(f'Spacer_{idx}_Thread_{j}',(x,y,lo.z+.011+j*.0027),.012,.00065,ps)
        mc(f'Spacer_{idx}_Lower_Nut',(x,y,lo.z),(x,y,lo.z+.009),.019,ps,6)
        mc(f'Spacer_{idx}_Upper_Nut',(x,y,hi.z-.016),(x,y,hi.z-.008),.019,ps,6)
        mc(f'Spacer_{idx}_Base_Washer',(x,y,lo.z),(x,y,lo.z+.002),.022,ps)
    for idx,o in enumerate([o for o in bpy.data.objects if o.name.startswith('Mounting_Foot')]):
        lo,hi=rb(o.name);x=(lo.x+hi.x)/2;y=(lo.y+hi.y)/2
        x+=math.copysign(.018,x);y+=math.copysign(.018,y)
        cut(o,mc(f'Foot_{idx}_Anchor_Hole',(x,y,lo.z-.002),(x,y,hi.z+.002),.008,pb))
    for side in ('Front','Rear'):
        lo,hi=rb(side+'_Column_Cap');y=(lo.y+hi.y)/2
        for j,(x,dy) in enumerate([(-.065,-.043),(.065,-.043),(-.065,.043),(.065,.043)]):
            bolt(side+f'_Cap_Bolt_{j}',(x,y+dy,hi.z),r=.005)
    rear=bpy.data.objects['Rear_Lower_Attachment'];lo,hi=rb(rear.name)
    for i,x in enumerate((-.074,.074)):
        plate=mb(f'Rear_Adjustment_Plate_{i}',(x,hi.y+.006,(lo.z+hi.z)/2),(.045,.012,hi.z-lo.z),paint,.0,.001)
        for j,z in enumerate((lo.z+.045,hi.z-.045)):
            slot(plate,f'Rear_Adjustment_Slot_{i}_{j}',(x,hi.y+.006,z),(.009,.032,.055))
            bolt(f'Rear_Adjustment_Bolt_{i}_{j}',(x,hi.y+.012,z),(0,1,0),.005)
        for j in range(5):
            mc(f'Rear_Adjustment_Index_{i}_{j}',(x,.516,.35+j*.018),(x,.517,.35+j*.018),.002,pb)
    # Exterior stub only. On operator-right (+X), appearing left in a rear photograph.
    pipe=mc('Rear_Exterior_Pipe',(.19,.514,.435),(.19,.642,.435),.016,metal)
    cut(pipe,mc('Rear_Pipe_Bore',(.19,.520,.435),(.19,.645,.435),.013,pb))
    mb('Rear_Pipe_Dark_Aperture',(.19,.5165,.435),(.047,.001,.044),pb)

def smooth_hoses_once():
    for o in pcol.objects:
        if o.type!='CURVE' or o.get('MD_softened'):continue
        # Preserve endpoint locations and manual route; soften the existing corner arcs.
        bp=o.data.splines[0].bezier_points
        for j in range(1,len(bp)-1,2):
            a=bp[j];b=bp[j+1]
            if j+2>=len(bp):continue
            incoming=(a.co-bp[j-1].co);outgoing=(bp[j+2].co-b.co)
            if incoming.length<1e-5 or outgoing.length<1e-5:continue
            extra=min(.007,incoming.length*.16,outgoing.length*.16)
            da=-incoming.normalized()*extra;db=outgoing.normalized()*extra
            a.co+=da;a.handle_left+=da;a.handle_right+=da*.33
            b.co+=db;b.handle_left+=db*.33;b.handle_right+=db
        o.data.resolution_u=24
        # 7.2 mm nominal at the 1 m cabinet convention, formerly 6.6 mm.
        o.data.bevel_depth=max(o.data.bevel_depth,.0036)
        o['MD_softened']=True;changed_hoses.add(o.name)

add_mechanical();smooth_hoses_once()
bpy.context.view_layer.update()
mechanical_names=set(bpy.data.objects.keys())
add_mechanical();smooth_hoses_once()
bpy.context.view_layer.update()
assert mechanical_names==set(bpy.data.objects.keys()),'Mechanical rerun duplicated parts'

add_details()  # Existing console controls are retained unchanged.
add_pneumatics()
bpy.context.view_layer.update()
initial_names=set(pcol.objects.keys())
initial_parts={o.name:fingerprint(o) for o in pcol.objects}
add_pneumatics()
bpy.context.view_layer.update()
assert set(pcol.objects.keys())==initial_names
assert initial_parts=={o.name:fingerprint(o) for o in pcol.objects}
for name,value in original.items():
    if name in changed_hoses:continue
    assert bpy.data.objects.get(name) and fingerprint(bpy.data.objects[name])==value,'Existing object changed: '+name

# Clearance sampling against existing machine structure (hose radius included).
from mathutils.bvhtree import BVHTree
from mathutils.geometry import interpolate_bezier
obstacles=[]
for o in bpy.data.objects:
    if o.type!='MESH' or o.name.startswith(('PN_','CC_','MD_','Studio')):continue
    if not any(t in o.name for t in ['Column','Spine','Branch','Head_','Shaft','Mount','Cylinder','Tabletop']):continue
    me=o.data;matrix=root_inv@o.matrix_world
    obstacles.append((o.name,BVHTree.FromPolygons([matrix@v.co for v in me.vertices],[list(p.vertices) for p in me.polygons])))
collisions=[]
for o in pcol.objects:
    if o.type!='CURVE':continue
    hose_matrix=root_inv@o.matrix_world
    bp=o.data.splines[0].bezier_points
    for a,b in zip(bp,bp[1:]):
        n=max(8,int((b.co-a.co).length/.0015))
        for pt in interpolate_bezier(a.co,a.handle_right,b.handle_left,b.co,n):
            pt=hose_matrix@pt
            for name,tree in obstacles:
                hit=tree.find_nearest(pt)
                if hit[0] is not None and hit[3]<o.data.bevel_depth-.0002:
                    collisions.append((o.name,name,round(hit[3],5)));break
report={'existing_objects_unchanged':len(original)-len(changed_hoses),'pneumatic_parts':len(pcol.objects),
        'editable_hoses':sum(o.type=='CURVE' for o in pcol.objects),'rerun_duplicate_check':True,
        'clearance_conflicts':sorted(set(collisions)),
        'approximate':'Under-beam link and obscured bends; hidden distribution circuit omitted. External supply intentionally shortened.'}
with open(os.path.join(FOLDER,'pneumatic_checks.json'),'w') as f:json.dump(report,f,indent=2)
assert not collisions,'Hose clearance check failed; inspect pneumatic_checks.json before saving'


# Evaluate hollow centers and accepted station geometry after modifier cuts.
dg=bpy.context.evaluated_depsgraph_get();ringchecks=[]
for i in range(1,4):
    o=bpy.data.objects[f'S{i}_Hollow_Ring'];lo,hi=rb(o.name);c=(lo+hi)/2
    eo=o.evaluated_get(dg);me=eo.to_mesh();matrix=root_inv@o.matrix_world
    vs=[matrix@v.co for v in me.vertices]
    tree=BVHTree.FromPolygons(vs,[list(p.vertices) for p in me.polygons])
    assert tree.ray_cast(Vector((c.x,c.y,hi.z+.01)),Vector((0,0,-1)),hi.z-lo.z+.02)[0] is None,'Blocked ring center'
    rad=max(math.hypot(v.x-c.x,v.y-c.y) for v in vs)
    assert abs(rad-(hi.x-lo.x)/2)<.00015,'Ring outside size changed'
    for suffix in ('Aligned_Shaft','Cylinder_Body'):
        a,b=rb(f'S{i}_{suffix}');assert ((a+b)/2-c).xy.length<1e-5,'Station alignment changed'
    a,b=rb(f'S{i}_Head_Lower_Disk');assert a.z-hi.z>.05
    ringchecks.append({'station':i,'open_center':True,'outer_radius':round(rad,5),'head_clearance':round(a.z-hi.z,5)})
    eo.to_mesh_clear()
report.update({'mechanical_objects':len(mcol.objects),'cutters':len(cutcol.objects),
               'mechanical_rerun_no_duplicates':True,'hose_curves_softened_this_run':len(changed_hoses),
               'ring_checks':ringchecks,'source_meshes_preserved':True,
               'approximate_mechanical':'Fastener sizes, slot lengths and ring slot angular placement; one exposed plate division only. Threads are economical circular ridges.'})
with open(os.path.join(FOLDER,'mechanical_checks.json'),'w') as f:json.dump(report,f,indent=2)
# ---------------- PRESENTATION: once-only material/light upgrade; editable labels ----------------
scene=bpy.context.scene
labels=collection('Labels_and_Badges')
pres=collection('Mechanical_Previews')  # reuse the existing presentation collection
world=lambda p:root.matrix_world@Vector(p)

def finish_material(name,color,metallic,roughness,texture=None):
    m=bpy.data.materials[name]
    if m.get('PR_finished'):return m
    m.use_nodes=True;m.diffuse_color=(*color,1)
    nt=m.node_tree;p=nt.nodes.get('Principled BSDF')
    for key,value in [('Base Color',(*color,1)),('Metallic',metallic),('Roughness',roughness)]:
        for link in list(p.inputs[key].links):nt.links.remove(link)
        p.inputs[key].default_value=value
    if texture:
        tex=nt.nodes.new('ShaderNodeTexNoise');tex.name='PR_Subtle_Surface';tex.inputs['Scale'].default_value=texture[0]
        tex.inputs['Detail'].default_value=2;tex.inputs['Roughness'].default_value=.45
        coord=nt.nodes.new('ShaderNodeTexCoord');nt.links.new(coord.outputs['Object'],tex.inputs['Vector'])
        ramp=nt.nodes.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=0;ramp.inputs['From Max'].default_value=1
        ramp.inputs['To Min'].default_value=roughness-.025;ramp.inputs['To Max'].default_value=roughness+.025
        nt.links.new(tex.outputs['Fac'],ramp.inputs['Value']);nt.links.new(ramp.outputs[0],p.inputs['Roughness'])
        bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=texture[1]
        nt.links.new(tex.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],p.inputs['Normal'])
    m['PR_finished']=True;return m

def presentation_materials():
    finish_material('LM_Grey_Paint',(.205,.225,.235),.05,.43,(1700,.000035))
    finish_material('LM_Cream_Paint',(.72,.665,.50),.0,.43,(1700,.00003))
    finish_material('LM_Dark_Metal',(.052,.060,.066),.8,.34,(600,.000012))
    for n in ('LM_Silver','CC_Material_Silver','PN_Material_Silver'):finish_material(n,(.54,.58,.62),1,.28)
    finish_material('PN_Material_Air_Blue',(.003,.205,.59),0,.27)
    finish_material('PN_Material_Black',(.009,.012,.015),.12,.36)
    finish_material('CC_Material_Black',(.008,.010,.012),.05,.38)
    finish_material('LM_Studio',(.25,.27,.29),0,.78)
    finish_material('CC_Material_Grille_White',(.68,.70,.68),0,.48)
    finish_material('CC_Material_Red',(.60,.005,.009),0,.29)
    finish_material('CC_Material_Yellow',(.95,.57,.003),0,.3)
    finish_material('CC_Material_Blue',(.004,.10,.60),0,.3)
    finish_material('CC_Material_Green',(.008,.27,.10),0,.3)
    for o in bpy.data.objects:
        if o.get('PR_material_assigned'):continue
        if o.name.startswith('MD_') and o.name.endswith('_Socket_Head'):
            o.data.materials[0]=bpy.data.materials['PN_Material_Silver'];o['PR_material_assigned']=True
        if o.name.startswith(('S1_Roller_','S2_Roller_','S3_Roller_')) and o.name[-1:] in ('1','2'):
            o.data.materials[0]=bpy.data.materials['LM_Dark_Metal'];o['PR_material_assigned']=True

ink=mat('Label_Ink',(.004,.006,.008),0,.5)
paper=mat('Label_White',(.82,.83,.80),0,.5)
labelred=mat('Label_Red',(.56,.007,.014),0,.48)
labelblue=mat('Label_Blue',(.005,.19,.40),0,.48)

def text_label(name,text,parent,frame,xy,size,material=ink):
    name='PR_'+name
    if bpy.data.objects.get(name):return bpy.data.objects[name]
    cu=bpy.data.curves.new(name,'FONT');cu.body=text;cu.align_x='CENTER';cu.align_y='CENTER';cu.size=size
    cu.extrude=0;cu.resolution_u=8;cu.space_character=1.0
    o=bpy.data.objects.new(name,cu);labels.objects.link(o);o.parent=parent;o.matrix_parent_inverse=Matrix.Identity(4)
    o.matrix_basis=frame@Matrix.Translation(Vector(xy));cu.materials.append(material)
    o['reference']='Readable wording only, photographs 12-14; no invented specifications'
    return o

def label_plate(name,parent,frame,size,material=paper):
    name='PR_'+name
    if bpy.data.objects.get(name):return bpy.data.objects[name]
    bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.name=name;o.dimensions=(size[0],size[1],.00035)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for c in list(o.users_collection):c.objects.unlink(o)
    labels.objects.link(o);o.parent=parent;o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=frame
    o.data.materials.append(material);return o

def badge(name,parent,frame,width,height,tagline='AMARDEEP ENTERPRISE'):
    # Supplied photographic nameplates are independent editable meshes.
    if bpy.data.objects.get('PR_'+name+'_Exact'):return
    label_plate(name+'_Backing',parent,frame,(width,height),paper)
    word=text_label(name+'_Wordmark','Micro',parent,frame,(0,height*.10,.00025),height*.64,ink)
    if not word.get('PR_wordmark_done'):
        word.data.materials.append(labelred)
        for j in (1,2,3):word.data.body_format[j].material_index=1
        word['PR_wordmark_done']=True
    for old in ('_M','_icr','_o'):
        ob=bpy.data.objects.get('PR_'+name+old)
        if ob:bpy.data.objects.remove(ob,do_unlink=True)
    text_label(name+'_Manufacturer',tagline,parent,frame,(0,-height*.30,.00025),height*.12,ink)

def add_labels():
    def pfm(u,v):return Matrix.Translation(Vector(panel_base(u,v))+Vector((0,0,.0006)))
    for n,u,v,word in [('R',.42,.85,'R-PHASE'),('Y',.56,.85,'Y-PHASE'),('B',.70,.85,'B-PHASE'),
                       ('Green',.70,.62,'START'),('Red_Start',.56,.39,'START'),('Red_Stop',.70,.39,'STOP')]:
        fr=pfm(u,v);label_plate('Control_'+n,panel,fr@Matrix.Translation((0,.008,0)),(.035,.039),ink)
        text_label('Control_'+n+'_Text',word,panel,fr,(0,.024,.0004),.0046,paper)
    for j,u in enumerate((.42,.56)):
        fr=pfm(u,.62);label_plate(f'Selector_{j}',panel,fr@Matrix.Translation((0,.008,0)),(.040,.039),ink)
        text_label(f'Selector_{j}_Off','OFF',panel,fr,(-.012,.024,.0004),.0045,paper)
        text_label(f'Selector_{j}_On','ON',panel,fr,(.012,.024,.0004),.0045,paper)
    fr=pfm(.42,.39)
    for word,angles in [('EMERGENCY',range(160,-1,-18)),('STOP',range(235,306,23))]:
        for j,(ch,deg) in enumerate(zip(word,angles)):
            a=math.radians(deg);p=Vector((.0235*math.cos(a),.0235*math.sin(a),.0045))
            f=fr@Matrix.Translation(p)@Matrix.Rotation(a-math.pi/2 if word=='EMERGENCY' else a+math.pi/2,4,'Z')
            text_label(f'Emergency_{word}_{j}',ch,panel,f,(0,0,0),.0034,ink)
    fr=pfm(.855,.62)
    for j in range(11):
        a=math.radians(225-j*27)
        text_label(f'Speed_{j}',str(j*10),panel,fr,(.0205*math.cos(a),.0205*math.sin(a),.004),.0028,paper)
    text_label('Speed_Word','SPEED',panel,fr,(0,-.019,.0042),.003,paper)
    fr=pfm(.18,.72)
    text_label('Timer_Make','MULTISPAN',panel,fr,(0,-.033,.010),.004,paper)
    text_label('Timer_Type','Quadra I',panel,fr,(-.021,-.025,.010),.003,paper)
    text_label('Timer_Min','MIN',panel,fr,(-.031,.035,.010),.0026,paper)
    text_label('Timer_Sec','SEC',panel,fr,(.029,.035,.010),.0026,paper)
    badge('Console_Panel_Badge',panel,pfm(.65,.20),.126,.046)
    # Console fascia: forward-facing surface -Y, with outward normal.
    lo,hi=rb('Console_Projecting_Upper_Housing')
    badge('Console_Fascia_Badge',root,Matrix.Translation((0,lo.y-.0007,.528))@FRONT,.245,.063,'Lapping Machine')
    # Photograph 5 / 4 side badge is on operator-left (-X).
    basis=Matrix(((0,0,-1,0),(-1,0,0,0),(0,1,0,0),(0,0,0,1)))
    badge('Cabinet_Left_Badge',root,Matrix.Translation((-.507,0,.493))@basis,.20,.059,'Lapping Machine')
    badge('Front_Beam_Badge',root,Matrix.Translation((0,-.611,1.103))@FRONT,.15,.074)
    # Gauge local X is operator-left viewed from the rear: world -X, local Y world +Z.
    gf=Matrix((( -1,0,0,.031),(0,0,1,ry+.026+.0128),(0,1,0,unit_z),(0,0,0,1)))
    for j in range(11):
        a=math.radians(-135+27*j)
        text_label(f'Gauge_Bar_{j}',str(j),root,gf,(.025*math.sin(a),.025*math.cos(a),0),.0027,ink)
    for j,value in enumerate((0,25,50,75,100,125,150)):
        a=math.radians(-135+45*j)
        text_label(f'Gauge_Psi_{value}',str(value),root,gf,(.0175*math.sin(a),.0175*math.cos(a),.00005),.003,labelred)
    text_label('Gauge_Brand','JANATICS',root,gf,(0,.0065,.0001),.0035,labelblue)
    text_label('Gauge_Psi','psi',root,gf,(0,-.010,.0001),.0033,labelred)
    text_label('Gauge_Bar','bar',root,gf,(0,-.015,.0001),.0033,ink)
    text_label('Gauge_Origin','MADE IN INDIA',root,gf,(0,-.022,.0001),.0022,ink)
    lf=gf.copy();lf.translation=Vector((-.031,ry+.0169,unit_z-.004))
    label_plate('Lubricator_Sticker',root,lf,(.037,.019),paper)
    text_label('Lubricator_Brand','JANATICS',root,lf,(0,.004,.0003),.0035,labelblue)
    text_label('Lubricator_Name','LUBRICATOR',root,lf,(0,-.003,.0003),.0031,ink)

presentation_materials();add_labels()
count_labels=set(labels.objects.keys());add_labels();assert count_labels==set(labels.objects.keys())
if not scene.get('PR_gauge_spacing_checked'):
    for j in range(11):
        o=bpy.data.objects[f'PR_Gauge_Bar_{j}'];a=math.radians(-135+27*j)
        o.location=Vector((.031-.025*math.sin(a),ry+.026+.0128,unit_z+.025*math.cos(a)))
        o.data.size=.0027
    scene['PR_gauge_spacing_checked']=True
# Reduce broad specular wash on printing and colored controls, one time only.
if not scene.get('PR_contrast_reviewed'):
    for m in (ink,paper,labelred,labelblue):
        bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Specular IOR Level'].default_value=0
    for name in ('CC_Material_Red','CC_Material_Yellow','CC_Material_Blue','CC_Material_Green','PN_Material_Air_Blue'):
        bpy.data.materials[name].node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value=.23
    scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.25
    scene['PR_contrast_reviewed']=True
if not scene.get('PR_metal_glare_checked'):
    m=bpy.data.materials['LM_Dark_Metal'];bs=m.node_tree.nodes['Principled BSDF']
    bs.inputs['Metallic'].default_value=.62
    for n in m.node_tree.nodes:
        if n.type=='MAP_RANGE':
            n.inputs['To Min'].default_value=.435;n.inputs['To Max'].default_value=.485
    scene['PR_metal_glare_checked']=True
# Upgrade the existing presentation objects only once, retaining later manual edits.
if not scene.get('PR_studio_finished'):
    bg=scene.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.65,.68,.72,1);bg.inputs['Strength'].default_value=.22
    for name,energy,size,loc in [('LM_Key',520,3.0,(-2,-3,3.8)),('LM_Fill',260,3.0,(3,-1,2.7)),('LM_Rim',560,2.6,(1,3,3.5))]:
        o=bpy.data.objects[name];o.location=loc;o.data.energy=energy;o.data.color=(1,1,1);o.data.shape='DISK';o.data.size=size
        o.rotation_euler=(Vector((0,0,.7))-o.location).to_track_quat('-Z','Y').to_euler()
    scene.view_settings.view_transform='AgX';scene.view_settings.exposure=0
    for name,loc,aim,lens in [
        ('MD_Preview_Complete',(-2.65,-3.35,2.65),(0,-.19,.69),55),
        ('PN_Preview_Regulator_Side',(2.6,3.3,2.6),(0,-.16,.70),55),
        ('MD_Preview_Working',(-1.38,.46,1.09),(0,0,.91),57),
        ('CC_Preview_Console',(-.82,-1.85,1.22),(0,-.84,.40),57)]:
        o=bpy.data.objects[name];o.location=world(loc);o.rotation_euler=(world(aim)-o.location).to_track_quat('-Z','Y').to_euler()
        o.data.type='PERSP';o.data.lens=lens;o.data.clip_start=.01;o.data.clip_end=200
        for c in list(o.users_collection):c.objects.unlink(o)
        pres.objects.link(o)
    scene['PR_studio_finished']=True
full=bpy.data.objects['MD_Preview_Complete'];close=bpy.data.objects['MD_Preview_Working']
opposite=bpy.data.objects['PN_Preview_Regulator_Side'];consolecam=bpy.data.objects['CC_Preview_Console']
if not scene.get('PR_framing_reviewed'):
    full.location=world((-3.276608,-2.294306,2.306105))
    full.rotation_euler=(world((0,-.19,.64))-full.location).to_track_quat('-Z','Y').to_euler();full.data.lens=70
    opposite.rotation_euler=(world((0,-.16,.64))-opposite.location).to_track_quat('-Z','Y').to_euler();opposite.data.lens=70
    scene['PR_framing_reviewed']=True
scene.camera=full;scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True
# Prefer the available NVIDIA device; fall back without altering geometry.
try:
    cp=bpy.context.preferences.addons['cycles'].preferences;cp.compute_device_type='CUDA';cp.get_devices()
    for device in cp.devices:device.use=(device.type=='CUDA')
    scene.cycles.device='GPU' if any(d.type=='CUDA' for d in cp.devices) else 'CPU'
except Exception:scene.cycles.device='CPU'
scene.render.resolution_x=1600;scene.render.resolution_y=1600;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
for o in bpy.data.objects:
    if o.type in {'CAMERA','LIGHT'}:o.hide_set(True)
for scr in bpy.data.screens:
    for area in scr.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active;sp.shading.type='MATERIAL';sp.overlay.show_overlays=False
            sp.overlay.show_extras=False;sp.overlay.show_relationship_lines=False
            sp.region_3d.view_rotation=full.rotation_euler.to_quaternion();sp.region_3d.view_location=world((0,-.19,.69))
            sp.region_3d.view_distance=3.25;sp.region_3d.view_perspective='PERSP'
bpy.ops.object.select_all(action='DESELECT')
# Control labels remain editable fonts; supplied nameplates use packed original artwork.
for img in bpy.data.images:
    if img.source=='FILE' and img.has_data and not img.packed_file:img.pack()
import runpy
runpy.run_path(os.path.join(FOLDER,'console_contact.py'))['apply']()
if bpy.context.scene.get('CI_inner_shroud'):
    runpy.run_path(os.path.join(FOLDER,'cabinet_inner_shroud.py'))['apply']()
if bpy.context.scene.get('PN_FRL_front_operator_mount'):
    runpy.run_path(os.path.join(FOLDER,'relocate_frl.py'))['apply']()
if bpy.context.scene.get('NP_three_cabinet_badges'):
    runpy.run_path(os.path.join(FOLDER,'cabinet_nameplates.py'))['apply']()
if bpy.context.scene.get('BM_blue_machine_palette'):
    runpy.run_path(os.path.join(FOLDER,'blue_machine_materials.py'))['apply']()
if bpy.context.scene.get('BM_working_parts_photo_match'):
    runpy.run_path(os.path.join(FOLDER,'match_blue_working_parts.py'))['apply']()
versions=bpy.context.preferences.filepaths.save_version;bpy.context.preferences.filepaths.save_version=0
text=bpy.data.texts.get('LM_GENERATION_SCRIPT') or bpy.data.texts.new('LM_GENERATION_SCRIPT')
text.clear();text.write(open(__file__,encoding='utf-8').read())
bpy.ops.wm.save_as_mainfile(filepath=WORKING,check_existing=False)
bpy.context.preferences.filepaths.save_version=versions
if RENDER:
    for cam,filename in [(consolecam,'finished_console.png'),(full,'finished_front.png'),(opposite,'finished_opposite.png'),(close,'finished_working.png')]:
        if '--only-console' in sys.argv and cam!=consolecam:continue
        if '--only-overviews' in sys.argv and cam not in (full,opposite):continue
        scene.camera=cam;scene.render.filepath=os.path.join(FOLDER,filename);bpy.ops.render.render(write_still=True)
    scene.camera=full
print('PRESENTATION_OK',len(labels.objects),'editable label objects; no external label images')

