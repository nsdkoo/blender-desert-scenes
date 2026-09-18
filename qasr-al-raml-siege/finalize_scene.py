import bpy
import os
import json
from mathutils import Vector


scene = bpy.context.scene
out = os.path.dirname(os.path.abspath(__file__))
scene.render.resolution_x = 1920
scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.cycles.samples = 64
scene.cycles.adaptive_threshold = 0.025
scene.render.filepath = os.path.join(out, 'qasr_al_raml_final.png')
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
            area.spaces.active.shading.type = 'SOLID'
            area.spaces.active.shading.color_type = 'MATERIAL'
            area.spaces.active.overlay.show_overlays = False
for obj in scene.objects:
    obj.select_set(False)
bpy.context.view_layer.objects.active = scene.camera
scene.camera.select_set(True)
report = {
    'scene': scene.name,
    'objects': len(scene.objects),
    'soldiers': json.loads(scene['Soldier counts']),
    'resolution': [1920, 1200],
    'engine': scene.render.engine,
    'device': scene.cycles.device,
    'external_assets': 0,
    'camera_lens_mm': scene.camera.data.lens,
    'collections': [collection.name for collection in scene.collection.children],
    'missing_images': [image.filepath for image in bpy.data.images if image.source == 'FILE' and not image.packed_file and not os.path.exists(bpy.path.abspath(image.filepath))],
}
assert scene.camera is not None
assert report['soldiers']['attackers'] > 20
assert report['soldiers']['defenders'] > 10
assert not report['missing_images']
with open(os.path.join(out, 'scene_report.json'), 'w', encoding='utf-8') as handle:
    json.dump(report, handle, ensure_ascii=False, indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, 'qasr_al_raml.blend'))
print('FINAL_SCENE_READY', json.dumps(report), flush=True)
bpy.ops.render.render(write_still=True)
print('FINAL_RENDER_COMPLETE', flush=True)
