from core.utils.maya_util import get_scene_path

import maya.cmds as mc

from pathlib import Path
import re

def capture_viewport():

    scene_path = get_scene_path()

    if not scene_path:
        raise ValueError("First, save your file")

    scene_file = Path(scene_path)
    base_path = scene_file.parent
    base_name = scene_file.stem
    ver_name = Path(re.findall('_(v\d+)', base_name)[0])
    ver_folder = base_path / ver_name

    if not ver_folder.exists():
        ver_folder.mkdir(parents = True, exist_ok  = True)

    jpg_path = str(ver_folder / base_name)


    mc.playblast(viewer=False, format="image", compression="jpg", quality=100, completeFilename=jpg_path + '.jpg',
                 widthHeight=(1920, 1080), forceOverwrite=True, startTime=1001, endTime=1001, clearCache=True)

    print(f"Screen capture completed: {jpg_path}.jpg")
