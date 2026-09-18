import bpy
from pathlib import Path
from mathutils import Vector

cache=Path.home()/'.agent-reach'/'assets'/'desert-tiger'
for asset in ['quiver_tree_01','wild_rooibos_bush','namaqualand_boulder_02']:
    path=cache/asset/(asset+'.blend')
    if not path.exists():
        continue
    bpy.ops.wm.open_mainfile(filepath=str(path))
    print('ASSET',asset,flush=True)
    for obj in bpy.data.objects:
        if obj.type=='MESH':
            print('MESH',obj.name,'vertices',len(obj.data.vertices),'dimensions',tuple(obj.dimensions),'position',tuple(obj.location),'materials',[mat.name for mat in obj.data.materials],flush=True)
    for image in bpy.data.images:
        if image.source=='FILE':
            print('IMAGE',image.name,image.filepath,flush=True)
