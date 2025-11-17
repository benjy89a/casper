# -*- coding: utf-8 -*-

# maya.cmds 모듈을 mc 라는 이름으로 가져옵니다. 씬의 오브젝트를 생성, 수정, 쿼리하는 데 사용됩니다.
import maya.cmds as mc
# maya.api.OpenMaya 모듈을 om2 라는 이름으로 가져옵니다. 벡터와 같은 수학적 계산을 위해 사용됩니다.
import maya.api.OpenMaya as om2

def create_center_locator():
    """
    선택된 요소(오브젝트, 컴포넌트)들의 모든 버텍스 위치의 평균을 계산하여
    그 중심점에 로케이터를 생성하는 함수입니다.
    """
    # 현재 씬에서 선택된 모든 요소를 리스트로 가져옵니다.
    # 이 리스트는 오브젝트, 버텍스, 엣지, 페이스 등 다양한 종류의 선택 항목을 포함할 수 있습니다.
    selection_list = mc.ls(selection=True)

    # 만약 선택된 요소가 하나도 없다면
    if not selection_list:
        # 사용자에게 경고 메시지를 표시하고 함수 실행을 중단합니다.
        mc.warning("아무것도 선택되지 않았습니다. 오브젝트, 버텍스, 엣지, 또는 페이스를 선택해주세요.")
        # 함수를 여기서 종료합니다.
        return

    # 선택된 요소들을 모두 버텍스 컴포넌트로 변환합니다.
    # 예를 들어, 폴리곤 페이스를 선택하면 해당 페이스를 구성하는 버텍스들이 반환됩니다.
    # toVertex=True는 선택된 컴포넌트를 버텍스로 변환하라는 지시입니다.
    vertex_components = mc.polyListComponentConversion(selection_list, toVertex=True)

    # 변환된 버텍스 리스트를 펼치고(flatten), set을 이용해 중복을 제거한 후 다시 리스트로 만듭니다.
    # 이를 통해 계산에 포함될 유일한 버텍스들의 목록을 확보합니다.
    unique_vertex_list = list(set(mc.ls(vertex_components, flatten=True)))

    # 만약 유효한 버텍스가 목록에 없다면 (예: 커브나 라이트만 선택한 경우, 또는 빈 선택)
    if not unique_vertex_list:
        # 사용자에게 폴리곤을 선택해야 함을 알리는 경고를 표시합니다.
        mc.warning("선택 항목에서 위치를 계산할 수 있는 버텍스를 찾지 못했습니다. 폴리곤 오브젝트나 컴포넌트를 선택해주세요.")
        # 함수를 여기서 종료합니다.
        return

    # 모든 버텍스의 월드 좌표 벡터를 더하기 위한 MVector 객체를 (0, 0, 0)으로 초기화합니다.
    # MVector는 OpenMaya에서 제공하는 3D 벡터 클래스입니다.
    total_position_vector = om2.MVector(0, 0, 0)

    # 유일한 버텍스 목록의 각 버텍스에 대해 반복 작업을 수행합니다.
    for vertex in unique_vertex_list:
        # xform 명령을 사용해 해당 버텍스의 월드 공간 위치([x, y, z])를 쿼리합니다.
        # query=True는 값을 쿼리하겠다는 의미, translation=True는 이동 값을 쿼리하겠다는 의미,
        # worldSpace=True는 월드 좌표계를 기준으로 쿼리하겠다는 의미입니다.
        pos = mc.xform(vertex, query=True, translation=True, worldSpace=True)
        # 쿼리한 위치 리스트(pos)를 MVector 객체로 변환한 후, total_position_vector에 더합니다.
        total_position_vector += om2.MVector(pos[0], pos[1], pos[2])

    # 버텍스의 총 개수를 구합니다.
    num_vertices = len(unique_vertex_list)
    
    # 총 위치 벡터를 버텍스의 개수로 나누어 모든 버텍스의 기하학적 평균 위치(중심점)를 계산합니다.
    # 이것이 선택된 모든 버텍스의 정확한 중심점이 됩니다.
    center_position = total_position_vector / num_vertices

    # 'center_locator'라는 이름으로 월드 공간에 로케이터를 생성합니다.
    # spaceLocator 명령은 [transform_node_name, shape_node_name] 형태의 리스트를 반환하므로,
    # [0]을 이용해 트랜스폼 노드의 이름을 가져옵니다.
    locator_transform = mc.spaceLocator(name="center_locator")[0]

    # 생성된 로케이터를 위에서 계산한 중심점의 x, y, z 좌표로 이동시킵니다.
    # absolute=True는 절대 좌표로 이동하겠다는 의미이며, worldSpace=True는 월드 좌표계를 기준으로 이동하겠다는 의미입니다.
    mc.move(center_position.x, center_position.y, center_position.z, locator_transform, absolute=True, worldSpace=True)

    # 사용자에게 작업 완료를 알리는 메시지를 출력합니다.
    print("'{0}'가 선택 영역의 평균 중심 위치에 생성되었습니다.".format(locator_transform))

# 스크립트가 Maya에서 직접 실행될 때 함수를 호출합니다.
create_center_locator()
