import bpy
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
arguments=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
mode=arguments[0] if arguments else 'hero'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'desert_tiger.blend'))
scene=bpy.context.scene
preferences=bpy.context.preferences.addons['cycles'].preferences
try:
    preferences.compute_device_type='OPTIX'
    preferences.get_devices()
    gpu_found=False
    for device in preferences.devices:
        device.use=device.type=='OPTIX'
        gpu_found=gpu_found or device.use
        print('DEVICE',device.name,device.type,device.use,flush=True)
    scene.cycles.device='GPU' if gpu_found else 'CPU'
except Exception as error:
    print('GPU configuration fallback:',error,flush=True)
    scene.cycles.device='CPU'
if mode=='preview':
    scene.render.resolution_percentage=45
    scene.cycles.samples=32
    scene.cycles.adaptive_threshold=0.08
    scene.render.filepath=str(ROOT/'renders'/'preview.png')
elif mode=='detail':
    scene.camera=bpy.data.objects['Camera · low armor detail']
    scene.render.resolution_x=2400
    scene.render.resolution_y=1600
    scene.cycles.samples=160
    scene.render.filepath=str(ROOT/'renders'/'desert_tiger_detail.png')
else:
    scene.render.filepath=str(ROOT/'renders'/'desert_tiger_hero.png')
bpy.ops.render.render(write_still=True)
print('RENDER_COMPLETE',scene.render.filepath,flush=True)
