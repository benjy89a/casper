
"""
========================================================
make_curve_from_locator.py
========================================================

[기능]
- Maya 씬에서 순서대로 선택된 로케이터들의 위치를 기반으로 NURBS 커브를 생성합니다.
- 먼저 로케이터 위치에 정확히 CV(Control Vertex)가 위치하는 Degree 1(Linear) 커브를 생성합니다.
- 그 다음, 생성된 커브를 부드러운 형태를 위해 Degree 3(Cubic) 커브로 리빌드(rebuild)합니다.
- 최소 4개의 로케이터가 선택되어야 Degree 3 커브를 정상적으로 생성할 수 있습니다.

[실행 방법]
1. 커브를 생성할 위치에 로케이터를 4개 이상 배치하고 생성 순서대로 선택합니다.
2. 스크립트를 실행합니다.

"""
# Maya 커맨드 모듈을 사용하기 위해 import 합니다.
import maya.cmds as cmds

def make_curve_from_locator():
    """
    선택된 로케이터의 위치를 기반으로 커브를 생성하는 메인 함수입니다.
    1. 먼저 Degree 1 커브를 생성하여 CV가 로케이터 위치와 일치하도록 합니다.
    2. 그 다음, 생성된 커브를 Degree 3으로 리빌드하여 부드럽게 만듭니다.
    """
    # 1. 현재 Maya 씬에서 선택된 오브젝트 리스트를 가져옵니다.
    # ls 명령어는 리스트를 반환합니다.
    # selection=True 플래그는 현재 선택된 것들을 대상으로 합니다.
    # type='transform' 플래그는 여러 노드 타입 중 'transform' 노드만 필터링합니다. 로케이터는 트랜스폼 노드를 가집니다.
    selected_locators = cmds.ls(selection=True, type='transform')

    # 2. 선택된 로케이터의 개수가 4개 미만인지 확인합니다.
    # Degree 3 커브를 의미있게 만들기 위해서는 최소 4개의 컨트롤 포인트가 필요하기 때문입니다.
    if len(selected_locators) < 4:
        # 4개 미만일 경우, 사용자에게 경고 메시지를 표시하고 스크립트 실행을 중단합니다.
        cmds.warning("최소 4개 이상의 로케이터를 선택해야 합니다.")
        return

    # 3. 각 로케이터의 월드 공간(world space) 위치 정보를 저장할 빈 리스트를 생성합니다.
    point_list = []
    # for 루프를 사용하여 선택된 각 로케이터에 대해 반복 작업을 수행합니다.
    for locator in selected_locators:
        # xform 명령어를 사용하여 로케이터의 월드 공간 기준 translation(위치) 값을 쿼리(query)합니다.
        position = cmds.xform(locator, query=True, worldSpace=True, translation=True)
        # 얻어온 위치 정보(e.g., [x, y, z])를 point_list에 추가합니다.
        point_list.append(position)

    # 4. 로케이터 위치 정보(point_list)를 사용하여 Degree 1 (Linear) 커브를 생성합니다.
    # Degree 1 커브는 각 포인트들을 직선으로 연결하며, 포인트의 위치가 곧 CV의 위치가 됩니다.
    # 생성된 커브의 트랜스폼 노드 이름이 linear_curve 변수에 저장됩니다.
    linear_curve = cmds.curve(degree=1, point=point_list)

    # 5. 생성된 Degree 1 커브를 Degree 3 (Cubic) 커브로 리빌드합니다.
    # rebuildCurve 명령어는 커브의 형태를 유지하면서 디그리, CV 개수 등을 변경합니다.
    cmds.rebuildCurve(linear_curve,               # 리빌드할 커브 오브젝트
                      replaceOriginal=True,       # 원본 커브를 리빌드된 커브로 대체
                      rebuildType=0,              # Uniform 방식으로 리빌드
                      keepRange=0,                # 커브의 범위를 유지하지 않음
                      constructionHistory=False,  # 히스토리를 남기지 않음
                      degree=3)                   # 목표 디그리(Cubic)

    # 6. 최종적으로 생성 및 리빌드된 커브의 이름을 'generated_curve#' 형식으로 변경합니다.
    # '#'은 Maya가 자동으로 숫자를 붙여 이름이 중복되지 않도록 합니다.
    final_curve = cmds.rename(linear_curve, "generated_curve#")
    
    # 사용자에게 생성된 커브의 이름을 알려줍니다.
    print(f"'{final_curve}' 이름으로 커브가 생성되었습니다.")
    
    # 생성된 커브의 이름을 반환합니다.
    return final_curve


# 스크립트의 메인 함수를 실행합니다.
make_curve_from_locator()


