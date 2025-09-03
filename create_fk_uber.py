
import pymel.core as pm
'''
연결을 하기위한 필요한 데이터들의 리스트를 가져오는건 했는데 지금 보면 리스트끼리 순서가 맵핑이 다르게 되어 있는문제가 하나 있음
네이밍으로 작업을 해야하는거 같은데 네이밍 말고 어떻게 처리할지 모르겠음

'''
def get_fk_controls_from_root(root):
    shapes = pm.listRelatives(root, ad=True, type='nurbsCurve') or []
    ctrls_set = set()

    for shape in shapes:
        transform = pm.listRelatives(shape, p=True)[0]
        ctrls_set.add(transform)

    ctrls = list(ctrls_set)
    return ctrls


def get_constrained_transforms(root):
    transforms = pm.listRelatives(root,ad=True, type='transform') or []
    constrained_set = set()
    print(transforms)
    for transform in transforms:
        cons = pm.listRelatives(transform, type='constraint') or []
        if cons:
            constrained_set.add(transform)

    constrained_transforms = list(constrained_set)
    return constrained_transforms

def insert_uber_transform(constrained_transforms):
    uber_grps = []

    for transform in constrained_transforms:
        if not pm.objExists(transform):
            pm.warning(f"f[skip] not exists: {transform}")
            continue
        uber_name = f"{transform}_uber"
        if pm.objExists(uber_name):
            continue

        children = pm.listRelatives(transform, children=True, path=True) or [None]

        children = [
            c for c in children
            if pm.nodeType(c) == "transform" and "Constraint" not in pm.nodeType(c)
        ]

        uber = pm.createNode("transform", n=uber_name, p=transform)

        wm = pm.xform(transform, q=True, ws=True, m=True)
        pm.xform(uber, ws=True, m=wm)

        for child in children:
            pm.parent(child, uber)

        uber_grps.append(uber)

    return uber_grps

import importlib
import sys

sys.path.append(r'/home/mago/casper')

import create_fk_uber as uber
importlib.reload(uber)

import pymel.core as pm


sel = pm.PyNode('lt_toe_3_ctrl_grp')

a = uber.get_fk_controls_from_root(sel)
b = uber.get_constrained_transforms(sel)
uber_grps = uber.insert_uber_transform(b)


uber_grp = uber_grps[0]
constrained_child_transform = b[0]
constrained_parent_transform = b[4]
parent_ctrl = a[3]

mm_uber_con_0 = pm.createNode('multMatrix',name =f'{uber_grp}_multMatrix_0')
mm_uber_con_1 = pm.createNode('multMatrix',name =f'{uber_grp}_multMatrix_1')
mm_uber_con_2 = pm.createNode('multMatrix',name =f'{uber_grp}_multMatrix_2')
dm_uber_con = pm.createNode('decomposeMatrix', name = f'{uber_grp}_decomposeMatrix')

pm.connectAttr(constrained_child_transform.worldMatrix[0] ,mm_uber_con_0.matrixIn[0],force=True)
pm.connectAttr(constrained_parent_transform.worldInverseMatrix[0], mm_uber_con_0.matrixIn[1],force=True)
pm.connectAttr(mm_uber_con_0.matrixSum,mm_uber_con_1.matrixIn[0], force = True)
pm.connectAttr(parent_ctrl.worldMatrix[0],mm_uber_con_1.matrixIn[1], force = True)
pm.connectAttr(mm_uber_con_1.matrixSum,mm_uber_con_2.matrixIn[0], force=True)
pm.connectAttr(constrained_child_transform.worldInverseMatrix[0],mm_uber_con_2.matrixIn[1], force=True)
pm.connectAttr(mm_uber_con_2.matrixSum,dm_uber_con.inputMatrix, force=True)

pm.connectAttr(dm_uber_con.outputTranslate,uber_grp.translate,force=True)
pm.connectAttr(dm_uber_con.outputRotate, uber_grp.rotate, force=True)


