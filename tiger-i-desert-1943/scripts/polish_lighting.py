import bpy
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'desert_tiger.blend'))
scene=bpy.context.scene
nodes=scene.world.node_tree.nodes
links=scene.world.node_tree.links
existing=nodes.get('Background')
output=nodes.get('World Output')
sky=nodes.new('ShaderNodeTexSky')
sky.sky_type='MULTIPLE_SCATTERING'
sky.sun_elevation=math.radians(43)
sky.sun_rotation=math.radians(220)
sky.sun_disc=False
sky.air_density=1.0
sky.aerosol_density=0.65
sky.ozone_density=1.0
clear_background=nodes.new('ShaderNodeBackground')
clear_background.name='Photographic clear desert sky'
clear_background.inputs['Strength'].default_value=0.20
links.new(sky.outputs[0],clear_background.inputs[0])
light_path=nodes.new('ShaderNodeLightPath')
mix=nodes.new('ShaderNodeMixShader')
links.new(light_path.outputs['Is Camera Ray'],mix.inputs[0])
links.new(existing.outputs[0],mix.inputs[1])
links.new(clear_background.outputs[0],mix.inputs[2])
links.new(mix.outputs[0],output.inputs['Surface'])
bpy.data.materials['Subtle mineral dust in distant air'].node_tree.nodes.get('Volume Scatter').inputs['Density'].default_value=0.00018
environment=bpy.data.collections['07 · Scanned sand and desert landscape']
sand=bpy.data.materials['Desert sand · photographic PBR']
vertices=[]
faces=[]
width=600
depth=220
columns=260
rows=130
for row in range(rows+1):
    ypos=42+depth*row/rows
    for column in range(columns+1):
        xpos=-300+width*column/columns
        height=0
        for center,amplitude,spread,phase in [(90,6,28,0),(152,11,34,1.4),(227,16,45,3.1)]:
            ridge=center+14*math.sin(xpos*0.016+phase)+5*math.sin(xpos*0.031+phase)
            delta=(ypos-ridge)/(spread if ypos<ridge else spread*0.45)
            height+=amplitude*math.exp(-delta*delta)*(0.75+0.25*math.sin(xpos*0.015+phase))
        fade=min(1,row/12,(rows-row)/15)
        vertices.append((xpos,ypos,-0.8+height*fade))
for row in range(rows):
    for column in range(columns):
        base=row*(columns+1)+column
        faces.append((base,base+1,base+columns+2,base+columns+1))
data=bpy.data.meshes.new('Aeolian dune ridges')
data.from_pydata(vertices,[],faces)
data.update()
obj=bpy.data.objects.new('Distant sculpted sand dunes',data)
environment.objects.link(obj)
data.materials.append(sand)
uv=data.uv_layers.new(name='Dune meters')
for polygon in data.polygons:
    polygon.use_smooth=True
    for loop_index in polygon.loop_indices:
        vertex=data.vertices[data.loops[loop_index].vertex_index]
        uv.data[loop_index].uv=(vertex.co.x*0.19,vertex.co.y*0.19)
scene.cycles.samples=256
scene.render.resolution_x=3840
scene.render.resolution_y=2400
scene.camera.data.dof.aperture_fstop=13
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'desert_tiger.blend'))
print('LIGHTING_POLISHED',flush=True)
