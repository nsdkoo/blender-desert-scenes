import bpy
import math
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'desert_tiger.blend'))
scene=bpy.context.scene
world=scene.world
world.name='Dry cracked lake · real sunlit desert panorama'
path=Path.home()/'.agent-reach'/'assets'/'desert-tiger'/'dry_cracked_lake_4k.hdr'
for node in world.node_tree.nodes:
    if node.type=='TEX_ENVIRONMENT':
        node.image=bpy.data.images.load(str(path))
        node.image.pack()
    if node.type=='MAPPING':
        node.inputs['Rotation'].default_value=(0,0,math.radians(40))
world.node_tree.nodes.get('Background').inputs['Strength'].default_value=0.65
sun=bpy.data.objects['Saharan afternoon sun']
sun.data.energy=3.6
sun.rotation_euler=Vector((0.50,0.30,-0.92)).to_track_quat('-Z','Y').to_euler()
scene.view_settings.exposure=-0.15

volume=bpy.data.materials.new('Subtle mineral dust in distant air')
volume.use_nodes=True
nodes=volume.node_tree.nodes
nodes.clear()
output=nodes.new('ShaderNodeOutputMaterial')
scatter=nodes.new('ShaderNodeVolumeScatter')
scatter.inputs['Color'].default_value=(0.77,0.70,0.59,1)
scatter.inputs['Density'].default_value=0.0007
scatter.inputs['Anisotropy'].default_value=0.30
volume.node_tree.links.new(scatter.outputs[0],output.inputs['Volume'])
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,35))
obj=bpy.context.object
obj.name='Desert atmosphere · distant dust haze'
obj.dimensions=(1300,1300,90)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
obj.data.materials.append(volume)
obj.display_type='WIRE'
for owner in list(obj.users_collection):
    owner.objects.unlink(obj)
bpy.data.collections['08 · Natural desert lighting and cameras'].objects.link(obj)
scene.cycles.volume_bounces=1
scene['External assets']='Poly Haven dry_cracked_lake HDRI and aerial_sand PBR / CC0'
scene.render.resolution_x=3000
scene.render.resolution_y=1875
scene.render.resolution_percentage=100
scene.cycles.samples=256
scene.cycles.adaptive_threshold=0.015
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'desert_tiger.blend'))
print('FINAL_SCENE_READY',flush=True)
