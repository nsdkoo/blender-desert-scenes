import bpy
import math
import random
from pathlib import Path
from mathutils import Vector
from mathutils.noise import fractal

ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'desert_tiger.blend'))
random.seed(830)
scene=bpy.context.scene
armor=bpy.data.materials['RAL 8000 · sun-bleached sand / chipped steel']
sand=bpy.data.materials['Desert sand · photographic PBR']
nodes=sand.node_tree.nodes
links=sand.node_tree.links
shader=nodes.get('Principled BSDF')
source=shader.inputs['Base Color'].links[0].from_socket
tint=nodes.new('ShaderNodeMixRGB')
tint.name='Warm mineral sand tint'
tint.blend_type='MULTIPLY'
tint.inputs[0].default_value=0.80
tint.inputs[2].default_value=(0.60,0.37,0.15,1)
links.new(source,tint.inputs[1])
links.new(tint.outputs[0],shader.inputs['Base Color'])

terrain=bpy.data.objects['Wind-rippled sand with sunken track paths']
uv=terrain.data.uv_layers.new(name='Sand meters')
for polygon in terrain.data.polygons:
    for loop_index in polygon.loop_indices:
        vertex=terrain.data.vertices[terrain.data.loops[loop_index].vertex_index]
        uv.data[loop_index].uv=(vertex.co.x*0.19,vertex.co.y*0.19)

environment_group=bpy.data.collections['07 · Scanned sand and desert landscape']
def ground_height(xpos,ypos):
    distance=math.sqrt(xpos*xpos+ypos*ypos)
    fade=min(1,max(0,(distance-4)/15))
    undulation=fractal(Vector((xpos*0.055,ypos*0.055,0.6)),1.0,2.0,4)*0.62
    ripples=0.012*math.sin(xpos*10+ypos*3+1.5*math.sin(ypos*0.6))
    return -0.025+undulation*fade+ripples*min(1,distance/6)

vertices=[]
faces=[]
segments=380
rings=55
for ring in range(rings):
    half=32.5+(ring/(rings-1))**1.7*650
    for index in range(segments*4):
        edge=index//segments
        fraction=(index%segments)/segments
        coords=[(-half+2*half*fraction,-half),(half,-half+2*half*fraction),(half-2*half*fraction,half),(-half,half-2*half*fraction)]
        xpos,ypos=coords[edge]
        fade=min(1,max(0,(half-35)/80))
        hills=fade*(2.3+2.4*math.sin(xpos*0.014+ypos*0.020)+1.8*math.sin(xpos*0.031-ypos*0.012))
        zpos=ground_height(xpos,ypos)+hills
        vertices.append((xpos,ypos,zpos))
for ring in range(rings-1):
    for index in range(segments*4):
        next_index=(index+1)%(segments*4)
        base=ring*segments*4
        faces.append((base+index,base+next_index,base+segments*4+next_index,base+segments*4+index))
data=bpy.data.meshes.new('Continuous distant desert mesh')
data.from_pydata(vertices,[],faces)
data.update()
obj=bpy.data.objects.new('Continuous sand hills to horizon',data)
environment_group.objects.link(obj)
data.materials.append(sand)
uv=data.uv_layers.new(name='Sand meters')
for polygon in data.polygons:
    polygon.use_smooth=True
    for loop_index in polygon.loop_indices:
        vertex=data.vertices[data.loops[loop_index].vertex_index]
        uv.data[loop_index].uv=(vertex.co.x*0.19,vertex.co.y*0.19)

turret=bpy.data.objects['Tiger horseshoe turret · rolled armor']
outline=[(-1.47,-0.73),(-1.32,-0.90)]
for index in range(65):
    angle=math.radians(-145+290*index/64)
    outline.append((-0.20+1.36*math.cos(angle),1.155*math.sin(angle)))
outline.extend([(-1.32,0.90),(-1.47,0.73)])
vertices=[(xpos,ypos,2.30) for xpos,ypos in outline]+[(xpos*0.96,ypos*0.97,3.12) for xpos,ypos in outline]
count=len(outline)
faces=[tuple(reversed(range(count))),tuple(range(count,2*count))]
faces += [(index,(index+1)%count,(index+1)%count+count,index+count) for index in range(count)]
data=bpy.data.meshes.new('Continuous rolled horseshoe turret armor')
data.from_pydata(vertices,[],faces)
data.update()
data.materials.append(armor)
turret.data=data
for polygon in data.polygons:
    polygon.use_smooth=len(polygon.vertices)==4
for modifier in list(turret.modifiers):
    if modifier.type=='WEIGHTED_NORMAL':
        turret.modifiers.remove(modifier)

for obj in list(bpy.data.objects):
    if obj.name.startswith('Tactical number'):
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active=obj
        obj.data.extrude=0
        bpy.ops.object.convert(target='MESH')
        wrap=obj.modifiers.new('Paint conforms to curved turret','SHRINKWRAP')
        wrap.target=turret
        wrap.wrap_method='NEAREST_SURFACEPOINT'
        wrap.offset=0.002 if 'ivory' in obj.name else 0.003

mark_group=bpy.data.collections['06 · Painted markings and weld details']
def flat_material(name,color,metallic):
    mat=bpy.data.materials.new(name)
    mat.diffuse_color=(*color,1)
    mat.use_nodes=True
    shader=mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value=(*color,1)
    shader.inputs['Metallic'].default_value=metallic
    shader.inputs['Roughness'].default_value=0.75
    return mat
chip_mats=[flat_material('Deep paint chip / dark exposed steel',(0.043,0.035,0.021),0.6),flat_material('Red oxide primer at worn edges',(0.105,0.052,0.023),0.35),flat_material('Pale paint scuff',(0.40,0.30,0.15),0.1)]
vertices=[]
faces=[]
material_indices=[]
for side in [-1,1]:
    for index in range(650):
        xpos=random.uniform(-2.86,2.84)
        zpos=random.choice([1.515,2.055,1.64])+random.gauss(0,0.025) if index<420 else random.uniform(1.53,2.06)
        size=random.uniform(0.004,0.024)
        base=len(vertices)
        count=random.randint(4,7)
        for corner in range(count):
            angle=corner*math.tau/count
            vertices.append((xpos+math.cos(angle)*size*random.uniform(0.6,1.6),side*1.398,zpos+math.sin(angle)*size*random.uniform(0.18,0.5)))
        faces.append(tuple(range(base,base+count)))
        material_indices.append(random.choices([0,1,2],[5,2,3])[0])
    for index in range(180):
        xpos=random.uniform(-2.75,2.72)
        ypos=side*random.uniform(1.43,1.74)
        size=random.uniform(0.008,0.035)
        base=len(vertices)
        for corner in range(5):
            angle=corner*math.tau/5
            vertices.append((xpos+math.cos(angle)*size,ypos+math.sin(angle)*size*0.45,1.627))
        faces.append(tuple(range(base,base+5)))
        material_indices.append(random.randrange(3))
for index in range(300):
    ypos=random.uniform(-1.34,1.34)
    zpos=random.choice([1.80,2.09])+random.gauss(0,0.02) if index<230 else random.uniform(1.77,2.08)
    size=random.uniform(0.004,0.026)
    base=len(vertices)
    for corner in range(5):
        angle=corner*math.tau/5
        vertices.append((-3.025,ypos+math.cos(angle)*size,zpos+math.sin(angle)*size*0.35))
    faces.append(tuple(range(base,base+5)))
    material_indices.append(random.randrange(3))
data=bpy.data.meshes.new('Irregular flaking paint mesh')
data.from_pydata(vertices,[],faces)
data.update()
obj=bpy.data.objects.new('Localized armor paint chipping',data)
mark_group.objects.link(obj)
for mat in chip_mats:
    data.materials.append(mat)
for polygon,index in zip(data.polygons,material_indices):
    polygon.material_index=index

for obj in bpy.data.objects:
    if obj.type=='MESH' and obj.name.startswith(('Cast gun mantlet','Turret rear stowage bin')):
        for modifier in obj.modifiers:
            if modifier.type=='BEVEL':
                modifier.segments=5

world=scene.world
for node in world.node_tree.nodes:
    if node.type=='MAPPING':
        node.inputs['Rotation'].default_value[2]=math.radians(235)
world.node_tree.nodes.get('Background').inputs['Strength'].default_value=0.55
sun=bpy.data.objects['Saharan afternoon sun']
sun.data.energy=2.6
sun.data.angle=math.radians(0.65)
sun.data.color=(1,0.94,0.84)
sun.rotation_euler=Vector((0.2,0.55,-0.86)).to_track_quat('-Z','Y').to_euler()

camera=bpy.data.objects['Camera · hero three-quarter']
camera.location=(-12.7,-15.8,3.60)
target=Vector((-0.75,0,1.80))
camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.lens=52
camera.data.dof.aperture_fstop=11
camera.data.dof.focus_distance=(target-camera.location).length
detail=bpy.data.objects['Camera · low armor detail']
detail.location=(-9.0,-11.3,3.15)
target=Vector((-0.9,0,1.67))
detail.rotation_euler=(target-detail.location).to_track_quat('-Z','Y').to_euler()
detail.data.lens=47
detail.data.dof.aperture_fstop=9
detail.data.dof.focus_distance=(target-detail.location).length
scene.view_settings.exposure=-0.25
scene.camera=camera
scene.render.resolution_x=3000
scene.render.resolution_y=1875
scene.cycles.samples=256
scene.cycles.adaptive_threshold=0.015
scene.render.resolution_percentage=100
scene.render.filepath=str(ROOT/'renders'/'desert_tiger_hero.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'desert_tiger.blend'))
print('REFINEMENT_COMPLETE',flush=True)
