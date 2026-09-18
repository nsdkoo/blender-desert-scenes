import bpy
import math
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'desert_tiger.blend'))
scene=bpy.context.scene
terrain=bpy.data.objects['Wind-rippled sand with sunken track paths']
foliage=bpy.data.collections['10 · Photographic desert vegetation and rocks']
for obj in foliage.objects:
    xpos,ypos=obj.location.x,obj.location.y
    hit,location,normal,index=terrain.ray_cast(Vector((xpos,ypos,50)),Vector((0,0,-1)))
    ground=location.z if hit else 0.0
    minimum=min(vertex[2] for vertex in obj.bound_box)*obj.scale.z
    obj.location.z=ground-minimum-0.025
    if obj.name.startswith('Scanned desert granite'):
        obj.scale*=1.35
        minimum=min(vertex[2] for vertex in obj.bound_box)*obj.scale.z
        obj.location.z=ground-minimum-0.055

bpy.data.objects['Distant sculpted sand dunes'].hide_render=True
nodes=scene.world.node_tree.nodes
links=scene.world.node_tree.links
background=nodes.get('Background')
output=nodes.get('World Output')
for node in nodes:
    if node.type=='TEX_ENVIRONMENT':
        image=bpy.data.images.get('goegap_4k.hdr')
        if not image:
            image=bpy.data.images.load(str(Path.home()/'.agent-reach'/'assets'/'desert-tiger'/'goegap_4k.hdr'))
        image.pack()
        node.image=image
        links.new(node.outputs[0],background.inputs[0])
    elif node.type=='MAPPING':
        node.inputs['Rotation'].default_value=(0,0,math.radians(-15))
links.new(background.outputs[0],output.inputs['Surface'])
background.inputs['Strength'].default_value=0.90
sun=bpy.data.objects['Saharan afternoon sun']
sun.data.energy=2.8
sun.data.color=(1.0,0.94,0.84)
sun.data.angle=math.radians(0.55)
source=Vector((0.63,-0.28,0.72))
sun.rotation_euler=(-source).to_track_quat('-Z','Y').to_euler()
scene.view_settings.exposure=0.5
scene.view_settings.look='AgX - Medium High Contrast'
bpy.ops.object.light_add(type='AREA',location=(-5.5,-6.5,6.5))
fill=bpy.context.object
fill.name='Open-sky reflected light'
fill.data.energy=650
fill.data.shape='DISK'
fill.data.size=8
fill.data.color=(0.74,0.84,1.0)
fill.rotation_euler=(Vector((0,0,1.7))-fill.location).to_track_quat('-Z','Y').to_euler()
for owner in list(fill.users_collection):
    owner.objects.unlink(fill)
bpy.data.collections['08 · Natural desert lighting and cameras'].objects.link(fill)
camera=scene.camera
camera.location=(-11.9,-14.8,3.40)
target=Vector((-0.7,0.2,1.93))
camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.lens=48
camera.data.dof.aperture_fstop=9
camera.data.dof.focus_distance=(target-camera.location).length
scene.cycles.samples=96
scene.cycles.adaptive_threshold=0.035
scene.render.resolution_x=3200
scene.render.resolution_y=2000
scene['External assets']='Poly Haven CC0: Goegap HDRI, Aerial Sand, Quiver Tree 01, Wild Rooibos Bush, Namaqualand Boulder 02'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'desert_tiger.blend'))
print('PHOTOGRAPHY_READY',flush=True)
