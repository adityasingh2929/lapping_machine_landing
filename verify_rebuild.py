"""Non-saving rebuild test; run in Blender after opening the blockout file."""
import bpy
import os
path=os.path.join(os.path.dirname(__file__),'generate_blockout.py')
sentinel=bpy.data.objects.new('UNRELATED_PRESERVATION_TEST',None)
bpy.context.scene.collection.objects.link(sentinel)
sentinel.location=(7,8,9)
before=len(bpy.data.collections['LM_BLOCKOUT'].all_objects)
source=open(path,encoding='utf-8').read().replace('RENDER = True','RENDER = False')
source=source.replace("bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTPUT_DIR,'lapping_machine_blockout.blend'))",'pass # verification does not save scene')
exec(compile(source,path,'exec'),{'__file__':path,'__name__':'__main__'})
assert bpy.data.objects.get(sentinel.name) is sentinel
assert tuple(sentinel.location)==(7.0,8.0,9.0)
after=len(bpy.data.collections['LM_BLOCKOUT'].all_objects)
assert before==after,(before,after)
assert len([c for c in bpy.data.collections if c.name=='LM_BLOCKOUT'])==1
print(f'REBUILD_PRESERVATION_OK: {before} owned objects before/after; unrelated sentinel unchanged')
