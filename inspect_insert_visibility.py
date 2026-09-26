import bpy
from mathutils import Vector
dep=bpy.context.evaluated_depsgraph_get()
for x,y in ((0,-.17974),(.04,-.22),(-.04,-.25),(0,-.23),(.08,-.18)):
    hits=[]
    for o in bpy.data.objects:
        if o.type!='MESH' or o.hide_render:continue
        e=o.evaluated_get(dep);inv=e.matrix_world.inverted()
        hit,p,n,index=e.ray_cast(inv@Vector((x,y,.90)),(inv.to_3x3()@Vector((0,0,-1))).normalized(),distance=.25)
        if hit:hits.append((o.name,tuple(e.matrix_world@p)))
    print('RAY',x,y,sorted(hits,key=lambda a:-a[1][2])[:8])
