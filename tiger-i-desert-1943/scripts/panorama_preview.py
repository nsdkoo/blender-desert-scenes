import bpy
from pathlib import Path

ROOT=Path(__file__).resolve().parent
scene=bpy.context.scene
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-0.8
path=Path.home()/'.agent-reach'/'assets'/'desert-tiger'/'goegap_4k.hdr'
image=bpy.data.images.load(str(path))
image.scale(1536,768)
image.save_render(str(ROOT/'renders'/'goegap_panorama.png'),scene=scene)
