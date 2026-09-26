import bpy,os
F=os.path.dirname(__file__)
for o in list(bpy.data.objects):
 if o.name.startswith('CI_Recessed_Inner_Shroud'):bpy.data.objects.remove(o,do_unlink=True)
if 'CI_inner_shroud' in bpy.context.scene:del bpy.context.scene['CI_inner_shroud']
for file,label in [('generate_blockout.py','LM_GENERATION_SCRIPT'),('cabinet_inner_shroud.py','LM_INNER_SHROUD_SCRIPT')]:
 t=bpy.data.texts.get(label) or bpy.data.texts.new(label);t.clear();t.write(open(os.path.join(F,file),encoding='utf-8-sig').read())
old=bpy.context.preferences.filepaths.save_version;bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(F,'lapping_machine_blockout.blend'));bpy.context.preferences.filepaths.save_version=old
print('SHROUD_REMOVED; all other scene objects retained.')
