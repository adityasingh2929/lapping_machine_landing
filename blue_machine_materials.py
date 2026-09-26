"""Photo-based blue-machine palette. Materials only; existing geometry is retained."""
import bpy

def linear(hexcode):
    rgb=[int(hexcode[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb)+(1,)

def material(name,hexcode,metallic,roughness,coat=0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True
    bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    for key,val in [('Base Color',linear(hexcode)),('Metallic',metallic),('Roughness',roughness),('Coat Weight',coat),('Coat Roughness',.22)]:
        sock=bs.inputs.get(key)
        if sock:
            for link in list(sock.links):m.node_tree.links.remove(link)
            sock.default_value=val
    m.diffuse_color=linear(hexcode)
    m['sRGB_hex']='#'+hexcode
    return m

def assign(o,m):
    if o.data and hasattr(o.data,'materials'):
        if len(o.data.materials):o.data.materials[0]=m
        else:o.data.materials.append(m)

def apply():
    blue=material('BM_RAL_5002_Ultramarine_Gloss','00387B',0,.23,.28)
    blue['reference']='RAL 5002; digital sRGB approximation #00387B, https://www.colorxs.com/color/ral-5002-ultramarine-blue'
    frame=material('LM_Grey_Paint','829FA9',0,.3,.15)
    frame['reference']='Pale blue-grey structural frame estimated from blue_machine/2.jpeg and 9.jpeg'
    console=material('BM_Console_Blue','46658D',0,.32,.12)
    cream=material('LM_Cream_Paint','DBD3B7',0,.36,.12)
    matched=bpy.context.scene.get('BM_working_parts_photo_match',False)
    rings=material('BM_Conditioning_Ring_Warm_Steel','807464',.85,.42 if matched else .34)
    plate=material('BM_Lapping_Plate_Machined_Steel','949697',.9,.36 if matched else .3)
    heads=material('BM_Pressure_Heads_Blackened_Steel','292B2C',.65,.32)
    support=material('BM_Carriers_Dark_Steel','575957',.8,.36)
    for o in bpy.data.objects:
        n=o.name
        if n in ('Panel_Front','Panel_Rear','Panel_Left','Panel_Right','Tabletop_Clipped_Corners') or n.startswith(('MD_Panel_Left_Louver_Hood','MD_Panel_Right_Louver_Hood','Table_Spacer','Spacer_Pad','MD_Spacer_')):
            assign(o,blue)
        elif n.startswith(('Console_Lower_Cabinet','Console_Projecting_Upper_Housing','Console_Floor_Rail')):assign(o,console)
        elif n.endswith('_Hollow_Ring'):assign(o,rings)
        elif n=='Circular_Working_Plate':assign(o,plate)
        elif any(n==f'S{i}_{part}' for i in (1,2,3) for part in ('Head_Flange','Head_Hub','Head_Lower_Disk','Head_Raised_Step')):assign(o,heads)
        elif any(n==f'S{i}_{part}' for i in (1,2,3) for part in ('Roller_Bracket','Bracket_Radial_Arm','Bracket_Support')) or ('Bracket_Raised_Block' in n) or ('Bracket_Adjustment_Plate' in n):assign(o,support)
    material('PN_Material_Air_Blue','009FD1',0,.26)
    bpy.context.scene['BM_blue_machine_palette']=True

if __name__=='__main__':apply()
