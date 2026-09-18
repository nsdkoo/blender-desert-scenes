import bpy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'desert_tiger.blend'))
scene=bpy.context.scene
images=[image for image in bpy.data.images if image.source=='FILE' and image.users]
result={
    'blender_version':bpy.app.version_string,
    'objects':len(scene.objects),
    'mesh_objects':sum(obj.type=='MESH' for obj in scene.objects),
    'track_links':sum(obj.name.startswith('Track ') and 'link' in obj.name for obj in scene.objects),
    'materials':len(bpy.data.materials),
    'packed_images':{image.name:bool(image.packed_file) for image in images},
    'camera':scene.camera.name,
    'resolution':[scene.render.resolution_x,scene.render.resolution_y],
    'renderer':scene.render.engine,
    'samples':scene.cycles.samples,
    'renders':{},
}
for filename in ['desert_tiger_hero.png','desert_tiger_detail.png']:
    path=ROOT/'renders'/filename
    if path.exists():
        image=bpy.data.images.load(str(path))
        result['renders'][filename]={'resolution':list(image.size),'bytes':path.stat().st_size}
    else:
        result['renders'][filename]={'missing':True}
assert all(result['packed_images'].values()),'An external texture is not packed'
assert result['track_links']>150,'Track links missing'
assert all('missing' not in render for render in result['renders'].values()),'Render missing'
(ROOT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
