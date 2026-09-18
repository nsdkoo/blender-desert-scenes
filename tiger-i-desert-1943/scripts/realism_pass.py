import bpy
import math
import random
from pathlib import Path
from mathutils import Vector, Matrix

ROOT=Path(__file__).resolve().parent
CACHE=Path.home()/'.agent-reach'/'assets'/'desert-tiger'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'desert_tiger.blend'))
scene=bpy.context.scene
random.seed(918)

def new_group(name):
    group=bpy.data.collections.new(name)
    scene.collection.children.link(group)
    return group

detail_group=new_group('09 · Close-up metalwork and battle wear')
foliage_group=new_group('10 · Photographic desert vegetation and rocks')

def move(obj,group):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    group.objects.link(obj)

def box(name,location,dimensions,mat,bevel=0.008):
    bpy.ops.mesh.primitive_cube_add(size=1,location=location)
    obj=bpy.context.object
    obj.name=name
    obj.dimensions=dimensions
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(mat)
    if bevel:
        modifier=obj.modifiers.new('Metal edge','BEVEL')
        modifier.width=bevel
        modifier.segments=3
        obj.modifiers.new('Machined normals','WEIGHTED_NORMAL')
    move(obj,detail_group)
    return obj

def curve(name,points,radius,mat):
    data=bpy.data.curves.new(name,'CURVE')
    data.dimensions='3D'
    data.bevel_depth=radius
    data.bevel_resolution=2
    spline=data.splines.new('POLY')
    spline.points.add(len(points)-1)
    for point,coord in zip(spline.points,points):
        point.co=(*coord,1)
    data.materials.append(mat)
    obj=bpy.data.objects.new(name,data)
    detail_group.objects.link(obj)
    return obj

paint=bpy.data.materials['RAL 8000 · sun-bleached sand / chipped steel']
steel=bpy.data.materials['Cast track steel · polished and oxidized']
edge=bpy.data.materials['Exposed worn steel edges']
dark=bpy.data.materials['Dusty recesses']

for mat in [paint,dark,steel]:
    nodes=mat.node_tree.nodes
    links=mat.node_tree.links
    shader=nodes.get('Principled BSDF')
    source=shader.inputs['Base Color'].links[0].from_socket
    geo=nodes.new('ShaderNodeNewGeometry')
    noise=nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value=72
    noise.inputs['Detail'].default_value=4
    links.new(geo.outputs['Position'],noise.inputs['Vector'])
    curvature=nodes.new('ShaderNodeValToRGB')
    curvature.color_ramp.elements[0].position=0.503
    curvature.color_ramp.elements[1].position=0.56
    links.new(geo.outputs['Pointiness'],curvature.inputs[0])
    broken=nodes.new('ShaderNodeMath')
    broken.operation='MULTIPLY'
    links.new(curvature.outputs[0],broken.inputs[0])
    links.new(noise.outputs['Fac'],broken.inputs[1])
    wear=nodes.new('ShaderNodeMixRGB')
    wear.name='Convex edges rubbed to metal'
    links.new(broken.outputs[0],wear.inputs[0])
    links.new(source,wear.inputs[1])
    wear.inputs[2].default_value=(0.10,0.088,0.063,1) if mat!=steel else (0.33,0.31,0.26,1)
    links.new(wear.outputs[0],shader.inputs['Base Color'])
    if mat==paint:
        for node in nodes:
            if node.type=='VALTORGB' and node!=curvature:
                ramp=node.color_ramp
                if ramp.elements[0].position<0.3:
                    ramp.elements[0].color=(0.235,0.181,0.090,1)
                    ramp.elements[-1].color=(0.36,0.28,0.155,1)
        shader.inputs['Metallic'].default_value=0.32
        for node in nodes:
            if node.type=='BUMP':
                node.inputs['Strength'].default_value=0.19
                node.inputs['Distance'].default_value=0.004
        ambient=nodes.new('ShaderNodeAmbientOcclusion')
        ambient.inputs['Distance'].default_value=0.10
        ambient.samples=8
        recess=nodes.new('ShaderNodeMixRGB')
        recess.blend_type='MULTIPLY'
        recess.inputs[0].default_value=0.30
        links.new(wear.outputs[0],recess.inputs[1])
        links.new(ambient.outputs['Color'],recess.inputs[2])
        links.new(recess.outputs[0],shader.inputs['Base Color'])
    elif mat==steel:
        shader.inputs['Metallic'].default_value=0.82

barrel_mat=paint.copy()
barrel_mat.name='Barrel paint · smooth aged steel'
for node in barrel_mat.node_tree.nodes:
    if node.type=='BUMP':
        node.inputs['Distance'].default_value=0.0015
for obj in bpy.data.objects:
    if obj.name.startswith(('88 mm KwK','Barrel collar','Recoil sleeve')):
        obj.data.materials.clear()
        obj.data.materials.append(barrel_mat)

prototype=next(obj for obj in bpy.data.objects if obj.name.startswith('Track -1 · link'))
basis=Matrix(((0,0,-1),(-1,0,0),(0,1,0)))
for index in range(13):
    obj=bpy.data.objects.new('Spare track shoe on front glacis',prototype.data)
    detail_group.objects.link(obj)
    obj.location=(-3.155,-1.08+index*0.18,1.31)
    obj.rotation_euler=basis.to_euler()
box('Spare track retaining rail',(-3.20,0,1.685),(0.07,2.43,0.052),dark)
for ypos in [-1.19,1.19]:
    box('Spare track retaining clasp',(-3.20,ypos,1.42),(0.078,0.067,0.56),dark)

for side in [-1,1]:
    for zpos in [1.74,2.095]:
        points=[]
        for index in range(121):
            xpos=-2.84+index*0.047
            points.append((xpos,side*(1.399+random.uniform(0,0.003)),zpos+0.004*math.sin(index*2.8)))
        curve('Rippling welded hull seam',points,0.009,dark)
    for xpos in [-2.82,2.82]:
        points=[]
        for index in range(22):
            points.append((xpos+0.002*math.sin(index*2),side*1.403,1.73+index*0.016))
        curve('Vertical armor weld bead',points,0.011,dark)
    points=[]
    for index in range(65):
        xpos=-1.16+index*0.025
        ypos=side*(1.155*math.sqrt(max(0,1-((xpos+0.2)/1.36)**2))*0.97)
        points.append((xpos,ypos,3.118+0.002*math.sin(index*2.6)))
    curve('Turret roof continuous weld',points,0.008,dark)

for obj in bpy.data.objects:
    if obj.name.startswith('Segmented side mudguard'):
        for vertex in obj.data.vertices:
            if abs(vertex.co.y)>0.15:
                vertex.co.z+=random.uniform(-0.028,0.022)

for side in [-1,1]:
    for index in range(20):
        xpos=random.uniform(-2.65,2.62)
        zpos=random.uniform(1.80,2.05)
        length=random.uniform(0.035,0.16)
        curve('Fine scrape across aged side paint',[(xpos,side*1.401,zpos),(xpos+length*0.5,side*1.402,zpos+random.uniform(-0.004,0.004)),(xpos+length,side*1.401,zpos+random.uniform(-0.004,0.004))],random.uniform(0.0006,0.0014),edge)

def load_asset(asset):
    path=CACHE/asset/(asset+'.blend')
    before=set(bpy.data.images)
    with bpy.data.libraries.load(str(path),link=False) as (source,target):
        names=[name for name in source.objects if 'LOD0' in name]
        if not names:
            names=[name for name in source.objects if asset in name and '_LOD' not in name]
        target.objects=names
    objects=[obj for obj in target.objects if obj and obj.type=='MESH']
    assert objects,f'No mesh in {asset}'
    for image in set(bpy.data.images)-before:
        if image.source=='FILE':
            basename=Path(image.filepath.replace('\\','/')).name
            candidate=CACHE/asset/'textures'/basename
            low_resolution=CACHE/asset/'textures'/basename.replace('_2k.','_1k.')
            if low_resolution.exists() and low_resolution.stat().st_size>100:
                candidate=low_resolution
            assert candidate.exists() and candidate.stat().st_size>100,f'Missing image {candidate}'
            image.filepath=str(candidate)
            image.reload()
            image.pack()
    for obj in objects:
        obj.hide_render=False
        obj.hide_viewport=False
        for modifier in list(obj.modifiers):
            if modifier.type in {'SUBSURF','DISPLACE'}:
                modifier.show_render=False
                modifier.show_viewport=False
    print('ASSET_LOADED',asset,[obj.name for obj in objects],flush=True)
    return objects

def instance_asset(prototypes,name,position,scale,rotation):
    for prototype in [random.choice(prototypes)]:
        obj=prototype.copy()
        obj.data=prototype.data
        obj.name=name
        obj.parent=None
        foliage_group.objects.link(obj)
        obj.location=position
        obj.scale=tuple(scale*value for value in prototype.scale)
        obj.rotation_euler=(0,0,rotation)
        obj.hide_set(False)
    return obj

tree=load_asset('quiver_tree_01')
trees=[(-8,8,1.5),(6.3,7.5,1.7),(12,14,1.8),(-3,19,1.35),(-14,18,1.9),(19,22,1.7),(3,27,1.5),(-20,28,2.0),(22,37,2.1),(10,34,1.5)]
for xpos,ypos,scale in trees:
    instance_asset(tree,'Desert quiver tree / photographic bark',(xpos,ypos,-0.08),scale,random.uniform(0,math.tau))
bush=load_asset('wild_rooibos_bush')
for index in range(88):
    xpos=random.uniform(-23,29)
    ypos=random.uniform(3.5,35)
    if abs(xpos)<4.5 and ypos<6:
        continue
    scale=random.uniform(0.60,1.70)
    instance_asset(bush,'Wild desert scrub',(xpos,ypos,-0.06),scale,random.uniform(0,math.tau))
for xpos,ypos,scale in [(-6,-3.9,0.9),(1.5,-6.5,0.60),(6,-2,0.9),(-7.5,0,1.2)]:
    instance_asset(bush,'Foreground scrub',(xpos,ypos,-0.05),scale,random.uniform(0,math.tau))
rock=load_asset('namaqualand_boulder_02')
rock_positions=[(-6,-3.8,0.31),(4.8,3.6,0.65),(7.5,8.0,0.85),(-10,11,0.70),(12,18,1.2),(-6,23,0.9),(20,27,1.5),(-16,18,1.4),(8,-3,0.26)]
for xpos,ypos,scale in rock_positions:
    instance_asset(rock,'Scanned desert granite',(xpos,ypos,-0.12),scale,random.uniform(0,math.tau))
for obj in list(bpy.data.objects):
    if obj.name.startswith('Scattered desert stone') and obj.scale.x>0.14:
        obj.hide_render=True

bpy.data.objects['Desert atmosphere · distant dust haze'].hide_render=True
for node in scene.world.node_tree.nodes:
    if node.type=='BACKGROUND':
        node.inputs['Strength'].default_value=0.055 if node.name=='Photographic clear desert sky' else 0.38
    if node.type=='TEX_SKY':
        node.sun_elevation=math.radians(34)
        node.aerosol_density=0.8
sun=bpy.data.objects['Saharan afternoon sun']
sun.data.energy=4.8
sun.data.color=(1,0.90,0.74)
sun.data.angle=math.radians(0.55)
sun.rotation_euler=Vector((0.88,0.40,-0.90)).to_track_quat('-Z','Y').to_euler()
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-0.4
camera=scene.camera
camera.location=(-12.7,-15.8,3.85)
target=Vector((-0.5,1.3,1.85))
camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.lens=49
camera.data.dof.aperture_fstop=8
camera.data.dof.focus_distance=(Vector((-0.6,0,1.6))-camera.location).length
scene.cycles.samples=128
scene.cycles.adaptive_threshold=0.025
scene.cycles.volume_bounces=0
scene.render.resolution_x=3200
scene.render.resolution_y=2000
scene.render.resolution_percentage=100
scene['Revised direction']='Desert woodland, photographic vegetation, strong clear sunshine, fine armor details'
scene['External assets']='Poly Haven CC0: aerial_sand, dry_cracked_lake, quiver_tree_01, wild_rooibos_bush, namaqualand_boulder_02'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'desert_tiger.blend'))
print('REALISM_PASS_COMPLETE',len(scene.objects),flush=True)
