import bpy
import math
import random
from pathlib import Path
from mathutils import Vector
from mathutils.noise import noise_vector, fractal

ROOT = Path(__file__).resolve().parent
ASSETS = Path.home() / '.agent-reach' / 'assets' / 'desert-tiger'
random.seed(1943)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for datablock in bpy.data.materials:
    bpy.data.materials.remove(datablock)

def collection(name):
    result = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(result)
    return result

GROUP = collection('01 · Armor and hull')

def move_group(obj):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    GROUP.objects.link(obj)
    return obj

def material(name, color, metallic=0.0, roughness=0.65):
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1)
    result.use_nodes = True
    shader = result.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Metallic'].default_value = metallic
    shader.inputs['Roughness'].default_value = roughness
    return result

def weathered(name, light, dark, metallic=0.2, scale=6):
    result = material(name, light, metallic)
    nodes = result.node_tree.nodes
    links = result.node_tree.links
    shader = nodes.get('Principled BSDF')
    coord = nodes.new('ShaderNodeTexCoord')
    broad = nodes.new('ShaderNodeTexNoise')
    broad.inputs['Scale'].default_value = scale
    broad.inputs['Detail'].default_value = 5
    broad.inputs['Roughness'].default_value = 0.75
    links.new(coord.outputs['Object'], broad.inputs['Vector'])
    palette = nodes.new('ShaderNodeValToRGB')
    palette.color_ramp.elements[0].position = 0.22
    palette.color_ramp.elements[0].color = (*dark, 1)
    palette.color_ramp.elements[1].position = 0.78
    palette.color_ramp.elements[1].color = (*light, 1)
    links.new(broad.outputs['Fac'], palette.inputs[0])
    grit = nodes.new('ShaderNodeTexNoise')
    grit.inputs['Scale'].default_value = 175
    grit.inputs['Detail'].default_value = 3
    links.new(coord.outputs['Object'], grit.inputs['Vector'])
    chip = nodes.new('ShaderNodeValToRGB')
    chip.color_ramp.elements[0].position = 0.67
    chip.color_ramp.elements[0].color = (0, 0, 0, 1)
    chip.color_ramp.elements[1].position = 0.77
    chip.color_ramp.elements[1].color = (1, 1, 1, 1)
    links.new(grit.outputs['Fac'], chip.inputs[0])
    mix = nodes.new('ShaderNodeMixRGB')
    links.new(chip.outputs['Color'], mix.inputs[0])
    links.new(palette.outputs['Color'], mix.inputs[1])
    mix.inputs[2].default_value = (0.065, 0.048, 0.03, 1)
    links.new(mix.outputs[0], shader.inputs['Base Color'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.24
    bump.inputs['Distance'].default_value = 0.012
    links.new(grit.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs[0], shader.inputs['Normal'])
    rough = nodes.new('ShaderNodeMapRange')
    rough.inputs['To Min'].default_value = 0.48
    rough.inputs['To Max'].default_value = 0.88
    links.new(broad.outputs['Fac'], rough.inputs['Value'])
    links.new(rough.outputs[0], shader.inputs['Roughness'])
    return result

paint = weathered('RAL 8000 · sun-bleached sand / chipped steel', (0.43, 0.325, 0.17), (0.22, 0.17, 0.085))
paint_dark = weathered('Dusty recesses', (0.27, 0.215, 0.12), (0.11, 0.095, 0.054))
steel = weathered('Cast track steel · polished and oxidized', (0.22, 0.19, 0.14), (0.043, 0.037, 0.029), 0.72, 13)
rubber = weathered('Worn rubber with sand dust', (0.075, 0.066, 0.05), (0.018, 0.02, 0.018), 0, 20)
rust = weathered('Heat-oxidized exhaust', (0.20, 0.093, 0.041), (0.043, 0.031, 0.02), 0.6, 9)
black = material('Blackened cavities', (0.012, 0.014, 0.011), 0.18, 0.8)
edge = material('Exposed worn steel edges', (0.18, 0.17, 0.13), 0.8, 0.38)
white = weathered('Aged ivory stencil', (0.75, 0.69, 0.49), (0.39, 0.34, 0.23), 0.0, 32)
red = weathered('Faded tactical red', (0.27, 0.046, 0.023), (0.12, 0.036, 0.018), 0.0, 25)
canvas = weathered('Canvas · sun-faded khaki', (0.29, 0.275, 0.16), (0.13, 0.13, 0.07), 0, 16)
wood = weathered('Weathered ash handles', (0.23, 0.13, 0.055), (0.07, 0.047, 0.026), 0, 8)

def finish(obj, name, mat, bevel=0.0, smooth=False):
    obj.name = name
    move_group(obj)
    if mat:
        obj.data.materials.append(mat)
    if bevel:
        modifier = obj.modifiers.new('Soft machined edges', 'BEVEL')
        modifier.width = bevel
        modifier.segments = 2
    if smooth:
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
    if bevel and not smooth:
        modifier = obj.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
        modifier.keep_sharp = True
    return obj

def box(name, location, dimensions, mat=paint, bevel=0.015, rotation=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if rotation:
        obj.rotation_euler = rotation
    return finish(obj, name, mat, bevel)

def cylinder(name, location, radius, depth, mat=paint, axis='Z', vertices=48, bevel=0.008):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    if axis == 'Y':
        obj.rotation_euler[0] = math.pi / 2
    elif axis == 'X':
        obj.rotation_euler[1] = math.pi / 2
    return finish(obj, name, mat, bevel, True)

def sphere(name, location, dimensions, mat=paint):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=location)
    obj = bpy.context.object
    obj.scale = dimensions
    return finish(obj, name, mat, 0, True)

def tube(name, points, radius=0.025, mat=steel):
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.resolution_u = 12
    data.bevel_depth = radius
    data.bevel_resolution = 3
    spline = data.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for point, position in zip(spline.points, points):
        point.co = (*position, 1)
    obj = bpy.data.objects.new(name, data)
    GROUP.objects.link(obj)
    data.materials.append(mat)
    return obj

def torus(name, location, major, minor, mat=steel, axis='Z'):
    bpy.ops.mesh.primitive_torus_add(major_segments=48, minor_segments=10, location=location, major_radius=major, minor_radius=minor)
    obj = bpy.context.object
    if axis == 'Y':
        obj.rotation_euler[0] = math.pi / 2
    elif axis == 'X':
        obj.rotation_euler[1] = math.pi / 2
    return finish(obj, name, mat, 0, True)

def mesh(name, vertices, faces, mat=paint, bevel=0.015):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    GROUP.objects.link(obj)
    data.materials.append(mat)
    if bevel:
        modifier = obj.modifiers.new('Armor plate edge radius', 'BEVEL')
        modifier.width = bevel
        modifier.segments = 3
        obj.modifiers.new('Plate normals', 'WEIGHTED_NORMAL')
    return obj

def bolt(location, axis='Z', radius=0.022, mat=paint_dark):
    return cylinder('Hex bolt', location, radius, 0.021, mat, axis, 6, 0.002)

def rod(name, start, end, radius, mat=steel):
    direction = Vector(end) - Vector(start)
    obj = cylinder(name, (Vector(start) + Vector(end)) / 2, radius, direction.length, mat)
    obj.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    return obj

def hollow_x(name, start, end, outer, inner, mat=steel):
    vertices = []
    for position, radius in [(start, outer), (end, outer), (start, inner), (end, inner)]:
        for index in range(64):
            angle = index * math.tau / 64
            vertices.append((position[0], position[1] + math.cos(angle) * radius, position[2] + math.sin(angle) * radius))
    faces = []
    for index in range(64):
        next_index = (index + 1) % 64
        faces.extend([(index, next_index, 64 + next_index, 64 + index), (128 + index, 192 + index, 192 + next_index, 128 + next_index), (index, 128 + index, 128 + next_index, next_index), (64 + index, 64 + next_index, 192 + next_index, 192 + index)])
    return mesh(name, vertices, faces, mat, 0.003)

box('Lower armored hull', (0, 0, 1.11), (5.6, 2.38, 0.91), paint_dark, 0.065)
box('Upper hull side armor', (0, 0, 1.78), (5.84, 2.79, 0.62), paint, 0.022)
box('Single-piece armored deck', (0, 0, 2.105), (5.88, 2.84, 0.10), paint, 0.018)
mesh('Angled glacis armor', [(-3.10,-1.40,1.24),(-3.10,1.40,1.24),(-2.93,1.40,1.72),(-2.93,-1.40,1.72),(-2.82,-1.40,1.26),(-2.82,1.40,1.26),(-2.72,1.40,1.75),(-2.72,-1.40,1.75)], [(0,1,2,3),(4,7,6,5),(0,4,5,1),(3,2,6,7),(0,3,7,4),(1,5,6,2)])
box('Vertical front plate', (-2.969,0,1.925), (0.11,2.78,0.38), paint, 0.025)
box('Lower nose armor', (-2.86,0,0.975), (0.24,2.38,0.37), paint_dark, 0.035, (0,-0.19,0))
for side in [-1,1]:
    for index in range(4):
        box('Segmented side mudguard', (-2.19+index*1.43,side*1.565,1.60), (1.40,0.43,0.047), paint, 0.008, (side*0.06,0,0))
        for offset in [-0.53,0.53]:
            bolt((-2.19+index*1.43+offset,side*1.43,1.633))
        box('Mudguard seam bracket', (-2.19+index*1.43,side*1.42,1.52), (0.08,0.08,0.22), paint_dark, 0.007)
    box('Front track mud flap', (-3.13,side*1.52,1.34), (0.085,0.71,0.45), paint, 0.016, (0,-0.27,0))
    box('Rear track mud flap', (3.04,side*1.52,1.35), (0.08,0.72,0.38), paint, 0.012, (0,0.20,0))
    for front in [-1,1]:
        box('Tow lug mount', (front*2.99,side*0.94,1.16), (0.22,0.18,0.26), paint, 0.018)
        torus('Heavy towing shackle', (front*3.13,side*0.94,1.12),0.103,0.035,edge,'Y')
        cylinder('Shackle pin', (front*3.05,side*0.94,1.23),0.035,0.27,steel,'Y')

GROUP = collection('02 · Suspension / interleaved wheels')
for side in [-1,1]:
    for index in range(8):
        xpos = -2.04 + index*0.575
        ypos = side*(1.43 if index%2 else 1.68)
        rod('Torsion bar suspension arm',(xpos+0.19,side*1.15,0.96),(xpos,ypos,0.64),0.085,paint_dark)
        cylinder('Rubber rim · road wheel',(xpos,ypos,0.62),0.445,0.19,rubber,'Y')
        cylinder('Pressed road wheel steel dish',(xpos,ypos+side*0.105,0.62),0.378,0.045,paint,'Y')
        torus('Wheel dish rim',(xpos,ypos+side*0.133,0.62),0.331,0.018,paint_dark,'Y')
        cylinder('Wheel concentric bearing cover',(xpos,ypos+side*0.141,0.62),0.153,0.06,paint_dark,'Y')
        cylinder('Wheel axle cap',(xpos,ypos+side*0.18,0.62),0.095,0.07,paint,'Y')
        for index_bolt in range(8):
            angle = index_bolt*math.tau/8
            bolt((xpos+0.245*math.cos(angle),ypos+side*0.137,0.62+0.245*math.sin(angle)),'Y',0.019)
        for index_bolt in range(6):
            angle = index_bolt*math.tau/6
            bolt((xpos+0.113*math.cos(angle),ypos+side*0.19,0.62+0.113*math.sin(angle)),'Y',0.014,edge)
        if index%2:
            cylinder('Inner interleaved wheel',(xpos,side*1.25,0.62),0.438,0.13,rubber,'Y')
    for xpos in [-2.59,2.59]:
        cylinder('Drive sprocket' if xpos<0 else 'Track idler',(xpos,side*1.50,0.77),0.50,0.42,steel,'Y')
        cylinder('Sprocket face',(xpos,side*1.744,0.77),0.424,0.055,paint,'Y')
        torus('Sprocket outer machined ring',(xpos,side*1.78,0.77),0.385,0.032,edge,'Y')
        cylinder('Final drive hub',(xpos,side*1.785,0.77),0.175,0.085,paint_dark,'Y')
        cylinder('Final drive cover',(xpos,side*1.837,0.77),0.10,0.035,paint,'Y')
        for spoke in range(10):
            angle = spoke*math.tau/10
            cylinder('Sprocket recessed lightening hole',(xpos+0.285*math.cos(angle),side*1.78,0.77+0.285*math.sin(angle)),0.06,0.009,black,'Y',24,0.002)
            bolt((xpos+0.139*math.cos(angle),side*1.835,0.77+0.139*math.sin(angle)),'Y',0.018,steel)
        for tooth in range(22):
            angle = tooth*math.tau/22
            box('Sprocket tooth',(xpos+0.51*math.cos(angle),side*1.5,0.77+0.51*math.sin(angle)),(0.10,0.41,0.09),edge,0.009,(0,-angle,0))

GROUP = collection('03 · Individual cast steel track links')
track_prototype = []
track_prototype.append(box('Track shoe', (0,0,0), (0.165,0.72,0.072),steel,0.008))
track_prototype.append(box('Raised worn grouser', (0,0,0.046), (0.039,0.71,0.032),edge,0.005))
for offset in [-0.25,0,0.25]:
    track_prototype.append(box('Cast track face rib',(0.048,offset,0.038),(0.050,0.16,0.025),steel,0.004))
track_prototype.append(cylinder('Track hinge pin',(0.077,0,-0.008),0.029,0.78,edge,'Y',16,0.003))
for offset in [-0.13,0.13]:
    track_prototype.append(box('Track guide tooth',(0,offset,-0.062),(0.064,0.046,0.091),steel,0.008))
bpy.ops.object.select_all(action='DESELECT')
for obj in track_prototype:
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for modifier in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=modifier.name)
bpy.context.view_layer.objects.active = track_prototype[0]
bpy.ops.object.join()
prototype = bpy.context.object
prototype.name = 'Track link master'
radius = 0.61
straight = 5.18
perimeter = 2*straight+math.tau*radius
count = round(perimeter/0.179)
def track_path(distance):
    if distance < straight:
        xpos = -2.59+distance
        return xpos,1.38-0.072*math.sin(math.pi*distance/straight),0
    distance -= straight
    if distance < math.pi*radius:
        angle = math.pi/2-distance/radius
        return 2.59+radius*math.cos(angle),0.77+radius*math.sin(angle),math.pi/2-angle
    distance -= math.pi*radius
    if distance < straight:
        return 2.59-distance,0.16,math.pi
    distance -= straight
    angle = -math.pi/2-distance/radius
    return -2.59+radius*math.cos(angle),0.77+radius*math.sin(angle),math.pi/2-angle
for side in [-1,1]:
    for index in range(count):
        xpos,zpos,rotation = track_path(index*perimeter/count)
        obj = bpy.data.objects.new(f'Track {side:+d} · link {index:03d}',prototype.data)
        GROUP.objects.link(obj)
        obj.location = (xpos,side*1.50,zpos)
        obj.rotation_euler[1] = rotation
bpy.data.objects.remove(prototype,do_unlink=True)

GROUP = collection('04 · Turret and 88 mm gun')
cylinder('Turret race bearing',(-0.25,0,2.20),1.035,0.14,steel,'Z',96)
cylinder('Turret base rim',(-0.25,0,2.275),1.12,0.075,paint_dark,'Z',96)
outline = [(-1.47,-0.73),(-1.27,-1.0),(-0.52,-1.16),(0.35,-1.13),(0.92,-0.85),(1.13,-0.43),(1.16,0),(1.13,0.43),(0.92,0.85),(0.35,1.13),(-0.52,1.16),(-1.27,1.0),(-1.47,0.73)]
vertices = [(xpos,ypos,2.30) for xpos,ypos in outline]+[(xpos*0.96,ypos*0.97,3.12) for xpos,ypos in outline]
length = len(outline)
faces = [tuple(reversed(range(length))),tuple(range(length,2*length))]
faces += [(index,(index+1)%length,(index+1)%length+length,index+length) for index in range(length)]
mesh('Tiger horseshoe turret · rolled armor',vertices,faces,paint,0.075)
box('Turret rear stowage bin',(1.22,0,2.83),(0.54,1.90,0.60),paint,0.05)
box('Stowage bin lid',(1.23,0,3.147),(0.60,1.98,0.045),paint_dark,0.018)
for side in [-1,1]:
    box('Bin latch',(1.517,side*0.61,2.97),(0.035,0.07,0.19),steel,0.006)
    box('Bin latch buckle',(1.54,side*0.61,2.92),(0.028,0.105,0.06),paint,0.004)
box('Cast gun mantlet',(-1.48,0,2.69),(0.36,1.38,0.68),paint,0.12)
cylinder('Gun mounting collar',(-1.715,0,2.70),0.265,0.19,paint,'X',64,0.03)
cylinder('Recoil sleeve',(-1.94,0,2.70),0.18,0.45,paint,'X',64,0.012)
bpy.ops.mesh.primitive_cone_add(vertices=64,radius1=0.095,radius2=0.135,depth=3.21,location=(-3.70,0,2.70),rotation=(0,math.pi/2,0))
finish(bpy.context.object,'88 mm KwK 36 · tapered barrel',paint,0.006,True)
for xpos,radius_band in [(-2.17,0.139),(-4.82,0.107),(-5.29,0.12)]:
    cylinder('Barrel collar',(xpos,0,2.70),radius_band,0.065,paint_dark,'X',64)
brake = hollow_x('Twin-chamber muzzle brake',(-5.88,0,2.70),(-5.28,0,2.70),0.185,0.09,paint_dark)
for xpos in [-5.70,-5.43]:
    cutter = box('Muzzle gas port cutter',(xpos,0,2.70),(0.145,0.60,0.18),None,0)
    bpy.context.view_layer.objects.active = brake
    modifier = brake.modifiers.new('Open transverse brake port','BOOLEAN')
    modifier.operation = 'DIFFERENCE'
    modifier.object = cutter
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter,do_unlink=True)
hollow_x('Muzzle face lip',(-5.94,0,2.70),(-5.88,0,2.70),0.174,0.087,edge)
cylinder('Dark bore deep inside barrel',(-5.29,0,2.70),0.086,0.012,black,'X',64,0)
for side in [-1,1]:
    for zpos in [2.47,2.92]:
        bolt((-1.68,side*0.52,zpos),'X',0.031)
    torus('Turret lifting eye',(-0.72,side*0.99,3.15),0.076,0.022,steel,'X')
    cylinder('Side pistol port',(0.59,side*1.027,2.71),0.117,0.10,paint_dark,'Y')
    cylinder('Pistol port armored cover',(0.59,side*1.082,2.71),0.097,0.025,paint,'Y')
    tube('Turret roof grab handle',[(-0.91,side*0.72,3.13),(-0.91,side*0.72,3.23),(-0.47,side*0.72,3.23),(-0.47,side*0.72,3.13)],0.017,edge)
    for xpos in [-1.08,-0.92,-0.76]:
        rod('Smoke launcher',(xpos,side*1.08,2.97),(xpos-0.10,side*1.23,3.16),0.046,paint_dark)
        cylinder('Smoke canister cap',(xpos-0.10,side*1.23,3.16),0.047,0.035,steel)
cylinder('Commander cupola base',(0.27,-0.49,3.16),0.395,0.10,paint_dark)
cylinder('Early drum cupola',(0.27,-0.49,3.33),0.354,0.29,paint)
for index in range(6):
    angle = index*math.tau/6
    obj = box('Cupola vision block',(0.27+0.352*math.cos(angle),-0.49+0.352*math.sin(angle),3.35),(0.035,0.15,0.06),black,0.007)
    obj.rotation_euler[2] = angle
cylinder('Commander hatch rim',(0.27,-0.49,3.505),0.382,0.055,paint_dark)
cylinder('Commander closed hatch',(0.27,-0.49,3.54),0.348,0.045,paint)
tube('Commander hatch handle',[(0.17,-0.49,3.57),(0.17,-0.49,3.65),(0.39,-0.49,3.65),(0.39,-0.49,3.57)],0.017)
cylinder('Loader hatch',(0.06,0.54,3.17),0.31,0.07,paint_dark)
cylinder('Loader hatch armor',(0.06,0.54,3.21),0.28,0.035,paint)
tube('Loader grab handle',[(-0.05,0.54,3.23),(-0.05,0.54,3.31),(0.17,0.54,3.31),(0.17,0.54,3.23)],0.015)
cylinder('Roof ventilator',(-0.84,0,3.18),0.15,0.12,paint_dark)
cylinder('Ventilator armored cover',(-0.84,0,3.255),0.19,0.04,paint)
for xpos in [-0.86,-0.45,-0.04,0.37,0.78]:
    for side in [-1,1]:
        bolt((xpos,side*0.83,3.134),'Z',0.018)
rod('Radio aerial mount',(0.79,0.89,3.01),(0.79,0.89,3.26),0.037,black)
tube('Flexible radio aerial',[(0.79,0.89,3.25),(0.80,0.90,3.95),(0.85,0.91,4.65),(0.94,0.93,5.05)],0.006,edge)

GROUP = collection('05 · Deck fittings and field equipment')
box('Driver vision surround',(-3.038,-0.67,1.95),(0.06,0.52,0.20),paint_dark,0.025)
box('Driver black vision slit',(-3.074,-0.67,1.97),(0.018,0.37,0.045),black,0.007)
box('Driver armored visor',(-3.093,-0.67,2.037),(0.06,0.48,0.071),paint,0.01)
sphere('Hull MG ball mount',(-3.03,0.64,1.94),(0.12,0.18,0.18),paint_dark)
cylinder('Hull machine gun',(-3.29,0.64,1.94),0.034,0.40,steel,'X',32)
hollow_x('MG muzzle opening',(-3.52,0.64,1.94),(-3.46,0.64,1.94),0.04,0.019,black)
for side in [-1,1]:
    cylinder('Front crew hatch',(-2.15,side*0.71,2.18),0.30,0.065,paint_dark)
    cylinder('Front crew hatch lid',(-2.15,side*0.71,2.218),0.275,0.033,paint)
    box('Hatch hinge',(-1.9,side*0.71,2.23),(0.13,0.30,0.08),paint,0.008)
    tube('Crew hatch grip',[(-2.28,side*0.71,2.24),(-2.28,side*0.71,2.31),(-2.09,side*0.71,2.31),(-2.09,side*0.71,2.24)],0.013)
    rod('Headlamp mounting stalk',(-2.90,side*1.13,2.09),(-2.90,side*1.13,2.24),0.022,paint_dark)
    cylinder('Bosch blackout headlamp housing',(-2.94,side*1.13,2.28),0.112,0.15,paint,'X')
    cylinder('Blackout headlamp face',(-3.024,side*1.13,2.28),0.093,0.015,black,'X')
    box('Blackout headlamp shield',(-3.035,side*1.13,2.31),(0.02,0.18,0.099),paint,0.015)
    box('Blackout headlamp lower shield',(-3.035,side*1.13,2.225),(0.02,0.17,0.055),paint,0.015)
    tube('Headlamp armored wire',[(-2.9,side*1.13,2.10),(-2.72,side*1.13,2.165),(-2.52,side*0.91,2.165)],0.008,black)
    box('Engine fan grille well',(1.99,side*0.72,2.172),(1.31,0.82,0.055),black,0.01)
    for rib in range(16):
        box('Engine grille slat',(1.39+rib*0.08,side*0.72,2.208),(0.032,0.77,0.041),paint_dark,0.004)
    for xpos in [1.36,2.65]:
        box('Grille surround',(xpos,side*0.72,2.213),(0.055,0.87,0.04),paint,0.004)
    for ypos in [side*0.29,side*1.15]:
        box('Grille surround',(2.00,ypos,2.213),(1.35,0.05,0.04),paint,0.004)
    cable_points = [(-1.62,side*1.32,2.20),(-1.20,side*1.36,2.22),(0.5,side*1.36,2.21),(1.77,side*1.31,2.24),(2.59,side*1.21,2.26),(2.72,side*0.94,2.26),(2.56,side*0.83,2.25)]
    tube('Braided steel tow cable',cable_points,0.027,steel)
    for strand in range(4):
        points=[]
        for step in range(101):
            xpos=-1.2+step*0.029
            phase=step*0.92+strand*math.pi/2
            points.append((xpos,side*1.36+0.026*math.cos(phase),2.22+0.026*math.sin(phase)))
        tube('Tow cable helical strand',points,0.006,edge)
    torus('Tow cable forged eye',(-1.71,side*1.31,2.20),0.103,0.027,steel)
    for xpos in [-0.9,0.6,1.55]:
        box('Cable hold-down clamp',(xpos,side*1.35,2.22),(0.085,0.13,0.08),paint,0.006)
box('Engine center inspection panel',(2.02,0,2.17),(1.30,0.45,0.035),paint_dark,0.015)
for xpos in [1.46,2.54]:
    for ypos in [-0.16,0.16]:
        bolt((xpos,ypos,2.20))
for side in [-1,1]:
    cylinder('Rear exhaust muffler',(3.01,side*0.56,1.81),0.15,0.88,rust)
    cylinder('Exhaust outlet',(3.01,side*0.56,2.32),0.075,0.18,black)
    cylinder('Exhaust rain cover',(3.01,side*0.56,2.43),0.123,0.025,steel)
    box('Exhaust heat shield',(3.16,side*0.56,1.75),(0.15,0.44,0.70),paint_dark,0.06)
    for zpos in [1.48,1.98]:
        box('Heat shield strap',(3.25,side*0.56,zpos),(0.028,0.49,0.055),steel,0.003)
    cylinder('Feifel air filter',(2.96,side*1.09,1.96),0.18,0.63,paint_dark)
    cylinder('Air filter lid',(2.96,side*1.09,2.30),0.196,0.06,paint)
    tube('Air cleaner flexible hose',[(2.98,side*1.09,2.32),(2.71,side*1.08,2.48),(2.35,side*1.09,2.40),(2.25,side*1.10,2.24)],0.065,rubber)
rod('Shovel wooden handle',(0.00,-1.44,1.96),(1.49,-1.44,1.96),0.025,wood)
box('Shovel forged blade',(1.63,-1.44,1.96),(0.38,0.048,0.20),steel,0.035)
rod('Pickaxe handle',(0.30,1.44,1.94),(1.73,1.44,1.94),0.025,wood)
rod('Pickaxe forged head',(1.62,1.43,1.73),(1.76,1.43,2.12),0.047,steel)
for xpos in [0.38,1.18]:
    box('Tool retaining strap',(xpos,-1.445,1.96),(0.051,0.075,0.13),paint_dark,0.004)
for index in range(3):
    xpos=1.40+index*0.40
    box('Field stowage jerry can',(xpos,0.40,2.47),(0.32,0.22,0.53),paint_dark,0.044)
    for direction in [-1,1]:
        rod('Jerry can stamped X',(xpos-0.10,0.278,2.31 if direction>0 else 2.63),(xpos+0.10,0.278,2.63 if direction>0 else 2.31),0.009,paint)
    tube('Jerry can carry handle',[(xpos-0.09,0.40,2.735),(xpos-0.09,0.40,2.80),(xpos+0.09,0.40,2.80),(xpos+0.09,0.40,2.735)],0.014,paint)
roll = cylinder('Rolled canvas blanket',(2.03,-0.74,2.40),0.18,1.14,canvas,'X',48,0.035)
for xpos in [1.67,2.34]:
    torus('Canvas retaining strap',(xpos,-0.74,2.40),0.181,0.021,wood,'X')
    box('Blanket strap buckle',(xpos,-0.91,2.47),(0.078,0.023,0.059),steel,0.006)

GROUP = collection('06 · Painted markings and weld details')
def lettering(name,body,location,size,mat,rotation,offset=0):
    data=bpy.data.curves.new(name,'FONT')
    data.body=body
    data.align_x='CENTER'
    data.align_y='CENTER'
    data.size=size
    data.extrude=0.0004
    data.offset=offset
    obj=bpy.data.objects.new(name,data)
    GROUP.objects.link(obj)
    obj.location=location
    obj.rotation_euler=rotation
    data.materials.append(mat)
    return obj
for side in [-1,1]:
    rotation=(math.pi/2,0,0) if side<0 else (math.pi/2,0,math.pi)
    lettering('Tactical number · ivory outline','213',(-0.37,side*1.157,2.78),0.46,white,rotation,0.017)
    lettering('Tactical number · faded red','213',(-0.37,side*1.159,2.78),0.46,red,rotation)
    for width,height in [(0.39,0.13),(0.13,0.39)]:
        box('Period cross · ivory border',(0.39,side*1.401,1.84),(width,0.006,height),white,0.002)
    for width,height in [(0.31,0.072),(0.072,0.31)]:
        box('Period cross · dark center',(0.39,side*1.406,1.84),(width,0.005,height),black,0.001)
    tube('Long armor weld seam',[(-2.9,side*1.397,2.08),(2.88,side*1.397,2.08)],0.008,paint_dark)
    for index in range(120):
        xpos=random.uniform(-2.85,2.82)
        zpos=random.choice([1.53,2.07])+random.uniform(-0.012,0.012)
        box('Edge paint scar',(xpos,side*1.403,zpos),(random.uniform(0.008,0.064),0.002,random.uniform(0.002,0.009)),edge,0)
for ypos in [-1.22,1.22]:
    tube('Front glacis weld',[(-3.11,ypos,1.29),(-2.98,ypos,1.70)],0.011,paint_dark)

GROUP = collection('07 · Scanned sand and desert landscape')
sand = material('Desert sand · photographic PBR', (0.48,0.34,0.18),0,0.88)
nodes=sand.node_tree.nodes
links=sand.node_tree.links
shader=nodes.get('Principled BSDF')
coord=nodes.new('ShaderNodeTexCoord')
mapping=nodes.new('ShaderNodeVectorMath')
mapping.operation='SCALE'
mapping.inputs[3].default_value=0.19
links.new(coord.outputs['Object'],mapping.inputs[0])
for filename,channel in [('sand_diff.jpg','Base Color'),('sand_rough.jpg','Roughness')]:
    path=ASSETS/filename
    if path.exists():
        texture=nodes.new('ShaderNodeTexImage')
        texture.image=bpy.data.images.load(str(path))
        texture.projection='BOX'
        texture.projection_blend=0.25
        if channel=='Roughness':
            texture.image.colorspace_settings.name='Non-Color'
        links.new(mapping.outputs[0],texture.inputs[0])
        links.new(texture.outputs['Color'],shader.inputs[channel])
grain=nodes.new('ShaderNodeTexNoise')
grain.inputs['Scale'].default_value=190
grain.inputs['Detail'].default_value=3
links.new(coord.outputs['Object'],grain.inputs[0])
bump=nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value=0.35
bump.inputs['Distance'].default_value=0.014
links.new(grain.outputs['Fac'],bump.inputs['Height'])
normal_path=ASSETS/'sand_normal.jpg'
if normal_path.exists():
    normal_image=nodes.new('ShaderNodeTexImage')
    normal_image.image=bpy.data.images.load(str(normal_path))
    normal_image.image.colorspace_settings.name='Non-Color'
    normal_image.projection='BOX'
    links.new(mapping.outputs[0],normal_image.inputs[0])
    normal=nodes.new('ShaderNodeNormalMap')
    normal.inputs['Strength'].default_value=0.65
    links.new(normal_image.outputs['Color'],normal.inputs['Color'])
    links.new(normal.outputs[0],bump.inputs['Normal'])
links.new(bump.outputs[0],shader.inputs['Normal'])

def ground_height(xpos,ypos):
    distance=math.sqrt(xpos*xpos+ypos*ypos)
    fade=min(1,max(0,(distance-4)/15))
    undulation=fractal(Vector((xpos*0.055,ypos*0.055,0.6)),1.0,2.0,4)*0.62
    ripples=0.012*math.sin(xpos*10+ypos*3+1.5*math.sin(ypos*0.6))
    height=-0.025+undulation*fade+ripples*min(1,distance/6)
    if 2.7<xpos<24:
        for side in [-1,1]:
            track_y=side*1.50+0.009*(xpos-3)**1.6
            width=abs(ypos-track_y)
            if width<0.43:
                height-=0.045*(1-width/0.43)
                height-=0.021*(0.5+0.5*math.cos((xpos-2.7)*math.tau/0.18))
    return height

resolution=380
extent=65
vertices=[]
for row in range(resolution+1):
    ypos=-extent/2+extent*row/resolution
    for column in range(resolution+1):
        xpos=-extent/2+extent*column/resolution
        vertices.append((xpos,ypos,ground_height(xpos,ypos)))
faces=[]
for row in range(resolution):
    for column in range(resolution):
        base=row*(resolution+1)+column
        faces.append((base,base+1,base+resolution+2,base+resolution+1))
terrain=mesh('Wind-rippled sand with sunken track paths',vertices,faces,sand,0)
for polygon in terrain.data.polygons:
    polygon.use_smooth=True
dust=weathered('Compressed dark sand in track prints',(0.29,0.22,0.13),(0.18,0.125,0.07),0,20)
for side in [-1,1]:
    for index in range(95):
        xpos=3.2+index*0.183
        ypos=side*1.50+0.009*(xpos-3)**1.6
        zpos=ground_height(xpos,ypos)+0.008
        box('Compressed transverse tread impression',(xpos,ypos,zpos),(0.045,0.60,0.013),dust,0.008,(0,0,0.014*(xpos-3)))
rock_mat=weathered('Desert limestone',(0.29,0.21,0.13),(0.10,0.079,0.052),0,6)
prototypes=[]
for index in range(7):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(0,0,-20))
    obj=bpy.context.object
    for vertex in obj.data.vertices:
        vertex.co*=random.uniform(0.75,1.20)
    finish(obj,'Limestone scatter master',rock_mat,0,False)
    prototypes.append(obj)
for index in range(900):
    xpos=random.uniform(-24,30)
    ypos=random.uniform(-24,30)
    if abs(xpos)<3.7 and abs(ypos)<2.25:
        continue
    size=random.uniform(0.017,0.075) if index<820 else random.uniform(0.08,0.26)
    obj=bpy.data.objects.new('Scattered desert stone',random.choice(prototypes).data)
    GROUP.objects.link(obj)
    obj.location=(xpos,ypos,ground_height(xpos,ypos)+size*0.1)
    obj.scale=(size*random.uniform(0.8,1.5),size,size*random.uniform(0.30,0.75))
    obj.rotation_euler=(random.uniform(-0.4,0.4),random.uniform(-0.4,0.4),random.uniform(0,math.tau))
for obj in prototypes:
    bpy.data.objects.remove(obj,do_unlink=True)

GROUP = collection('08 · Natural desert lighting and cameras')
world=bpy.data.worlds.new('Goegap · real arid landscape / afternoon sun')
bpy.context.scene.world=world
world.use_nodes=True
nodes=world.node_tree.nodes
links=world.node_tree.links
background=nodes.get('Background')
hdri_path=ASSETS/'goegap_4k.hdr'
if hdri_path.exists():
    environment=nodes.new('ShaderNodeTexEnvironment')
    environment.image=bpy.data.images.load(str(hdri_path))
    coordinates=nodes.new('ShaderNodeTexCoord')
    mapping=nodes.new('ShaderNodeMapping')
    mapping.inputs['Rotation'].default_value[2]=math.radians(125)
    links.new(coordinates.outputs['Generated'],mapping.inputs[0])
    links.new(mapping.outputs[0],environment.inputs[0])
    links.new(environment.outputs[0],background.inputs['Color'])
    background.inputs['Strength'].default_value=0.75
else:
    sky=nodes.new('ShaderNodeTexSky')
    sky.sky_type='MULTIPLE_SCATTERING'
    sky.sun_elevation=math.radians(35)
    sky.sun_rotation=math.radians(140)
    sky.air_density=1.1
    sky.aerosol_density=1.8
    links.new(sky.outputs[0],background.inputs[0])
    background.inputs[1].default_value=0.3
bpy.ops.object.light_add(type='SUN',location=(-10,-8,12))
sun=move_group(bpy.context.object)
sun.name='Saharan afternoon sun'
sun.rotation_euler=Vector((0.5,0.35,-0.95)).to_track_quat('-Z','Y').to_euler()
sun.data.energy=2.2
sun.data.angle=math.radians(1.2)
sun.data.color=(1.0,0.89,0.72)

def camera(name,location,target,lens):
    bpy.ops.object.camera_add(location=location)
    obj=move_group(bpy.context.object)
    obj.name=name
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    obj.data.lens=lens
    obj.data.clip_end=1500
    obj.data.dof.use_dof=True
    obj.data.dof.focus_distance=(Vector(target)-obj.location).length
    obj.data.dof.aperture_fstop=9
    return obj

hero=camera('Camera · hero three-quarter',(-11.7,-13.8,5.3),(-0.8,0,1.70),49)
camera('Camera · low armor detail',(-8.0,-10.6,3.50),(-0.85,-0.10,1.76),56)
scene=bpy.context.scene
scene.camera=hero
scene.render.engine='CYCLES'
scene.cycles.samples=192
scene.cycles.use_denoising=True
scene.cycles.adaptive_threshold=0.025
scene.cycles.max_bounces=8
scene.cycles.diffuse_bounces=4
scene.cycles.glossy_bounces=4
scene.render.resolution_x=2560
scene.render.resolution_y=1600
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGB'
scene.render.image_settings.color_depth='8'
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-0.35
scene.render.film_transparent=False
scene.render.filepath=str(ROOT/'renders'/'desert_tiger_hero.png')
scene.render.image_settings.compression=30
scene.unit_settings.system='METRIC'
scene['Asset']='Early Tiger I / North Africa, 1943 · artistic reconstruction'
scene['External assets']='Poly Haven goegap HDRI and aerial_sand PBR / CC0'
scene['Build seed']=1943
scene['Instructions']='Numpad 0: camera. F12: render. Collections separate all editable components.'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.clip_end=1500
            area.spaces.active.shading.type='MATERIAL'
            area.spaces.active.overlay.show_overlays=False
for image in bpy.data.images:
    if image.source=='FILE':
        image.pack()
(ROOT/'renders').mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'desert_tiger.blend'))
print('SCENE_READY',len(bpy.data.objects),'objects',flush=True)
