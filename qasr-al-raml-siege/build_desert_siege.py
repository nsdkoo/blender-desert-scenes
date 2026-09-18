import bpy
import math
import random
import os
import sys
import json
from mathutils import Vector


random.seed(47)
OUT = os.path.dirname(os.path.abspath(__file__))
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PREVIEW = '--preview' in ARGS
scene = bpy.context.scene
for obj in list(scene.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
scene.name = 'QASR AL RAML | The Last Amber Light'
groups = {}
for name in ['01 Terrain', '02 Fortress', '03 Courtyard', '04 Siege Works', '05 Soldiers', '06 Camp', '07 Atmosphere', '08 Lighting']:
    group = bpy.data.collections.new(name)
    scene.collection.children.link(group)
    groups[name] = group
active_group = groups['01 Terrain']


def move(obj, name, material=None):
    obj.name = name
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    active_group.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    return obj


def material(name, color, roughness=0.8, metallic=0.0, noise=0.0, scale=5):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    shader = nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    if noise:
        tex = nodes.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value = scale
        tex.inputs['Detail'].default_value = 4
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = 0.18
        ramp.color_ramp.elements[0].color = (*(value * 0.57 for value in color), 1)
        ramp.color_ramp.elements[1].position = 0.82
        ramp.color_ramp.elements[1].color = (*(min(1, value * 1.3) for value in color), 1)
        links.new(tex.outputs['Fac'], ramp.inputs[0])
        links.new(ramp.outputs['Color'], shader.inputs['Base Color'])
        bump = nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = 0.38
        bump.inputs['Distance'].default_value = noise
        links.new(tex.outputs['Fac'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    return mat


stone = [material('Sandstone / weathered variation %02d' % index, (0.40 + index * 0.025, 0.285 + index * 0.020, 0.175 + index * 0.014), noise=0.10, scale=6) for index in range(7)]
mortar = material('Recessed sandy mortar', (0.23, 0.165, 0.105), noise=0.09)
sand = material('Wind combed ochre sand', (0.53, 0.345, 0.17), noise=0.06, scale=3)
nodes = sand.node_tree.nodes
links = sand.node_tree.links
wave = nodes.new('ShaderNodeTexWave')
wave.wave_type = 'BANDS'
wave.bands_direction = 'X'
wave.inputs['Scale'].default_value = 34
wave.inputs['Distortion'].default_value = 7
wave.inputs['Detail Scale'].default_value = 1.8
fine = nodes.new('ShaderNodeBump')
fine.inputs['Strength'].default_value = 0.22
fine.inputs['Distance'].default_value = 0.035
links.new(wave.outputs['Color'], fine.inputs['Height'])
old_bump = next(node for node in nodes if node.bl_idname == 'ShaderNodeBump' and node != fine)
links.new(old_bump.outputs['Normal'], fine.inputs['Normal'])
links.new(fine.outputs['Normal'], nodes.get('Principled BSDF').inputs['Normal'])
wood = material('Dry oak / grain', (0.125, 0.064, 0.025), noise=0.06, scale=5)
woodlight = material('Exposed split timber', (0.26, 0.14, 0.062), noise=0.045, scale=8)
steel = material('Hammered iron', (0.19, 0.225, 0.24), 0.36, 0.82, 0.014, 42)
edge = material('Worn steel edges', (0.43, 0.47, 0.47), 0.29, 0.85, 0.005, 65)
dark = material('Blackened iron', (0.035, 0.029, 0.025), 0.5, 0.7)
mail = material('Dark chain mail', (0.12, 0.13, 0.125), 0.58, 0.72, 0.024, 100)
leather = material('Scuffed leather', (0.055, 0.027, 0.013), noise=0.017, scale=28)
red = material('Besiegers / oxblood linen', (0.24, 0.025, 0.013), noise=0.018, scale=50)
teal = material('Garrison / faded petrol blue', (0.025, 0.13, 0.14), noise=0.018, scale=50)
gold = material('Ochre heraldry', (0.74, 0.43, 0.10), 0.65, 0.15)
cloth = material('Dusty tent canvas', (0.55, 0.405, 0.25), noise=0.025, scale=35)
skin = material('Sun weathered skin', (0.30, 0.15, 0.073), noise=0.009, scale=25)
deadwood = material('Dry thorn branches', (0.145, 0.095, 0.036), noise=0.03)
coal = material('Ash and char', (0.022, 0.015, 0.012), noise=0.07)


def mesh(name, verts, faces, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    active_group.objects.link(obj)
    if mat:
        data.materials.append(mat)
    return obj


cube_cache = {}


def box(name, loc, dims, mat, bevel=0.025):
    key = (tuple(round(value, 4) for value in dims), mat.name, bevel)
    if key in cube_cache:
        obj = bpy.data.objects.new(name, cube_cache[key])
        active_group.objects.link(obj)
        obj.location = loc
        return obj
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = move(bpy.context.object, name, mat)
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        modifier = obj.modifiers.new('Chipped edge softness', 'BEVEL')
        modifier.width = bevel
        modifier.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        modifier = obj.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    cube_cache[key] = obj.data
    return obj


def sphere(name, loc, scale, mat, sub=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=1, location=loc)
    obj = move(bpy.context.object, name, mat)
    obj.scale = scale
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def rod(name, start, end, radius, mat, radius2=None, vertices=10):
    delta = Vector(end) - Vector(start)
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius, radius2=radius if radius2 is None else radius2, depth=delta.length, location=(Vector(start) + Vector(end)) / 2)
    obj = move(bpy.context.object, name, mat)
    obj.rotation_euler = delta.to_track_quat('Z', 'Y').to_euler()
    return obj


def path(name, points, radius, mat):
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.resolution_u = 1
    data.bevel_depth = radius
    data.bevel_resolution = 1
    spline = data.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for point, coords in zip(spline.points, points):
        point.co = (*coords, 1)
    obj = bpy.data.objects.new(name, data)
    active_group.objects.link(obj)
    data.materials.append(mat)
    return obj


def terrain_height(horizontal, depth):
    blend = 1 - math.exp(-max(0, abs(horizontal) - 16) / 12)
    return -0.13 + blend * (0.7 + 0.85 * math.sin(horizontal * 0.12 + depth * 0.13) + 0.55 * math.sin(depth * 0.28)) + 0.06 * math.sin(horizontal * 0.7 + depth * 0.24)


verts = []
faces = []
count = 180
for row in range(count + 1):
    depth = -75 + row * 170 / count
    for column in range(count + 1):
        horizontal = -105 + column * 210 / count
        verts.append((horizontal, depth, terrain_height(horizontal, depth)))
for row in range(count):
    for column in range(count):
        index = row * (count + 1) + column
        faces.append((index, index + 1, index + count + 2, index + count + 1))
ground = mesh('Continuous dune field', verts, faces, sand)
for polygon in ground.data.polygons:
    polygon.use_smooth = True
for index in range(22):
    horizontal = random.uniform(-95, 90)
    depth = random.uniform(52, 90)
    peak = sphere('Distant eroded desert ridge', (horizontal, depth, -1), (random.uniform(7, 19), random.uniform(7, 13), random.uniform(3, 10)), stone[2], 2)
for index in range(580):
    horizontal = random.uniform(-34, 32)
    depth = random.uniform(-28, 28)
    if abs(horizontal) < 3 and depth > -8:
        continue
    size = random.uniform(0.025, 0.20)
    rock = sphere('Wind polished rubble', (horizontal, depth, terrain_height(horizontal, depth) + size * 0.3), (size * 1.7, size, size * 0.6), random.choice(stone), 1)
    rock.rotation_euler = (random.random(), random.random(), random.random() * 6)
for index in range(48):
    horizontal = random.uniform(-33, 33)
    depth = random.uniform(-27, 20)
    if abs(horizontal) < 7:
        continue
    base = Vector((horizontal, depth, terrain_height(horizontal, depth)))
    for branch in range(random.randint(4, 7)):
        tip = base + Vector((random.uniform(-0.38, 0.38), random.uniform(-0.32, 0.32), random.uniform(0.2, 0.65)))
        elbow = base.lerp(tip, 0.58)
        path('Desiccated thorn scrub', [base, elbow, tip], 0.018, deadwood)
        twig = elbow + Vector((random.uniform(-0.22, 0.22), random.uniform(-0.2, 0.2), 0.12))
        rod('Thorn fork', elbow, twig, 0.01, deadwood, 0.002, 5)

active_group = groups['02 Fortress']


def wall(left, right, depth, height=7.4, damaged=False):
    width = right - left
    columns = round(width / 1.18)
    step = width / columns
    for row in range(round(height / 0.47)):
        for column in range(columns):
            horizontal = left + (column + 0.5) * step + (0.22 if row % 2 else -0.22)
            level = 0.24 + row * 0.47
            breach = damaged and abs(horizontal - 11.8) < max(0, (level - 2.7) * 0.62) + random.uniform(-0.2, 0.3)
            if breach:
                continue
            box('Curtain wall / coursed limestone', (horizontal, depth, level), (step - 0.028, 1.65, 0.443), random.choice(stone), 0.035)
    for horizontal in [left + 0.6 + index * 1.42 for index in range(int(width / 1.42))]:
        if damaged and abs(horizontal - 11.8) < 3:
            continue
        box('Parapet merlon', (horizontal, depth - 0.48, height + 0.56), (0.81, 0.78, 1.15), random.choice(stone), 0.055)
        box('Parapet cap stone', (horizontal, depth - 0.48, height + 1.16), (0.91, 0.85, 0.15), stone[4])
    if not damaged:
        box('Wall walk', ((left + right) / 2, depth + 0.35, height - 0.15), (width, 2.3, 0.3), stone[3])


def tower(horizontal, depth, radius, height, label):
    segments = 24
    rows = round(height / 0.49)
    for row in range(rows):
        level = 0.245 + row * 0.49
        for segment in range(segments):
            angle = (segment + (0.5 if row % 2 else 0)) * math.tau / segments
            if (3.6 < level < 5.2 or 7.3 < level < 8.6) and math.sin(angle) < -0.985:
                continue
            block = box(label + ' / radial ashlar', (horizontal + radius * math.cos(angle), depth + radius * math.sin(angle), level), (math.tau * radius / segments - 0.015, 0.56, 0.46), random.choice(stone), 0.03)
            block.rotation_euler.z = angle + math.pi / 2
    rod(label + ' / shadowed inner core', (horizontal, depth, 0), (horizontal, depth, height - 0.2), radius - 0.32, mortar, vertices=32)
    for bandlevel in [0.22, height - 0.7, height - 0.2]:
        for segment in range(segments):
            angle = segment * math.tau / segments
            block = box('Projecting tower string course', (horizontal + radius * math.cos(angle), depth + radius * math.sin(angle), bandlevel), (math.tau * radius / segments + 0.04, 0.72, 0.19), stone[4])
            block.rotation_euler.z = angle + math.pi / 2
    rod('Tower fighting platform', (horizontal, depth, height - 0.3), (horizontal, depth, height), radius + 0.12, stone[3], vertices=32)
    for segment in range(12):
        angle = segment * math.tau / 12
        block = box('Tower crown / crenellation', (horizontal + radius * math.cos(angle), depth + radius * math.sin(angle), height + 0.55), (0.82, 0.72, 1.15), random.choice(stone), 0.045)
        block.rotation_euler.z = angle + math.pi / 2
        cap = box('Tower crenellation cap', (horizontal + radius * math.cos(angle), depth + radius * math.sin(angle), height + 1.15), (0.94, 0.81, 0.15), stone[4])
        cap.rotation_euler.z = angle + math.pi / 2
    for slotlevel in [4.35, 8.0]:
        box('Arrow slit / deep shadow', (horizontal, depth - radius + 0.3, slotlevel), (0.19, 0.045, 1.12), dark, 0)
        box('Arrow slit / cross aperture', (horizontal, depth - radius + 0.28, slotlevel), (0.53, 0.045, 0.14), dark, 0)


wall(-19, -6, 5.8)
wall(6, 20, 5.8, damaged=True)
tower(-5.5, 5.5, 2.45, 11.3, 'Western gate bastion')
tower(5.5, 5.5, 2.45, 11.3, 'Eastern gate bastion')
tower(-19, 7.2, 2.5, 9.2, 'Western arrow tower')
tower(20, 7.2, 2.5, 8.7, 'Ruined eastern tower')
wall(-19, 20, 24, 7.0)
for side in [-19, 20]:
    box('Castle return wall', (side, 16, 3.5), (1.5, 18, 7), stone[1], 0.1)
    for depth in range(8, 25, 2):
        box('Return wall battlement', (side, depth, 7.55), (1.1, 0.9, 1.1), stone[3])
tower(-14, 21, 3.0, 14.5, 'High watch keep')
for horizontal in [-3.23, 3.23]:
    for row in range(9):
        box('Gateway pier', (horizontal, 4.62, row * 0.48 + 0.24), (0.68, 2.15, 0.455), stone[4])
for index in range(19):
    first = index * math.pi / 19 + 0.008
    second = (index + 1) * math.pi / 19 - 0.008
    verts = [(radius * math.cos(angle), depth, 4.2 + radius * math.sin(angle)) for depth in [3.48, 5.85] for radius, angle in [(2.88, first), (3.55, first), (3.55, second), (2.88, second)]]
    mesh('Arched gate / wedge shaped voussoir', verts, [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], stone[4 if index % 3 else 6])
for row in range(5):
    for column in range(7):
        box('Gatehouse upper masonry', ((column - 3) * 0.97, 4.8, 7.62 + row * 0.46), (0.94, 2.0, 0.44), random.choice(stone))
for horizontal in [-2.9, -1.45, 0, 1.45, 2.9]:
    box('Gatehouse crown', (horizontal, 4.1, 10.32), (0.8, 0.9, 1.05), stone[3])
for side in [-1, 1]:
    before = set(active_group.objects)
    for plank in range(9):
        horizontal = side * (0.15 + plank * 0.30)
        height = 4.2 + math.sqrt(max(0, 2.75 ** 2 - horizontal ** 2))
        box('Oak gate / individual plank', (horizontal, 5.25, height / 2), (0.285, 0.22, height), wood, 0.015)
    for level in [0.85, 2.55, 4.0]:
        box('Forged gate strap', (side * 1.40, 5.10, level), (2.7, 0.12, 0.17), dark)
        for horizontal in [0.3, 0.9, 1.5, 2.1, 2.6]:
            sphere('Gate iron rivet', (side * horizontal, 5.02, level), (0.045, 0.025, 0.045), edge, 1)
    pivot = bpy.data.objects.new('Partly breached gate leaf', None)
    active_group.objects.link(pivot)
    pivot.location = (side * 2.85, 5.25, 0)
    for obj in set(active_group.objects) - before - {pivot}:
        obj.parent = pivot
        obj.location -= pivot.location
    pivot.rotation_euler.z = side * math.radians(47 if side == 1 else 24)
for index in range(100):
    horizontal = random.gauss(11.9, 1.7)
    depth = random.uniform(1.6, 8.2)
    block = box('Collapsed breach / fallen stone', (horizontal, depth, random.uniform(0.05, 0.5)), (random.uniform(0.3, 0.95), random.uniform(0.3, 0.7), random.uniform(0.2, 0.55)), random.choice(stone), 0.06)
    block.rotation_euler = (random.uniform(-0.5, 0.5), random.uniform(-0.7, 0.7), random.random() * 6)


def flag(horizontal, depth, base, height, mat, width=1.7):
    rod('Banner ash pole', (horizontal, depth, base), (horizontal, depth, base + height + 0.2), 0.044, woodlight)
    rod('Banner spear finial', (horizontal, depth, base + height + 0.2), (horizontal, depth, base + height + 0.55), 0.085, gold, 0, 8)
    verts = []
    faces = []
    for column in range(21):
        across = column / 20
        for row in range(9):
            down = row / 8
            verts.append((horizontal + across * width, depth + (math.sin(across * 8 - down * 2) * 0.20 + math.sin(across * 15 + down) * 0.07) * across, base + height - down * 1.2 - 0.2 * across + 0.11 * math.sin(across * 7 + down * 2)))
    for column in range(20):
        for row in range(8):
            index = column * 9 + row
            faces.append((index, index + 9, index + 10, index + 1))
    obj = mesh('Wind torn faction banner', verts, faces, mat)
    obj.data.materials.append(gold)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
        if polygon.index % 8 == 6:
            polygon.material_index = 1
    modifier = obj.modifiers.new('Woven cloth thickness', 'SOLIDIFY')
    modifier.thickness = 0.008


flag(-5.5, 5.6, 11.3, 3.5, teal, 2.2)
flag(5.5, 5.6, 11.3, 3.7, teal, 2.2)
flag(-14, 21, 14.5, 3, teal, 2.6)
flag(-19, 7.2, 9.2, 2.9, teal)
for horizontal in [-5.5, 5.5]:
    banner = box('Hanging garrison standard', (horizontal, 2.76, 7.0), (1.0, 0.04, 2.5), teal, 0.01)
    box('Standard ochre vertical device', (horizontal, 2.72, 7.0), (0.09, 0.015, 1.7), gold, 0)
    box('Standard ochre horizontal device', (horizontal, 2.715, 7.35), (0.65, 0.02, 0.09), gold, 0)

active_group = groups['03 Courtyard']
for index in range(18):
    box('Courtyard stone stair', (-10.5, 7.8 + index * 0.44, index * 0.40 / 2), (2.0, 0.47, max(0.15, index * 0.40)), stone[2])
for horizontal in range(-6, 7):
    for depth in range(7, 16):
        box('Courtyard worn paving', (horizontal * 0.82, depth, -0.03), (0.79, 0.95, 0.12), random.choice(stone), 0.035)
for horizontal in [-10, 9]:
    for offset in [-1.7, 1.7]:
        for depth in [12, 15]:
            rod('Courtyard timber shelter post', (horizontal + offset, depth, 0), (horizontal + offset, depth, 3.0), 0.09, wood)
    for offset in range(12):
        plank = box('Courtyard lean to roof', (horizontal - 1.9 + offset * 0.35, 13.5, 3.1), (0.33, 3.7, 0.11), woodlight)
        plank.rotation_euler.x = 0.12
    for index in range(4):
        box('Supply crate', (horizontal + random.uniform(-1, 1), 13 + random.random(), 0.4), (0.75, 0.65, 0.8), wood)

active_group = groups['04 Siege Works']


def ladder(horizontal, bottom_depth, top_depth, top_height):
    for offset in [-0.47, 0.47]:
        rod('Siege ladder / long oak rail', (horizontal + offset, bottom_depth, 0.05), (horizontal + offset, top_depth, top_height), 0.075, woodlight)
    for index in range(24):
        fraction = (index + 0.3) / 24
        depth = bottom_depth + fraction * (top_depth - bottom_depth)
        level = fraction * top_height
        rod('Siege ladder / rung', (horizontal - 0.53, depth, level), (horizontal + 0.53, depth, level), 0.043, woodlight)
        for offset in [-0.47, 0.47]:
            rod('Ladder lashings', (horizontal + offset, depth - 0.045, level - 0.045), (horizontal + offset, depth + 0.045, level + 0.045), 0.09, leather)


ladder(-10.8, -2.8, 5.5, 8.25)
ladder(-15.0, -1.8, 5.5, 8.25)
ladder(9.2, -2.3, 5.4, 7.5)


def wheel(horizontal, depth, level, radius):
    points = [(horizontal, depth + radius * math.cos(index * math.tau / 32), level + radius * math.sin(index * math.tau / 32)) for index in range(33)]
    path('Siege engine wheel / iron tyre', points, 0.074, dark)
    points = [(horizontal, depth + radius * 0.88 * math.cos(index * math.tau / 32), level + radius * 0.88 * math.sin(index * math.tau / 32)) for index in range(33)]
    path('Wheel / wooden felloe', points, 0.11, woodlight)
    for index in range(10):
        angle = index * math.tau / 10
        rod('Wheel spoke', (horizontal, depth, level), (horizontal, depth + radius * 0.85 * math.cos(angle), level + radius * 0.85 * math.sin(angle)), 0.047, woodlight)
    rod('Wheel axle hub', (horizontal - 0.15, depth, level), (horizontal + 0.15, depth, level), 0.14, dark)


for horizontal in [-1.0, 1.0]:
    box('Battering ram / undercarriage', (horizontal, -4.5, 0.65), (0.19, 4.4, 0.24), wood)
    for depth in [-6, -3]:
        wheel(horizontal * 1.15, depth, 0.58, 0.59)
        rod('Ram shelter upright', (horizontal, depth, 0.65), (horizontal, depth, 2.8), 0.11, wood)
for depth in [-6.4, -2.6]:
    rod('Ram shelter gable', (-1.35, depth, 2.65), (0, depth, 3.55), 0.105, wood)
    rod('Ram shelter gable', (0, depth, 3.55), (1.35, depth, 2.65), 0.105, wood)
for side in [-1, 1]:
    for index in range(14):
        plank = box('Ram protective sloped roof', (side * 0.66, -6.5 + index * 0.30, 3.10), (1.68, 0.28, 0.13), woodlight)
        plank.rotation_euler.y = side * 0.58
rod('Suspended oak battering beam', (0, -7, 1.25), (0, -1.25, 1.25), 0.24, woodlight, vertices=14)
rod('Ram iron striking head', (0, -1.70, 1.25), (0, -1.12, 1.25), 0.29, dark, vertices=12)
for depth in [-5.8, -3.1]:
    path('Battering beam suspension rope', [(0, depth, 3.1), (-0.28, depth, 1.3), (0, depth, 0.97), (0.28, depth, 1.3), (0, depth, 3.1)], 0.032, cloth)
engine_x, engine_y = -13, -12
for offset in [-1.0, 1.0]:
    box('Traction catapult / base beam', (engine_x + offset, engine_y, 0.6), (0.25, 3.4, 0.24), wood)
    for depth in [-1.1, 1.1]:
        wheel(engine_x + offset * 1.2, engine_y + depth, 0.58, 0.56)
        rod('Catapult trestle', (engine_x + offset, engine_y + depth, 0.7), (engine_x + offset, engine_y, 2.7), 0.14, woodlight)
rod('Catapult pivot axle', (engine_x - 1.35, engine_y, 2.7), (engine_x + 1.35, engine_y, 2.7), 0.17, dark)
rod('Catapult throwing arm', (engine_x, engine_y - 1.8, 0.9), (engine_x, engine_y + 2.4, 5.1), 0.16, woodlight, 0.1)
path('Catapult sling', [(engine_x, engine_y + 2.4, 5.1), (engine_x - 0.25, engine_y + 3.2, 3.9), (engine_x, engine_y + 3.5, 3.65), (engine_x + 0.25, engine_y + 3.2, 3.9), (engine_x, engine_y + 2.4, 5.1)], 0.03, leather)
sphere('Catapult sling stone', (engine_x, engine_y + 3.4, 3.8), (0.23, 0.27, 0.2), stone[1])
for index in range(7):
    sphere('Ammunition pile', (-15 + random.random(), -10 + random.random(), 0.2), (0.25, 0.25, 0.23), stone[2])

active_group = groups['05 Soldiers']
soldier_counts = {'attackers': 0, 'defenders': 0, 'poses': {}}


def sword(hand, tip):
    direction = (Vector(tip) - Vector(hand)).normalized()
    grip_end = Vector(hand) + direction * 0.14
    blade_end = Vector(tip)
    rod('Sword leather grip', Vector(hand) - direction * 0.13, grip_end, 0.028, leather)
    sphere('Sword pommel', Vector(hand) - direction * 0.15, (0.045, 0.045, 0.045), steel, 1)
    across = direction.cross(Vector((0, 1, 0))).normalized()
    if across.length < 0.1:
        across = Vector((1, 0, 0))
    rod('Sword cross guard', grip_end - across * 0.15, grip_end + across * 0.15, 0.023, edge)
    verts = [grip_end - across * 0.05, grip_end + Vector((0, -0.018, 0)), grip_end + across * 0.05, grip_end + Vector((0, 0.018, 0)), blade_end]
    mesh('Forged sword / diamond section blade', verts, [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)], edge)


def shield(center, faction):
    horizontal, depth, level = center
    outline = [(-0.34, 0.42), (0.34, 0.42), (0.35, -0.05), (0.23, -0.32), (0, -0.57), (-0.23, -0.32), (-0.35, -0.05)]
    verts = [(horizontal + offset, depth, level + height) for offset, height in outline]
    verts.append((horizontal, depth - 0.105, level))
    mesh('Heater shield / painted timber', verts, [(index, (index + 1) % 7, 7) for index in range(7)], faction)
    path('Shield iron rim', verts[:7] + [verts[0]], 0.025, edge)
    box('Shield ochre vertical heraldry', (horizontal, depth - 0.11, level + 0.015), (0.068, 0.018, 0.69), gold, 0)
    box('Shield ochre horizontal heraldry', (horizontal, depth - 0.107, level + 0.19), (0.49, 0.018, 0.067), gold, 0)
    sphere('Shield iron boss', (horizontal, depth - 0.15, level + 0.02), (0.078, 0.044, 0.078), dark, 2)
    for offset, height in outline:
        sphere('Shield rivet', (horizontal + offset * 0.88, depth - 0.02, level + height * 0.86), (0.019, 0.016, 0.019), gold, 1)


def soldier(name, loc, angle, team='attackers', pose='sword', scale=1.0):
    faction = red if team == 'attackers' else teal
    soldier_counts[team] += 1
    soldier_counts['poses'][pose] = soldier_counts['poses'].get(pose, 0) + 1
    before = set(active_group.objects)
    if pose == 'climb':
        hips = [(-0.15, 0, 0.92), (0.15, 0, 0.92)]
        knees = [(-0.20, -0.30, 0.65), (0.23, -0.28, 0.96)]
        feet = [(-0.2, -0.14, 0.15), (0.23, -0.42, 0.57)]
        elbows = [(-0.33, -0.25, 1.65), (0.36, -0.25, 1.82)]
        hands = [(-0.37, -0.44, 1.91), (0.38, -0.38, 2.12)]
    else:
        hips = [(-0.16, 0, 0.91), (0.16, 0, 0.91)]
        knees = [(-0.24, -0.17, 0.54), (0.25, 0.15, 0.54)]
        feet = [(-0.29, -0.29, 0.08), (0.34, 0.28, 0.08)]
        if pose == 'strike':
            elbows = [(-0.40, -0.16, 1.17), (0.48, 0.00, 1.77)]
            hands = [(-0.40, -0.43, 1.37), (0.24, -0.13, 2.1)]
        elif pose == 'archer':
            elbows = [(-0.31, -0.40, 1.44), (0.46, 0.0, 1.53)]
            hands = [(-0.17, -0.76, 1.46), (0.10, -0.17, 1.60)]
        elif pose == 'spear':
            elbows = [(-0.39, -0.13, 1.18), (0.42, 0.08, 1.18)]
            hands = [(-0.40, -0.42, 1.3), (0.43, -0.23, 1.30)]
        else:
            elbows = [(-0.43, -0.11, 1.18), (0.46, -0.06, 1.20)]
            hands = [(-0.41, -0.45, 1.35), (0.51, -0.45, 1.48)]
    for side in range(2):
        rod('Mail chausses / thigh', hips[side], knees[side], 0.115, mail, 0.092)
        sphere('Articulated knee plate', knees[side], (0.115, 0.13, 0.105), steel)
        rod('Leather shin', knees[side], feet[side], 0.093, leather, 0.068)
        middle = Vector(knees[side]).lerp(Vector(feet[side]), 0.48)
        sphere('Iron greave', middle + Vector((0, -0.065, 0)), (0.082, 0.061, 0.22), steel)
        sphere('Dusty leather boot', Vector(feet[side]) + Vector((0, -0.08, 0.025)), (0.10, 0.19, 0.09), leather)
    verts = [(-0.28, -0.18, 0.68), (0.28, -0.18, 0.68), (0.28, 0.18, 0.68), (-0.28, 0.18, 0.68), (-0.20, -0.15, 1.1), (0.20, -0.15, 1.1), (0.20, 0.15, 1.1), (-0.20, 0.15, 1.1)]
    mesh('Split campaign surcoat skirt', verts, [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], faction)
    sphere('Mail hauberk torso', (0, 0, 1.25), (0.275, 0.18, 0.35), mail)
    sphere('Hammered breastplate', (0, -0.097, 1.29), (0.236, 0.13, 0.285), steel)
    box('Surcoat center stripe', (0, -0.229, 1.23), (0.13, 0.018, 0.40), faction, 0.015)
    box('Leather waist belt', (0, 0, 1.015), (0.46, 0.36, 0.065), leather)
    box('Belt brass buckle', (0, -0.19, 1.015), (0.087, 0.025, 0.07), gold)
    rod('Neck mail collar', (0, 0, 1.49), (0, 0, 1.64), 0.10, mail)
    sphere('Face in helmet', (0, -0.035, 1.72), (0.119, 0.113, 0.15), skin)
    ring_verts = []
    ring_faces = []
    for row in range(8):
        polar = row / 7 * math.pi / 2
        for segment in range(16):
            azimuth = segment * math.tau / 16
            ring_verts.append((0.16 * math.cos(polar) * math.cos(azimuth), 0.15 * math.cos(polar) * math.sin(azimuth), 1.73 + 0.205 * math.sin(polar)))
    for row in range(7):
        for segment in range(16):
            index = row * 16 + segment
            next_index = row * 16 + (segment + 1) % 16
            ring_faces.append((index, next_index, next_index + 16, index + 16))
    mesh('Riveted iron helmet dome', ring_verts, ring_faces, steel)
    path('Helmet rolled brow', [(0.163 * math.cos(segment * math.tau / 32), 0.154 * math.sin(segment * math.tau / 32), 1.74) for segment in range(33)], 0.018, edge)
    box('Nasal guard', (0, -0.16, 1.695), (0.035, 0.028, 0.18), steel, 0.008)
    for side in [-1, 1]:
        guard = box('Helmet cheek guard', (side * 0.115, -0.075, 1.66), (0.052, 0.1, 0.18), steel, 0.012)
        guard.rotation_euler.y = side * -0.15
    box('Shadow under helmet brow', (0, -0.145, 1.737), (0.18, 0.023, 0.027), dark, 0)
    for side in range(2):
        shoulder = Vector(((-1 if side == 0 else 1) * 0.27, 0, 1.43))
        rod('Mail upper sleeve', shoulder, elbows[side], 0.093, mail, 0.074)
        sphere('Layered shoulder pauldron', shoulder, (0.152, 0.181, 0.115), steel)
        sphere('Elbow cop', elbows[side], (0.082, 0.086, 0.082), steel)
        rod('Armored forearm', elbows[side], hands[side], 0.078, steel, 0.047)
        sphere('Leather gauntlet', hands[side], (0.059, 0.057, 0.068), leather)
    if pose == 'archer':
        hand = Vector(hands[0])
        points = [hand + Vector((0, -0.20 * math.sin(index * math.pi / 16), (index / 16 - 0.5) * 1.12)) for index in range(17)]
        path('Yew war bow', points, 0.025, woodlight)
        path('Drawn bowstring', [points[0], hands[1], points[-1]], 0.006, cloth)
        arrow_start = Vector(hands[1]) + Vector((0, 0.15, 0))
        arrow_end = hand + Vector((0, -0.58, 0.05))
        rod('Nocked arrow shaft', arrow_start, arrow_end, 0.009, woodlight, vertices=6)
        rod('Arrow bodkin', arrow_end, arrow_end + Vector((0, -0.09, 0)), 0.025, steel, 0, 4)
        rod('Leather back quiver', (0.13, 0.21, 0.98), (0.23, 0.28, 1.55), 0.085, leather)
        for index in range(5):
            rod('Quiver arrows', (0.20 + index * 0.015, 0.28, 1.4), (0.26 + index * 0.015, 0.28, 1.80 + random.random() * 0.08), 0.008, woodlight)
    elif pose == 'spear':
        hand = Vector(hands[1])
        bottom = hand + Vector((0.12, 0.60, -1.1))
        tip = hand + Vector((-0.18, -0.95, 1.65))
        rod('Ash spear shaft', bottom, tip, 0.025, woodlight)
        rod('Leaf spear point', tip, tip + (tip - bottom).normalized() * 0.30, 0.065, edge, 0, 4)
        shield(Vector(hands[0]) + Vector((0, -0.075, -0.02)), faction)
    elif pose != 'climb':
        hand = Vector(hands[1])
        tip = hand + (Vector((0.38, 0.13, 0.85)) if pose == 'strike' else Vector((0.25, -0.75, 0.4)))
        sword(hand, tip)
        shield(Vector(hands[0]) + Vector((0, -0.075, -0.02)), faction)
    if pose not in ['archer', 'climb'] and random.random() < 0.7:
        verts = []
        for row in range(9):
            fraction = row / 8
            for column in range(7):
                across = column / 6 - 0.5
                verts.append((across * (0.43 + fraction * 0.22), 0.14 + fraction * 0.30 + 0.06 * math.sin(across * 18 + fraction * 4), 1.48 - fraction * 0.96))
        mesh('Dust worn short mantle', verts, [(row * 7 + column, row * 7 + column + 1, (row + 1) * 7 + column + 1, (row + 1) * 7 + column) for row in range(8) for column in range(6)], faction)
    root = bpy.data.objects.new(name, None)
    active_group.objects.link(root)
    for obj in set(active_group.objects) - before - {root}:
        obj.parent = root
    root.location = loc
    root.rotation_euler.z = angle
    root.scale = (scale, scale, scale)
    if pose == 'fallen':
        root.rotation_euler.x = math.pi / 2
        root.location.z += 0.22
    root['faction'] = team
    root['pose'] = pose
    return root


soldier('Foreground / crimson sword captain', (6.4, -15.2, 0), math.radians(158), pose='strike', scale=1.12)
soldier('Foreground / garrison shield guard', (6.7, -12.9, 0), math.radians(-19), team='defenders', pose='sword', scale=1.07)
soldier('Foreground / advancing spear bearer', (-2.7, -17.0, 0), math.radians(191), pose='spear', scale=1.07)
soldier('Foreground / fallen defender', (3.7, -17.7, 0), 0.5, team='defenders', pose='fallen')
soldier('Left flank / swordsman', (-7.3, -10.6, 0), 2.55, pose='sword')
for index in range(18):
    horizontal = random.uniform(-5, 5)
    depth = random.uniform(-1.7, 3.7)
    if abs(horizontal) < 1.2 and depth < 0:
        horizontal += 2.0
    team = 'attackers' if index % 2 == 0 else 'defenders'
    angle = math.pi + random.uniform(-0.6, 0.6) if team == 'attackers' else random.uniform(-0.7, 0.7)
    soldier('Gateway melee %02d' % index, (horizontal, depth, 0), angle, team, ['strike', 'sword', 'spear'][index % 3], random.uniform(0.94, 1.05))
for index, (horizontal, depth) in enumerate([(-6, -6), (-8, -4), (3, -7), (5, -5), (8, -7), (-4, -11), (0, -12), (-11, -7), (11, -4)]):
    soldier('Assault wave %02d' % index, (horizontal, depth, 0), math.pi + random.uniform(-0.4, 0.4), pose='spear' if index % 3 == 0 else 'sword')
for horizontal, bottom, top, height in [(-10.8, -2.8, 5.5, 8.25), (-15, -1.8, 5.5, 8.25), (9.2, -2.3, 5.4, 7.5)]:
    for fraction in [0.25, 0.64]:
        soldier('Scaling the curtain wall', (horizontal, bottom + (top - bottom) * fraction - 0.25, height * fraction - 0.1), math.pi, pose='climb', scale=0.96)
for index, horizontal in enumerate([-17.3, -13.2, -8.1, 7.6, 16.9]):
    soldier('Wall defender %02d' % index, (horizontal, 6.05, 7.42), random.uniform(-0.2, 0.2), 'defenders', 'archer' if index % 2 == 0 else 'spear')
for horizontal in [-5.5, 5.5]:
    for offset in [-0.9, 0.8]:
        soldier('Bastion archer', (horizontal + offset, 4.55, 11.3), -0.1, 'defenders', 'archer')
for loc in [(-5, -5, 0), (8, -1, 0), (-8, -13, 0)]:
    soldier('Fallen combatant', loc, random.random() * 6, 'attackers', 'fallen')
for index in range(24):
    horizontal = random.uniform(-12, 12)
    depth = random.uniform(-14, 3)
    base = Vector((horizontal, depth, 0))
    rod('Spent arrow embedded in sand', base, base + Vector((0.1, 0.3, 0.52)), 0.008, woodlight, vertices=5)
    rod('Arrow fletching', base + Vector((0.085, 0.25, 0.45)), base + Vector((0.1, 0.3, 0.53)), 0.023, cloth, vertices=4)

active_group = groups['06 Camp']
for horizontal, depth, size in [(-23, -3, 1.0), (-25, 3, 1.1), (-28, -8, 0.85), (24, 0, 0.85)]:
    height = 2.2 * size
    width = 2.0 * size
    length = 3.0 * size
    mesh('Campaign tent / pitched canvas', [(horizontal - width, depth - length, 0), (horizontal + width, depth - length, 0), (horizontal, depth - length, height), (horizontal - width, depth + length, 0), (horizontal + width, depth + length, 0), (horizontal, depth + length, height)], [(0, 2, 5, 3), (2, 1, 4, 5), (3, 5, 4)], cloth)
    for offset in [-length, length]:
        rod('Tent ridge pole', (horizontal, depth + offset, 0), (horizontal, depth + offset, height + 0.18), 0.045, wood)
        for side in [-1, 1]:
            path('Tent guy rope', [(horizontal, depth + offset, height), (horizontal + side * (width + 1), depth + offset * 1.2, 0.05)], 0.012, cloth)
            rod('Tent stake', (horizontal + side * (width + 1), depth + offset * 1.2, 0), (horizontal + side * (width + 1), depth + offset * 1.2, 0.22), 0.025, wood)
flag(-21, -7, 0, 4.4, red, 2.2)
flag(-5, -10.5, 0, 3.7, red, 1.7)


def emission(name, color, strength):
    mat = material(name, color)
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Emission Color'].default_value = (*color, 1)
    shader.inputs['Emission Strength'].default_value = strength
    return mat


flame = emission('Fire / amber flame', (1.0, 0.18, 0.006), 5)
heart = emission('Fire / hot core', (1.0, 0.62, 0.05), 8)
ember = emission('Airborne glowing embers', (1.0, 0.24, 0.013), 4)


def light(name, kind, loc, energy, color, size=1):
    data = bpy.data.lights.new(name, kind)
    data.energy = energy
    data.color = color
    if kind == 'AREA':
        data.shape = 'DISK'
        data.size = size
    elif kind == 'POINT':
        data.shadow_soft_size = size
    obj = bpy.data.objects.new(name, data)
    active_group.objects.link(obj)
    obj.location = loc
    return obj


def fire(loc, size=1):
    base = Vector(loc)
    for index in range(5):
        angle = index * math.tau / 5
        direction = Vector((math.cos(angle), math.sin(angle), 0))
        rod('Burning oak log', base - direction * 0.45 * size, base + direction * 0.45 * size + Vector((0, 0, 0.08)), 0.095 * size, coal)
    for index in range(7):
        offset = Vector((random.uniform(-0.18, 0.18), random.uniform(-0.18, 0.18), 0)) * size
        obj = sphere('Wind swept flame', base + offset + Vector((0, 0, 0.34 * size)), (0.12 * size, 0.10 * size, random.uniform(0.27, 0.60) * size), flame, 2)
        obj.rotation_euler.y = -0.24
        sphere('Golden flame core', base + offset + Vector((0, 0, 0.18 * size)), (0.08 * size, 0.07 * size, 0.24 * size), heart)
    light('Fire glow', 'POINT', base + Vector((0, 0, 0.65 * size)), 110 * size, (1, 0.25, 0.045), 0.7 * size)
    for index in range(12):
        sphere('Rising ember', base + Vector((random.uniform(-0.3, 0.3), random.uniform(-0.2, 0.2), random.uniform(0.3, 2.3))) * size, (0.012, 0.012, 0.023), ember, 1)


fire((-21, -3, 0.12), 1.2)
fire((12.5, 4, 0.7), 1.7)
fire((-7.5, 2.0, 0.15), 0.85)
for horizontal in [-3.0, 3.0]:
    rod('Gate torch iron bracket', (horizontal, 3.3, 2.6), (horizontal, 2.8, 3.0), 0.055, dark)
    rod('Gate torch handle', (horizontal, 2.8, 2.8), (horizontal, 2.8, 3.7), 0.064, wood)
    fire((horizontal, 2.8, 3.72), 0.4)

active_group = groups['07 Atmosphere']


def volume_material(name, color, density, scale=2):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    links = mat.node_tree.links
    output = nodes.new('ShaderNodeOutputMaterial')
    volume = nodes.new('ShaderNodeVolumePrincipled')
    volume.inputs['Color'].default_value = (*color, 1)
    volume.inputs['Anisotropy'].default_value = 0.35
    tex = nodes.new('ShaderNodeTexNoise')
    tex.inputs['Scale'].default_value = scale
    tex.inputs['Detail'].default_value = 3
    ramp = nodes.new('ShaderNodeMapRange')
    ramp.inputs['From Min'].default_value = 0.25
    ramp.inputs['From Max'].default_value = 0.8
    ramp.inputs['To Min'].default_value = 0
    ramp.inputs['To Max'].default_value = density
    links.new(tex.outputs['Fac'], ramp.inputs['Value'])
    links.new(ramp.outputs['Result'], volume.inputs['Density'])
    links.new(volume.outputs['Volume'], output.inputs['Volume'])
    return mat


dust = volume_material('Air / anisotropic suspended ochre dust', (0.64, 0.42, 0.21), 0.045, 2.3)
smoke = volume_material('Smoke / turbulent charcoal plume', (0.19, 0.17, 0.14), 0.32, 3.6)
haze = volume_material('Distance / warm desert aerial perspective', (0.75, 0.61, 0.42), 0.006, 0.8)
box('Atmospheric scattering volume', (0, 25, 20), (180, 180, 55), haze, 0)
for loc, size in [((-10, -5, 0.65), (7, 2.0, 0.7)), ((9, -1, 0.8), (5, 1.7, 0.9)), ((0, 0.5, 0.6), (6, 1, 0.6)), ((-28, 18, 1), (12, 3, 1.4)), ((23, 16, 1), (8, 3, 1.4))]:
    sphere('Wind driven ground dust', loc, size, dust, 2)
for horizontal, depth, height, size in [(12.5, 4, 1.8, 1.0), (-21, -3, 1.0, 0.6), (-7.5, 2, 1, 0.45)]:
    for index in range(7):
        sphere('Leeward smoke plume', (horizontal - index * 0.32 * size, depth + index * 0.22 * size, height + index * 0.83 * size), ((0.55 + index * 0.15) * size, (0.48 + index * 0.13) * size, (0.75 + index * 0.1) * size), smoke, 2)

active_group = groups['08 Lighting']
world = bpy.data.worlds.new('Amber dusk over Qasr al Raml')
scene.world = world
world.use_nodes = True
nodes = world.node_tree.nodes
links = world.node_tree.links
background = nodes.get('Background')
background.inputs['Strength'].default_value = 0.35
texcoord = nodes.new('ShaderNodeTexCoord')
separate = nodes.new('ShaderNodeSeparateXYZ')
mapping = nodes.new('ShaderNodeMapRange')
mapping.inputs['From Min'].default_value = -0.1
mapping.inputs['From Max'].default_value = 0.8
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color = (0.65, 0.36, 0.16, 1)
ramp.color_ramp.elements[1].color = (0.12, 0.20, 0.28, 1)
links.new(texcoord.outputs['Normal'], separate.inputs[0])
links.new(separate.outputs['Z'], mapping.inputs['Value'])
links.new(mapping.outputs['Result'], ramp.inputs[0])
links.new(ramp.outputs['Color'], background.inputs['Color'])
sun = light('Low amber sun / long shadows', 'SUN', (0, 0, 20), 3.0, (1.0, 0.65, 0.31))
sun.rotation_euler = Vector((-0.60, -0.64, -0.28)).to_track_quat('-Z', 'Y').to_euler()
sun.data.angle = math.radians(3)
fill = light('Sky bounce / broad cool fill', 'AREA', (2, -15, 18), 2100, (0.57, 0.68, 0.84), 22)
fill.rotation_euler = (Vector((0, 2, 2)) - fill.location).to_track_quat('-Z', 'Y').to_euler()
sunmat = emission('Visible dusty sun disc', (1.0, 0.55, 0.16), 3)
sphere('Sun at the dust horizon', (48, 85, 26), (3.0, 3.0, 3.0), sunmat, 4)
bpy.ops.object.camera_add(location=(22, -34, 4.5))
camera = move(bpy.context.object, 'CAMERA / The Last Amber Light')
camera.rotation_euler = (Vector((0.0, 4.0, 5.5)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.lens = 31
camera.data.sensor_width = 36
camera.data.clip_end = 400
camera.data.dof.use_dof = True
camera.data.dof.focus_distance = 39
camera.data.dof.aperture_fstop = 10
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.samples = 20 if PREVIEW else 64
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.cycles.volume_bounces = 1
scene.cycles.transparent_max_bounces = 4
scene.cycles.adaptive_threshold = 0.06 if PREVIEW else 0.025
try:
    preferences = bpy.context.preferences.addons['cycles'].preferences
    preferences.compute_device_type = 'OPTIX'
    preferences.get_devices()
    for device in preferences.devices:
        device.use = device.type == 'OPTIX'
    if any(device.use for device in preferences.devices):
        scene.cycles.device = 'GPU'
except Exception as error:
    print('GPU setup fallback:', error)
scene.render.resolution_x = 1280 if PREVIEW else 1920
scene.render.resolution_y = 800 if PREVIEW else 1200
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.view_settings.exposure = 0.45
scene.render.filepath = os.path.join(OUT, 'preview.png' if PREVIEW else 'qasr_al_raml_final.png')
scene.render.image_settings.color_mode = 'RGB'
scene['Artwork'] = 'QASR AL RAML — The Last Amber Light'
scene['Description'] = 'Original procedural medieval desert siege. Oxblood besiegers against petrol-blue garrison. No external models, textures or intellectual property used.'
scene['Seed'] = 47
scene['Generator'] = 'build_desert_siege.py'
scene['Soldier counts'] = json.dumps(soldier_counts)
scene.unit_settings.system = 'METRIC'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
            area.spaces.active.shading.type = 'MATERIAL'
textblock = bpy.data.texts.get('build_desert_siege.py') or bpy.data.texts.new('build_desert_siege.py')
with open(__file__, 'r', encoding='utf-8') as source:
    textblock.write(source.read())
report = {'scene': scene.name, 'objects': len(scene.objects), 'soldiers': soldier_counts, 'resolution': [scene.render.resolution_x, scene.render.resolution_y], 'engine': scene.render.engine, 'device': scene.cycles.device, 'external_assets': 0}
with open(os.path.join(OUT, 'scene_report.json'), 'w', encoding='utf-8') as handle:
    json.dump(report, handle, indent=2, ensure_ascii=False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'qasr_al_raml.blend'))
print('SCENE_READY', json.dumps(report), flush=True)
if '--no-render' not in ARGS:
    bpy.ops.render.render(write_still=True)
    print('RENDER_COMPLETE', scene.render.filepath, flush=True)
