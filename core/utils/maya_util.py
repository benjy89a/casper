import maya.cmds as mc
import maya.api.OpenMaya as om2

import re
import os

def get_shape(trans):
    shape = mc.listRelatives(trans,shapes=1)[0]
    return shape

def get_version():
    name = mc.file(q=True, sceneName = True)
    base_name = os.path.basename(name)
    ver = re.findall('_(v\d+)', base_name)

    if ver:
        return ver[0]

def get_scene_path():
    return mc.file(q=True, sceneName=True)
