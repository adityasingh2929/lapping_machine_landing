"""Lapping machine exterior blockout. Target: Blender 5.2 (bpy).
Revision v02. Run: blender --background --python generate_blockout_v02.py
Only the LM_BLOCKOUT collection is rebuilt; unrelated objects are preserved.
All dimensions are provisional metres, with cabinet width = 1.0.
"""
import bpy
import math
import os
import json
from mathutils import Vector

# ---------------- ALL MAIN CONFIGURATION ----------------
C = dict(
    cabinet_width=1.0, cabinet_depth=1.02, cabinet_bottom=0.09,
    cabinet_top=0.65, panel_thickness=0.012,
    frame_height=0.055, frame_rail=0.045,
    foot_width=0.085, foot_depth=0.085, foot_height=0.035,
    table_width=1.08, table_depth=1.08, table_top=0.735,
    table_thickness=0.014, table_clip=0.045, spacer_radius=0.012,
    plate_diameter=0.73, plate_thickness=0.012, lower_body_diameter=0.79,
    lower_body_bottom=0.652,
    # Explicit XY positions, shared by ALL station components.
    stations=[(0.0,-0.190),(-0.164545,0.095),(0.164545,0.095)],
    ring_diameter=0.29, ring_wall=0.018, ring_height=0.075,
    roller_diameter=0.035, roller_height=0.044,
    bracket_thickness=0.014, bracket_width=0.047,
    head_diameter=0.270, head_disk_thickness=0.026,
    head_clearance=0.125, head_step_diameter=0.19, head_step_height=0.023,
    head_flange_diameter=0.115, head_flange_height=0.009,
    head_hub_diameter=0.061, head_hub_height=0.038, shaft_diameter=0.025,
    column_spacing=1.15, column_width=0.085, column_depth=0.07,
    column_bottom=0.11, shaft_exposed_length=0.030, beam_height=0.085,
    beam_width=0.115, branch_width=0.145, station_mount_width=0.205,
    station_mount_depth=0.190, station_mount_thickness=0.012,
    cap_width=0.17, cap_depth=0.13, cap_thickness=0.012,
    cylinder_diameter=0.065, cylinder_height=0.255,
    cylinder_cap_width=0.080, cylinder_cap_height=0.018, tie_rod_radius=0.0025,
    console_position=(0.0,-0.84), console_width=0.56, console_depth=0.34,
    console_bottom=0.035, console_body_top=0.53,
    console_housing_width=0.59, console_housing_depth=0.40,
    console_housing_offset_y=-0.025,
    console_housing_bottom=0.515, console_front_top=0.57, console_rear_top=0.655,
    console_panel_thickness=0.010,
    bevel=0.002, render_resolution=1100, render_samples=96,
)
# Support elevations follow the complete head stack, not a stretched head/cylinder.
C['beam_bottom'] = (C['table_top'] + C['plate_thickness'] + C['ring_height']
    + C['head_clearance'] + C['head_disk_thickness'] + C['head_step_height']
    + C['head_flange_height'] + C['head_hub_height'] + C['shaft_exposed_length']
    + C['station_mount_thickness'])
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
PREVIEW_DIR = os.path.join(OUTPUT_DIR,'previews_v02')
GENERATED = 'LM_BLOCKOUT'
RENDER = True
SAVE = True

# ---------------- OWNED SCENE DATA ----------------
def remove_collection(col):
    for child in list(col.children):
        remove_collection(child)
    for obj in list(col.objects):
        # Unlink shared objects rather than removing them from unrelated collections.
        if len(obj.users_collection) > 1:
            col.objects.unlink(obj)
        else:
            bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(col)

old = bpy.data.collections.get(GENERATED)
if old:
    remove_collection(old)
owned = bpy.data.collections.new(GENERATED)
bpy.context.scene.collection.children.link(owned)
groups = {}
for name in ['00_ROOT','01_CABINET','02_TABLE','03_WORKING','04_HEADS',
             '05_CYLINDERS','06_SUPPORT_PROVISIONAL','07_CONSOLE','08_PRESENTATION']:
    col = bpy.data.collections.new(name)
    owned.children.link(col)
    groups[name] = col
root = bpy.data.objects.new('LM_ROOT_Move_Complete_Machine', None)
groups['00_ROOT'].objects.link(root)
root['coordinates'] = 'Front -Y; rear +Y; right +X; Z up'
root['scale_note'] = '1 metre cabinet width is a convention, NOT a measured dimension'
root['configuration'] = json.dumps(C)
root['beam_status'] = 'Provisional spine and station branches; concealed joints not verified'
root['revision'] = 'v02: clearance, console, mounting plates and review lighting'

def material(name, color, metallic=0.0, roughness=0.45):
    name = 'LM_v02_' + name
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color,1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color,1)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    return mat

grey = material('Grey_Paint',(0.20,0.235,0.26),0.0,0.48)
cream = material('Cream_Paint',(0.74,0.65,0.43),0.0,0.48)
dark = material('Dark_Metal',(0.022,0.027,0.032),0.18,0.48)
silver = material('Silver',(0.53,0.57,0.62),0.72,0.32)
floor_mat = material('Studio',(0.12,0.145,0.175))
floor_bsdf=floor_mat.node_tree.nodes.get('Principled BSDF')
floor_bsdf.inputs['Emission Color'].default_value=(.18,.20,.23,1)
floor_bsdf.inputs['Emission Strength'].default_value=.8

def finish(obj,name,group,mat,bevel=True,parent=True):
    obj.name = name
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    groups[group].objects.link(obj)
    if parent:
        obj.parent=root
    obj.data.materials.append(mat)
    if bevel:
        mod=obj.modifiers.new('Modest edge bevel','BEVEL')
        mod.width=C['bevel']; mod.segments=2
        mod=obj.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    return obj

def box(name,loc,size,group,mat=grey):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    obj=bpy.context.object
    obj.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(obj,name,group,mat)

def cylinder(name,xy,z0,z1,r,group,mat=dark):
    bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=r,depth=z1-z0,
                                      location=(*xy,(z0+z1)/2))
    return finish(bpy.context.object,name,group,mat)

def prism(name,outline,z0,z1,group,mat=grey):
    n=len(outline)
    verts=[(x,y,z) for z in [z0,z1] for x,y in outline]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(verts,[],faces); mesh.update()
    obj=bpy.data.objects.new(name,mesh); groups[group].objects.link(obj)
    return finish(obj,name,group,mat)

def hollow_ring(name,xy,z0):
    n=128; ro=C['ring_diameter']/2; ri=ro-C['ring_wall']; h=C['ring_height']
    verts=[]
    for radius,z in [(ro,z0),(ro,z0+h),(ri,z0),(ri,z0+h)]:
        verts += [(xy[0]+radius*math.cos(i*2*math.pi/n),
                   xy[1]+radius*math.sin(i*2*math.pi/n),z) for i in range(n)]
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,j,n+j,n+i),(2*n+j,2*n+i,3*n+i,3*n+j),
                      (n+i,n+j,3*n+j,3*n+i),(j,i,2*n+i,2*n+j)])
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(verts,[],faces); mesh.update()
    obj=bpy.data.objects.new(name,mesh); groups['03_WORKING'].objects.link(obj)
    return finish(obj,name,'03_WORKING',dark)

# ---------------- CABINET AND TABLE ----------------
w=C['cabinet_width']; d=C['cabinet_depth']; low=C['cabinet_bottom']; high=C['cabinet_top']
p=C['panel_thickness']; g='01_CABINET'
for y,side in [(-d/2,'Front'),(d/2,'Rear')]:
    box('Panel_'+side,(0,y,(low+high)/2),(w-0.025,p,high-low-0.014),g)
for x,side in [(-w/2,'Left'),(w/2,'Right')]:
    box('Panel_'+side,(x,0,(low+high)/2),(p,d-0.025,high-low-0.014),g)
for x in [-w/2+0.018,w/2-0.018]:
    for y in [-d/2+0.018,d/2-0.018]:
        box('Cabinet_Corner_Post', (x,y,(low+high)/2),(.035,.035,high-low),g)
        box('Mounting_Foot',(x*1.05,y*1.05,C['foot_height']/2),
            (C['foot_width'],C['foot_depth'],C['foot_height']),g)
for z in [low-C['frame_height']/2,high-0.018]:
    for y in [-d/2+.025,d/2-.025]:
        box('Frame_X_Rail',(0,y,z),(w-.05-C['frame_rail'],C['frame_rail'],C['frame_height']),g)
    for x in [-w/2+.025,w/2-.025]:
        box('Frame_Y_Rail',(x,0,z),(C['frame_rail'],d,C['frame_height']),g)

g='02_TABLE'; tx=C['table_width']/2; ty=C['table_depth']/2; cut=C['table_clip']
outline=[(-tx+cut,-ty),(tx-cut,-ty),(tx,-ty+cut),(tx,ty-cut),
         (tx-cut,ty),(-tx+cut,ty),(-tx,ty-cut),(-tx,-ty+cut)]
table_bottom=C['table_top']-C['table_thickness']
prism('Tabletop_Clipped_Corners',outline,table_bottom,C['table_top'],g)
for x in [-0.40,0.40]:
    for y in [-0.40,0.40]:
        cylinder('Table_Spacer',(x,y),high,table_bottom,C['spacer_radius'],g,silver)
        cylinder('Spacer_Pad',(x,y),table_bottom-.007,table_bottom,.023,g,grey)
cylinder('Exposed_Under_Table_Drum',(0,0),C['lower_body_bottom'],table_bottom,.5*C['lower_body_diameter'],'03_WORKING')
plate_top=C['table_top']+C['plate_thickness']
cylinder('Circular_Working_Plate',(0,0),C['table_top'],plate_top,C['plate_diameter']/2,'03_WORKING')

# ---------------- THREE SHARED STATIONS ----------------
ring_top=plate_top+C['ring_height']
head_bottom=ring_top+C['head_clearance']
mount_bottom=C['beam_bottom']-C['station_mount_thickness']
beam_top=C['beam_bottom']+C['beam_height']
for i,xy in enumerate(C['stations'],1):
    x,y=xy; prefix=f'S{i}_'
    hollow_ring(prefix+'Hollow_Ring',xy,plate_top)
    # Two external contacts on each ring's outward-facing arc.
    angle=math.atan2(y,x)
    contacts=[]
    for j,offset in enumerate([-0.65,0.65],1):
        a=angle+offset
        r=(C['ring_diameter']+C['roller_diameter'])/2+.001
        pt=(x+r*math.cos(a),y+r*math.sin(a)); contacts.append(pt)
        cylinder(prefix+f'Roller_{j}',pt,plate_top+.018,plate_top+.018+C['roller_height'],C['roller_diameter']/2,'03_WORKING',silver)
    # Concave bracket follows the outside wall, avoiding a chord through the ring.
    inner=C['ring_diameter']/2+.002
    outer=inner+C['bracket_width']
    arc=[angle-.82+k*1.64/20 for k in range(21)]
    outline=[(x+outer*math.cos(a),y+outer*math.sin(a)) for a in arc]
    outline += [(x+inner*math.cos(a),y+inner*math.sin(a)) for a in reversed(arc)]
    prism(prefix+'Roller_Bracket',outline,plate_top+.004,plate_top+.018,'03_WORKING',dark)
    mid=(x+(outer-.01)*math.cos(angle),y+(outer-.01)*math.sin(angle))
    # Support is radially outside the working disk, and reaches up to bracket.
    outer_r=C['plate_diameter']/2+.025
    support=(outer_r*math.cos(angle),outer_r*math.sin(angle))
    support_box=box(prefix+'Bracket_Support',(*support,(C['table_top']+plate_top+.014)/2),(.075,.05,plate_top+.014-C['table_top']),'03_WORKING',dark)
    support_box.rotation_euler.z=angle
    arm_length=math.dist(mid,support)+.035
    arm=box(prefix+'Bracket_Radial_Arm',((mid[0]+support[0])/2,(mid[1]+support[1])/2,plate_top+.009),(arm_length,.035,C['bracket_thickness']),'03_WORKING',dark)
    arm.rotation_euler.z=angle
    z=head_bottom
    for suffix,diameter,height in [('Lower_Disk',C['head_diameter'],C['head_disk_thickness']),
                                 ('Raised_Step',C['head_step_diameter'],C['head_step_height']),
                                 ('Flange',C['head_flange_diameter'],C['head_flange_height']),
                                 ('Hub',C['head_hub_diameter'],C['head_hub_height'])]:
        cylinder(prefix+'Head_'+suffix,xy,z,z+height,diameter/2,'04_HEADS'); z+=height
    assert z<mount_bottom, 'Head hub exceeds mounting plate: adjust clearance or beam height'
    cylinder(prefix+'Aligned_Shaft',xy,z,mount_bottom,C['shaft_diameter']/2,'04_HEADS',silver)
    box(prefix+'Underside_Mount',(*xy,(mount_bottom+C['beam_bottom'])/2),
        (C['station_mount_width'],C['station_mount_depth'],C['station_mount_thickness']),'04_HEADS',dark)
    cap=C['cylinder_cap_height']; cyl_top=beam_top+C['cylinder_height']
    cylinder(prefix+'Cylinder_Body',xy,beam_top+cap,cyl_top-cap,C['cylinder_diameter']/2,'05_CYLINDERS',silver)
    for zc in [beam_top+cap/2,cyl_top-cap/2]:
        box(prefix+'Cylinder_End_Cap',(*xy,zc),(C['cylinder_cap_width'],C['cylinder_cap_width'],cap),'05_CYLINDERS',silver)
    r=C['cylinder_cap_width']*.39
    for dx in [-r,r]:
        for dy in [-r,r]:
            cylinder(prefix+'Cylinder_Tie_Rod',(x+dx,y+dy),beam_top+cap,cyl_top-cap,C['tie_rod_radius'],'05_CYLINDERS',silver)

# ---------------- PROVISIONAL STRUCTURAL CONNECTIONS ----------------
g='06_SUPPORT_PROVISIONAL'
col_top=C['beam_bottom']-C['cap_thickness']
for y,name in [(-C['column_spacing']/2,'Front'),(C['column_spacing']/2,'Rear')]:
    box(name+'_Centerline_Column',(0,y,(C['column_bottom']+col_top)/2),
        (C['column_width'],C['column_depth'],col_top-C['column_bottom']),g)
    box(name+'_Column_Cap',(0,y,(col_top+C['beam_bottom'])/2),
        (C['cap_width'],C['cap_depth'],C['cap_thickness']),g)
    # Exterior bracket bridges column to cabinet; hidden bolt details omitted.
    box(name+'_Lower_Attachment',(0,y*.94,.22),(.19,.075,.20),g)
box('PROVISIONAL_Longitudinal_Spine',(0,0,(C['beam_bottom']+beam_top)/2),
    (C['beam_width'],C['column_spacing']+C['column_depth'],C['beam_height']),g)
for i,(x,y) in enumerate(C['stations'],1):
    if abs(x)>1e-6:
        sign=1 if x>0 else -1
        start=sign*C['beam_width']/2
        end=x+sign*C['station_mount_width']/2
        box(f'PROVISIONAL_S{i}_Lateral_Branch',((start+end)/2,y,(C['beam_bottom']+beam_top)/2),
            (abs(end-start),C['branch_width'],C['beam_height']),g)

# ---------------- CONSOLE ----------------
g='07_CONSOLE'; cx,cy=C['console_position']
box('Console_Lower_Cabinet',(cx,cy,(C['console_bottom']+C['console_body_top'])/2),
    (C['console_width'],C['console_depth'],C['console_body_top']-C['console_bottom']),g)
box('Console_Cream_Front_Door',(cx,cy-C['console_depth']/2-.005,.265),
    (C['console_width']-.022,.012,.44),g,cream)
for x in [cx-C['console_width']/2+.025,cx+C['console_width']/2-.025]:
    box('Console_Floor_Rail',(x,cy,.012),(.045,C['console_depth']+.055,.024),g)
hw=C['console_housing_width']/2; hd=C['console_housing_depth']/2
housing_y=cy+C['console_housing_offset_y']
zf=C['console_front_top']; zr=C['console_rear_top']; zb=C['console_housing_bottom']
verts=[(cx-hw,housing_y-hd,zb),(cx+hw,housing_y-hd,zb),(cx+hw,housing_y+hd,zb),(cx-hw,housing_y+hd,zb),
       (cx-hw,housing_y-hd,zf),(cx+hw,housing_y-hd,zf),(cx+hw,housing_y+hd,zr),(cx-hw,housing_y+hd,zr)]
mesh=bpy.data.meshes.new('Console_Wedge');mesh.from_pydata(verts,[],[(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]);mesh.update()
obj=bpy.data.objects.new('Console_Projecting_Upper_Housing',mesh);groups[g].objects.link(obj)
finish(obj,obj.name,g,grey)
slope=math.atan2(zr-zf,2*hd)
panel=box('Console_Sloping_Cream_Panel',(cx,housing_y,(zf+zr)/2+C['console_panel_thickness']/2),
    (2*hw,math.hypot(2*hd,zr-zf),C['console_panel_thickness']),g,cream)
panel.rotation_euler.x=slope

# ---------------- NUMERICAL CHECKS ----------------
checks=[]
for i,xy in enumerate(C['stations']):
    edge=math.hypot(*xy)+C['ring_diameter']/2
    assert edge<C['plate_diameter']/2, 'Ring extends beyond working plate'
    checks.append(f'S{i+1} plate edge margin: {C["plate_diameter"]/2-edge:.5f} m')
    for j in range(i):
        gap=math.dist(xy,C['stations'][j])-C['ring_diameter']
        assert gap>0, 'Rings intersect'
        checks.append(f'S{j+1}-S{i+1} ring gap: {gap:.5f} m')
    for suffix in ['Head_Lower_Disk','Aligned_Shaft','Cylinder_Body']:
        obj=bpy.data.objects[f'S{i+1}_'+suffix]
        assert math.dist(obj.location[:2],xy)<1e-6, 'Station alignment failure'
assert C['head_clearance']>0
assert C['column_spacing']/2-C['column_depth']/2>=C['table_depth']/2-1e-8
assert housing_y+C['console_housing_depth']/2 < -C['column_spacing']/2-C['column_depth']/2
checks += [f'Head clearance: {C["head_clearance"]:.5f} m',
           'All head/shaft/cylinder XY centers checked against shared station positions.',
           'Columns outside tabletop; console clears front column.',
           'Upper connections are provisional, not verified concealed fabrication.']

# ---------------- CAMERAS, LIGHTS, SAVE AND RENDER ----------------
scene=bpy.context.scene
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
scene.render.engine='BLENDER_EEVEE'
scene.eevee.taa_render_samples=C['render_samples']
scene.eevee.shadow_ray_count=3
scene.render.resolution_x=C['render_resolution'];scene.render.resolution_y=C['render_resolution']
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene.view_settings.exposure=-0.25
world=bpy.data.worlds.get('LM_v02_Studio_World') or bpy.data.worlds.new('LM_v02_Studio_World')
world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.26,.32,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.8
scene.world=world
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.001))
floor=finish(bpy.context.object,'Studio_Floor','08_PRESENTATION',floor_mat,bevel=False,parent=False)
target=Vector((0,-.22,.72))

def camera(name,location,aim,kind='PERSP',lens=52,scale=2.15):
    data=bpy.data.cameras.new(name);data.type=kind;data.lens=lens;data.ortho_scale=scale
    data.clip_start=.01;data.clip_end=200
    obj=bpy.data.objects.new(name,data);groups['08_PRESENTATION'].objects.link(obj)
    obj.location=location
    obj.rotation_euler=(Vector(aim)-obj.location).to_track_quat('-Z','Y').to_euler()
    return obj

cams=[]
# Orthographic checks, plus photo-like perspective views. Coordinates remain fixed.
cams.append(camera('V02_Ortho_Front',(0,-5,.72),target,'ORTHO',scale=2.12))
cams.append(camera('V02_Ortho_Side',(-5,-.22,.72),target,'ORTHO',scale=2.12))
cams.append(camera('V02_Ortho_Top',(0,-.22,5),target,'ORTHO',scale=2.12))
cams.append(camera('V02_Perspective_Front_11',(0,-3.8,1.15),target,lens=55))
cams.append(camera('V02_Perspective_Side_5',(-3.8,-.18,1.15),target,lens=55))
cams.append(camera('V02_ThreeQuarter_Front_10',(2.20,-2.95,1.42),target,lens=52))
cams.append(camera('V02_ThreeQuarter_Rear_6',(-2.40,2.85,1.35),target,lens=52))
close=camera('V02_Closeup_16',(-1.12,-.22,1.005),(0,0,.940),lens=52)
cams.append(close)
# Check complete-machine framing against actual world-space geometry bounds.
from bpy_extras.object_utils import world_to_camera_view
bpy.context.view_layer.update()
bounds=[obj.matrix_world @ Vector(corner)
        for col in groups.values() if col != groups['08_PRESENTATION']
        for obj in col.objects if obj.type=='MESH' for corner in obj.bound_box]
for cam in cams[:-1]:
    for attempt in range(30):
        projected=[world_to_camera_view(scene,cam,v) for v in bounds]
        if all(.055 < v.x < .945 and .055 < v.y < .945 and v.z>0 for v in projected):
            break
        if cam.data.type=='ORTHO': cam.data.ortho_scale *= 1.05
        else: cam.location=target+(cam.location-target)*1.05
        bpy.context.view_layer.update()
    else: raise AssertionError('Camera cannot frame complete machine: '+cam.name)
    checks.append(cam.name+': complete-machine bounds within 5.5% frame margins')
for name,loc,power,size in [('Key',(1.8,-2.3,3.3),180,2.0),
                            ('Fill',(-2.3,-.6,2.0),70,2.5),
                            ('Rim',(.7,2.5,2.8),140,1.8)]:
    data=bpy.data.lights.new('LM_v02_'+name,'AREA'); data.energy=power;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new('LM_v02_'+name,data);groups['08_PRESENTATION'].objects.link(obj)
    obj.location=loc;obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()

os.makedirs(PREVIEW_DIR,exist_ok=True)
with open(os.path.join(OUTPUT_DIR,'blockout_v02_checks.txt'),'w') as f:
    f.write('\n'.join(checks))
text=bpy.data.texts.get('LM_GENERATION_SCRIPT_V02') or bpy.data.texts.new('LM_GENERATION_SCRIPT_V02')
text.clear()
with open(__file__,encoding='utf-8') as f:text.write(f.read())

# Viewport-only hiding retains all presentation objects for rendering.
def setup_review_view():
    scene.camera=cams[5]
    bpy.ops.object.select_all(action='DESELECT')
    for obj in groups['08_PRESENTATION'].objects:
        obj.hide_set(True)
        obj.hide_render=False
    root.hide_set(True)  # hide only the empty's marker; children remain visible
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active
                space.shading.type='MATERIAL'
                space.shading.use_scene_world=False
                space.shading.use_scene_lights=False
                space.shading.studiolight_rotate_z=.6
                space.shading.studiolight_intensity=.8
                space.overlay.show_extras=False
                space.overlay.show_relationship_lines=False
                space.overlay.show_floor=False
                space.overlay.show_axis_x=False;space.overlay.show_axis_y=False
                space.region_3d.view_rotation=(target-Vector((2.2,-2.95,1.85))).to_track_quat('-Z','Y')
                space.region_3d.view_location=target
                space.region_3d.view_distance=3.0
                space.region_3d.view_perspective='PERSP'
                space.lens=50
    bpy.context.view_layer.update()

setup_review_view()
if SAVE:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTPUT_DIR,'lapping_machine_blockout_v02.blend'))
if RENDER:
    # Inspection priorities first, then the full comparison set.
    for cam in [close,cams[5],cams[6],*cams[:5]]:
        scene.camera=cam
        scene.render.resolution_x=1400 if cam==close else C['render_resolution']
        scene.render.resolution_y=1000 if cam==close else C['render_resolution']
        scene.render.filepath=os.path.join(PREVIEW_DIR,cam.name+'.png')
        bpy.ops.render.render(write_still=True)
    scene.render.resolution_x=C['render_resolution'];scene.render.resolution_y=C['render_resolution']
    setup_review_view()
    if SAVE:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTPUT_DIR,'lapping_machine_blockout_v02.blend'))
print('BLOCKOUT_V02_CHECKS_OK\n'+'\n'.join(checks))
