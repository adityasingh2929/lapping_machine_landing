"""Exact photographic print extraction in shader space; no logo retypes or AI redraws.
Source photo homographies rectify the plate. Only classified ink/white lettering
contributes to the final material; the substrate is uniform neutral silver.
"""
import bpy, math, os, json, hashlib
import numpy as np
from mathutils import Vector, Matrix

FOLDER=os.path.dirname(os.path.abspath(__file__))
PREFIXES=('PR_Console_Panel_Badge','PR_Console_Fascia_Badge','PR_Front_Beam_Badge')

def material(index):
    name='NP_Exact_Plate_'+str(index)
    old=bpy.data.materials.get(name)
    m=old or bpy.data.materials.new(name);m.use_nodes=True
    nt=m.node_tree;nt.nodes.clear()
    def node(t):return nt.nodes.new(t)
    def setin(n,i,v):
        if hasattr(v,'is_output'):nt.links.new(v,n.inputs[i])
        else:n.inputs[i].default_value=v
    def op(kind,a,b=0):
        n=node('ShaderNodeMath');n.operation=kind;setin(n,0,a);setin(n,1,b);return n.outputs[0]
    def ramp(v,lo,hi):
        return op('MINIMUM',1,op('MAXIMUM',0,op('DIVIDE',op('SUBTRACT',v,lo),hi-lo)))
    def mix(f,a,b):
        n=node('ShaderNodeMixRGB');setin(n,0,f);setin(n,1,a);setin(n,2,b);return n.outputs[0]
    uv=node('ShaderNodeTexCoord');sep=node('ShaderNodeSeparateXYZ');nt.links.new(uv.outputs['UV'],sep.inputs[0]);u,v=sep.outputs[0],sep.outputs[1]
    # Four physical plate corners, measured in the displayed 1824 x 1368 source.
    corners=([(451,461),(1178,462),(1185,914),(445,914)] if index==1 else [(284,550),(1415,517),(1435,849),(289,894)])
    A=[];b=[]
    for (x,y),(px,py) in zip([(0,1),(1,1),(1,0),(0,0)],corners):
        X=px/1824;Y=1-py/1368
        A.extend([[x,y,1,0,0,0,-X*x,-X*y],[0,0,0,x,y,1,-Y*x,-Y*y]]);b.extend([X,Y])
    h=np.linalg.solve(np.array(A),np.array(b))
    def lin(a,b,c):return op('ADD',op('ADD',op('MULTIPLY',u,float(a)),op('MULTIPLY',v,float(b))),float(c))
    den=lin(h[6],h[7],1);vec=node('ShaderNodeCombineXYZ')
    setin(vec,0,op('DIVIDE',lin(*h[:3]),den));setin(vec,1,op('DIVIDE',lin(*h[3:6]),den))
    tex=node('ShaderNodeTexImage');tex.label='Original supplied plate; projective rectification'
    path=os.path.join(FOLDER,'..',f'plate_{index}.jpeg')
    tex.image=bpy.data.images.load(path,check_existing=True);tex.image.pack();nt.links.new(vec.outputs[0],tex.inputs[0])
    rgb=node('ShaderNodeSeparateColor');nt.links.new(tex.outputs['Color'],rgb.inputs[0])
    r,g,bl=rgb.outputs[:3]
    brightness=op('MAXIMUM',g,bl)
    if index==2:
        # Estimate local bare-metal brightness from neighboring source pixels.
        # A relative threshold recovers ink even across the photographed glare stripe.
        bg=brightness
        for dx,dy in [(0,-.008),(0,.008),(0,-.015),(0,.015)]:
            shift=node('ShaderNodeVectorMath');shift.operation='ADD';setin(shift,0,vec.outputs[0]);setin(shift,1,(dx,dy,0))
            sample=node('ShaderNodeTexImage');sample.image=tex.image;nt.links.new(shift.outputs[0],sample.inputs[0])
            channels=node('ShaderNodeSeparateColor');nt.links.new(sample.outputs[0],channels.inputs[0])
            bg=op('MAXIMUM',bg,op('MAXIMUM',channels.outputs[1],channels.outputs[2]))
        recovered=op('SUBTRACT',1,ramp(op('DIVIDE',brightness,op('MAXIMUM',bg,.01)),.15,.40))
        recovered=op('MULTIPLY',recovered,op('LESS_THAN',v,.24))
        ink=op('MAXIMUM',op('SUBTRACT',1,ramp(brightness,.015,.048)),recovered)
    else:ink=op('SUBTRACT',1,ramp(brightness,.015,.048))
    red=ramp(op('SUBTRACT',r,g),.015,.045)
    # Reject the physical rim and its reflected dark edges. Keep all printed pixels.
    inside=op('MULTIPLY',op('MULTIPLY',op('GREATER_THAN',u,.018 if index==1 else .10),op('LESS_THAN',u,.985 if index==1 else .90)),op('MULTIPLY',op('GREATER_THAN',v,.04),op('LESS_THAN',v,.96)))
    ink=op('MULTIPLY',ink,inside);red=op('MULTIPLY',red,inside)
    white=0
    if index==1:
        # White glyphs occur only inside the five original black specification boxes.
        boxes=0
        for a,b in [(.033,.201),(.227,.392),(.419,.583),(.610,.777),(.802,.970)]:
            q=op('MULTIPLY',op('GREATER_THAN',u,a),op('LESS_THAN',u,b));boxes=op('MAXIMUM',boxes,q)
        boxes=op('MULTIPLY',boxes,op('MULTIPLY',op('GREATER_THAN',v,.064),op('LESS_THAN',v,.153)))
        white=op('MULTIPLY',boxes,ramp(op('MAXIMUM',g,bl),.04,.18))
    color=mix(ink,(.003,.003,.003,1),(.003,.003,.003,1))
    color=mix(red,color,(.50,.003,.006,1));color=mix(white,color,(.92,.92,.92,1))
    printed=op('MAXIMUM',op('MAXIMUM',ink,red),white)
    color=mix(printed,(.55,.55,.55,1),color)
    bs=node('ShaderNodeBsdfPrincipled');setin(bs,'Base Color',color)
    setin(bs,'Metallic',op('SUBTRACT',1,printed));setin(bs,'Roughness',mix(printed,(.34,.34,.34,1),(.5,.5,.5,1)))
    bs.inputs['Specular IOR Level'].default_value=.22
    out=node('ShaderNodeOutputMaterial');nt.links.new(bs.outputs[0],out.inputs[0])
    m.diffuse_color=(.55,.55,.55,1);m['source']=f'plate_{index}.jpeg; original pixels, rectified UV, lighting-independent print mask'
    return m

def rounded_plate(name,frame,parent,w,h,mat):
    radius=.0012;t=.00065;verts=[]
    for z in (-t/2,t/2):
        for cx,cy,a in [(w/2-radius,h/2-radius,0),(-w/2+radius,h/2-radius,90),(-w/2+radius,-h/2+radius,180),(w/2-radius,-h/2+radius,270)]:
            for j in range(9):
                th=math.radians(a+j*90/8);verts.append((cx+radius*math.cos(th),cy+radius*math.sin(th),z))
    n=len(verts)//2;faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    uv=mesh.uv_layers.new(name='Rectified_Plate')
    for p in mesh.polygons:
        for li in p.loop_indices:
            co=mesh.vertices[mesh.loops[li].vertex_index].co;uv.data[li].uv=(co.x/w+.5,co.y/h+.5)
    ob=bpy.data.objects.new(name,mesh);bpy.data.collections['Labels_and_Badges'].objects.link(ob)
    ob.parent=parent;ob.matrix_world=frame;mesh.materials.append(mat)
    # Sidewalls have plain metal; only front face carries the print.
    silver=bpy.data.materials.get('NP_Silver_Edge')
    if not silver:
        silver=bpy.data.materials.new('NP_Silver_Edge');silver.use_nodes=True
        bs=next(n for n in silver.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(.55,.55,.55,1);bs.inputs['Metallic'].default_value=1;bs.inputs['Roughness'].default_value=.34
    mesh.materials.append(silver)
    for p in mesh.polygons:p.material_index=0 if p.index==1 else 1
    bevel=ob.modifiers.new('Small edge bevel','BEVEL');bevel.width=.00008;bevel.segments=3
    ob['nameplate_design']=mat.name;ob['aspect_ratio']=w/h;ob['thickness']=t
    return ob

def apply_nameplates():
    if all(bpy.data.objects.get(p+'_Exact') for p in PREFIXES):
        material(1);material(2)
        return
    for prefix,index,w in zip(PREFIXES,(1,2,2),(.105,.235,.15)):
        old=bpy.data.objects[prefix+'_Backing'];frame=old.matrix_world.copy();parent=old.parent
        # Preserve mount frames; normalize basis to prevent inherited scale stretching.
        loc,rot,scale=frame.decompose();frame=Matrix.LocRotScale(loc,rot,Vector((1,1,1)))
        frame.translation+=frame.to_3x3()@Vector((0,0,.00045))
        for ob in list(bpy.data.objects):
            if ob.name.startswith(prefix):bpy.data.objects.remove(ob,do_unlink=True)
        rounded_plate(prefix+'_Exact',frame,parent,w,w/(1.64 if index==1 else 3.38),material(index))
    bpy.context.view_layer.update()
    bpy.context.scene['NP_supplied_nameplates']='plate_1: sloped panel; plate_2: console fascia and vertical upper front mount'

def run():
    def signature(o):
        d={'matrix':[list(r) for r in o.matrix_world],'materials':[m.name for m in o.data.materials] if hasattr(o.data,'materials') else [],'hide':o.hide_render}
        if o.type=='MESH':d['vertices']=[list(v.co) for v in o.data.vertices]
        return hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
    before={o.name:signature(o) for o in bpy.data.objects if not o.name.startswith(PREFIXES)}
    apply_nameplates()
    assert all(signature(bpy.data.objects[n])==v for n,v in before.items())
    for name in ('generate_blockout.py','nameplates.py'):
        text=bpy.data.texts.get('LM_GENERATION_SCRIPT' if name.startswith('generate') else 'LM_NAMEPLATES_SCRIPT') or bpy.data.texts.new('LM_GENERATION_SCRIPT' if name.startswith('generate') else 'LM_NAMEPLATES_SCRIPT')
        text.clear();text.write(open(os.path.join(FOLDER,name),encoding='utf-8-sig').read())
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(FOLDER,'lapping_machine_blockout.blend'))
    json.dump({'protected_objects':before,'plates':[{'name':p+'_Exact','ratio':bpy.data.objects[p+'_Exact']['aspect_ratio']} for p in PREFIXES],'packed':[i.name for i in bpy.data.images if i.packed_file]},open(os.path.join(FOLDER,'nameplates_verification.json'),'w'),indent=2)
    print('NAMEPLATES_SAVED; all unrelated object signatures unchanged',flush=True)

if __name__=='__main__':run()
