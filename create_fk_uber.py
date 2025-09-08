import pymel.core as pm
'''
    상단의 3개의 함수는 uber그룹을 찾고 만들기위한 함수로 환경 탐색 및 준비 단계 이고 아래쪽 함수 2개는 연결해주는걸로 fk_data_list를 만들어서 전달
    즉 준비단계와 연결단계가 분리되어 있는 상황
    
    fk구조에서 중간에 컨스트레인이 걸려서 부모의 위치값을 자식에게 전달을 못하는데 uber라는 트랜스폼이 이동값을 계산해서 넘겨주는 구조로 총 4개의 트랜스폼이
    매트릭스로 곱해서 계산을 해준다.
    
    컨스트레인된 부모그룹, 부모 컨트롤러, 컨스트레인된 자식 그룹, 자식의 uber 가 필요 곱샘순서는 아래 코드 참조
    
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


def create_fk_uber(fk_data):

    constrained_parent_transform = fk_data[0]
    parent_ctrl = fk_data[1]
    constrained_child_transform = fk_data[2]
    uber_grp = fk_data[3]


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

def create_fk_uber_batch(fk_data_list):
    '''
    fk_data_list = [
        [constrained_parent_transform1, parent_ctrl1, constrained_child_transform1, uber_grp1],
        [constrained_parent_transform2, parent_ctrl2, constrained_child_transform2, uber_grp2],
        ...
    ]
    '''

    for fk_data in fk_data_list:
        create_fk_uber(fk_data)

