"""
스플라인 가중치(weights)를 생성하기 위한 함수들입니다.

사용법:
    이 모듈의 각 함수는 커브 매개변수(parameters)를 입력받아 제어점(control point) 가중치를 출력합니다.
    가중치는 드 부어(de Boor) 알고리즘의 수정된 버전을 사용하여 생성됩니다.
    이 가중치들은 스플라인 위의 점이나 탄젠트(tangent)를 찾기 위한 가중 합(weighted sum)을 만드는 데 사용될 수 있습니다.

    이 함수들은 Autodesk Maya에서 사용하기 위해 작성되었지만, 실제로는 Maya에 특화된 라이브러리를 포함하고 있지 않습니다.
    또한, 이 함수들은 제공된 제어점의 데이터 유형에 신경 쓰지 않습니다.
    이를 통해 점, 행렬(matrices), 또는 Maya 어트리뷰트(attribute) 이름 등 다양한 데이터 유형을 지원할 수 있습니다.
    출력 매핑은 제공된 것과 동일한 제어점을 사용합니다.

예제:
    이 모듈의 맨 끝에는 몇 가지 Maya 예제가 포함되어 있습니다.
    이 예제 함수들은 테스트용으로 사용되거나 다른 곳에서 활용하기 위한 시작점으로 제공됩니다.
    완전한 기능의 자동 리거(auto-rigger)로 설계된 것은 아닙니다.
"""


def defaultKnots(count, degree=3):
    """
    주어진 CV 개수와 차수(degree)에 대한 기본 노트 벡터(knot vector)를 가져옵니다.

    Args:
        count(int): CV의 개수.
        degree(int): 커브의 차수.

    Returns:
        list: 노트 값의 리스트.
    """
    knots = [0 for i in range(degree)] + [i for i in range(count - degree + 1)]
    knots += [count - degree for i in range(degree)]
    return [float(knot) for knot in knots]


def pointOnCurveWeights(cvs, t, degree, knots=None):
    """
    스플라인 커브 위의 CV와 커브 가중치 값의 매핑을 생성합니다.
    모든 CV가 필요하지만, 0이 아닌 가중치를 가진 CV만 반환됩니다.
    이 함수는 스플라인 평가를 위한 드 부어(de Boor) 알고리즘을 기반으로 하며, 가중치를 통합하기 위해 수정되었습니다.

    Args:
        cvs(list): CV 리스트. 반환 값에 사용됩니다.
        t(float): 매개변수 값.
        degree(int): 커브 차원.
        knots(list): 노트 값 리스트.

    Returns:
        list: [제어점, 가중치] 쌍의 리스트.
    """

    order = degree + 1  # 함수에서는 종종 차수 대신 순서(order)를 사용합니다.
    if len(cvs) <= degree:
        raise CurveException('차수 %s의 커브는 최소 %s개의 CV가 필요합니다' % (degree, degree + 1))

    knots = knots or defaultKnots(len(cvs), degree)  # 기본적으로 균일한 노트 분포를 사용합니다.
    if len(knots) != len(cvs) + order:
        raise CurveException('제공된 노트가 충분하지 않습니다. %s개의 CV를 가진 커브는 길이가 %s인 노트 벡터가 필요합니다. '
                             '수신된 노트 벡터 길이: %s, 내용: %s. '
                             '총 노트 개수는 len(cvs) + degree + 1과 같아야 합니다.' % (len(cvs), len(cvs) + order,
                                                                                     len(knots), knots))

    # CV를 해시 가능한 인덱스로 변환합니다.
    _cvs = cvs
    cvs = [i for i in range(len(cvs))]

    # t 값을 노트 값의 범위로 다시 매핑합니다.
    min_val = knots[order] - 1
    max_val = knots[len(knots) - 1 - order] + 1
    t = (t * (max_val - min_val)) + min_val

    # t가 어느 세그먼트(segment)에 속하는지 결정합니다.
    segment = degree
    for index, knot in enumerate(knots[order:len(knots) - order]):
        if knot <= t:
            segment = index + order

    # 사용하지 않을 CV를 필터링합니다.
    cvs = [cvs[j + segment - degree] for j in range(0, degree + 1)]

    # 수정된 드 부어 알고리즘을 실행합니다.
    cvWeights = [{cv: 1.0} for cv in cvs]
    for r in range(1, degree + 1):
        for j in range(degree, r - 1, -1):
            right = j + 1 + segment - r
            left = j + segment - degree
            alpha = (t - knots[left]) / (knots[right] - knots[left])

            weights = {}
            for cv, weight in cvWeights[j].items():
                weights[cv] = weight * alpha

            for cv, weight in cvWeights[j - 1].items():
                if cv in weights:
                    weights[cv] += weight * (1 - alpha)
                else:
                    weights[cv] = weight * (1 - alpha)

            cvWeights[j] = weights

    cvWeights = cvWeights[degree]
    return [[_cvs[index], weight] for index, weight in cvWeights.items()]


def tangentOnCurveWeights(cvs, t, degree, knots=None):
    """
    CV와 커브 탄젠트 가중치 값의 매핑을 생성합니다.
    모든 CV가 필요하지만, 0이 아닌 가중치를 가진 CV만 반환됩니다.

    Args:
        cvs(list): CV 리스트. 반환 값에 사용됩니다.
        t(float): 매개변수 값.
        degree(int): 커브 차원.
        knots(list): 노트 값 리스트.

    Returns:
        list: [제어점, 가중치] 쌍의 리스트.
    """

    order = degree + 1  # 함수에서는 종종 차수 대신 순서(order)를 사용합니다.
    if len(cvs) <= degree:
        raise CurveException('차수 %s의 커브는 최소 %s개의 CV가 필요합니다' % (degree, degree + 1))

    knots = knots or defaultKnots(len(cvs), degree)  # 기본적으로 균일한 노트 분포를 사용합니다.
    if len(knots) != len(cvs) + order:
        raise CurveException('제공된 노트가 충분하지 않습니다. %s개의 CV를 가진 커브는 길이가 %s인 노트 벡터가 필요합니다. '
                             '수신된 노트 벡터 길이: %s, 내용: %s. '
                             '총 노트 개수는 len(cvs) + degree + 1과 같아야 합니다.' % (len(cvs), len(cvs) + order,
                                                                                     len(knots), knots))

    # t 값을 노트 값의 범위로 다시 매핑합니다.
    min_val = knots[order] - 1
    max_val = knots[len(knots) - 1 - order] + 1
    t = (t * (max_val - min_val)) + min_val

    # t가 어느 세그먼트(segment)에 속하는지 결정합니다.
    segment = degree
    for index, knot in enumerate(knots[order:len(knots) - order]):
        if knot <= t:
            segment = index + order

    # CV를 해시 가능한 인덱스로 변환합니다.
    _cvs = cvs
    cvs = [i for i in range(len(cvs))]

    # 탄젠트를 찾기 위해 더 낮은 차수의 커브에서 점을 찾아야 합니다.
    degree = degree - 1
    qWeights = [{cv: 1.0} for cv in range(0, degree + 1)]

    # 이 낮은 차수 커브에 대한 드 부어 가중치를 얻습니다.
    for r in range(1, degree + 1):
        for j in range(degree, r - 1, -1):
            right = j + 1 + segment - r
            left = j + segment - degree
            alpha = (t - knots[left]) / (knots[right] - knots[left])

            weights = {}
            for cv, weight in qWeights[j].items():
                weights[cv] = weight * alpha

            for cv, weight in qWeights[j - 1].items():
                if cv in weights:
                    weights[cv] += weight * (1 - alpha)
                else:
                    weights[cv] = weight * (1 - alpha)

            qWeights[j] = weights
    weights = qWeights[degree]

    # 낮은 차수의 가중치를 실제 CV와 일치시킵니다.
    cvWeights = []
    for j in range(0, degree + 1):
        weight = weights[j]
        cv0 = j + segment - degree
        cv1 = j + segment - degree - 1
        alpha = weight * (degree + 1) / (knots[j + segment + 1] - knots[j + segment - degree])
        cvWeights.append([cvs[cv0], alpha])
        cvWeights.append([cvs[cv1], -alpha])

    return [[_cvs[index], weight] for index, weight in cvWeights]


def pointOnSurfaceWeights(cvs, u, v, uKnots=None, vKnots=None, degree=3):
    """
    CV와 서피스(surface) 점 가중치 값의 매핑을 생성합니다.

    Args:
        cvs(list): CV 행(row)의 리스트. 반환 값에 사용됩니다.
        u(float): 커브 위의 u 매개변수 값.
        v(float): 커브 위의 v 매개변수 값.
        uKnots(list, optional): u 방향의 노트 정수 리스트.
        vKnots(list, optional): v 방향의 노트 정수 리스트.
        degree(int, optional): 커브의 차수. 최소값은 2.

    Returns:
        list: [제어점, 가중치] 쌍의 리스트.
    """
    matrixWeightRows = [pointOnCurveWeights(row, u, degree, uKnots) for row in cvs]
    matrixWeightColumns = pointOnCurveWeights([i for i in range(len(matrixWeightRows))], v, degree, vKnots)
    surfaceMatrixWeights = []
    for index, weight in matrixWeightColumns:
        matrixWeights = matrixWeightRows[index]
        surfaceMatrixWeights.extend([[m, (w * weight)] for m, w in matrixWeights])

    return surfaceMatrixWeights


def tangentUOnSurfaceWeights(cvs, u, v, uKnots=None, vKnots=None, degree=3):
    """
    u 축을 따르는 서피스 탄젠트 가중치 값과 CV의 매핑을 생성합니다.

    Args:
        cvs(list): CV 행(row)의 리스트. 반환 값에 사용됩니다.
        u(float): 커브 위의 u 매개변수 값.
        v(float): 커브 위의 v 매개변수 값.
        uKnots(list, optional): u 방향의 노트 정수 리스트.
        vKnots(list, optional): v 방향의 노트 정수 리스트.
        degree(int, optional): 커브의 차수. 최소값은 2.

    Returns:
        list: [제어점, 가중치] 쌍의 리스트.
    """

    matrixWeightRows = [pointOnCurveWeights(row, u, degree, uKnots) for row in cvs]
    matrixWeightColumns = tangentOnCurveWeights([i for i in range(len(matrixWeightRows))], v, degree, vKnots)
    surfaceMatrixWeights = []
    for index, weight in matrixWeightColumns:
        matrixWeights = matrixWeightRows[index]
        surfaceMatrixWeights.extend([[m, (w * weight)] for m, w in matrixWeights])

    return surfaceMatrixWeights


def tangentVOnSurfaceWeights(cvs, u, v, uKnots=None, vKnots=None, degree=3):
    """
    v 축을 따르는 서피스 탄젠트 가중치 값과 CV의 매핑을 생성합니다.

    Args:
        cvs(list): CV 행(row)의 리스트. 반환 값에 사용됩니다.
        u(float): 커브 위의 u 매개변수 값.
        v(float): 커브 위의 v 매개변수 값.
        uKnots(list, optional): u 방향의 노트 정수 리스트.
        vKnots(list, optional): v 방향의 노트 정수 리스트.
        degree(int, optional): 커브의 차수. 최소값은 2.

    Returns:
        list: [제어점, 가중치] 쌍의 리스트.
    """
    # CV 순서를 재정렬합니다.
    rowCount = len(cvs)
    columnCount = len(cvs[0])
    reorderedCvs = [[cvs[row][col] for row in range(rowCount)] for col in range(columnCount)]
    return tangentUOnSurfaceWeights(reorderedCvs, v, u, uKnots=vKnots, vKnots=uKnots, degree=degree)


class CurveException(BaseException):
    """ 잘못된 커브 매개변수를 나타내기 위해 발생합니다. """


# ------- 예제 -------- #


import math
from maya import cmds


def _is2020():
    """ 현재 마야 버전이 2020 이상인지 확인합니다. """
    if 'Preview' in cmds.about(version=True):  # Maya Beta는 2020 이상으로 간주합니다.
        return True
    return int(cmds.about(version=True).split('.')[0]) >= 2020


def _testCube(radius=1.0, color=(1,1,1), name='cube', position=(0,0,0)):
    """ 테스트 목적으로 큐브를 생성합니다. """
    radius *= 2
    cube = cmds.polyCube(name=name, h=radius, w=radius, d=radius)[0]
    shader = cmds.shadingNode('lambert', asShader=True)
    cmds.setAttr('%s.color' % shader, *color)
    cmds.setAttr('%s.ambientColor' % shader, 0.1, 0.1, 0.1)
    shadingGroup = cmds.sets(renderable=True, noSurfaceShader=True, empty=True)
    cmds.connectAttr(shader + '.outColor', shadingGroup + ".surfaceShader", force=True)
    cmds.sets(cube, fe=shadingGroup)
    cmds.xform(cube, t=position)
    return cube


def _testSphere(radius=1.0, color=(1,1,1), name='sphere', position=(0,0,0)):
    """ 테스트 목적으로 구체를 생성합니다. """
    sphere = cmds.polySphere(name=name, radius=radius)[0]
    shader = cmds.shadingNode('lambert', asShader=True)
    cmds.setAttr('%s.ambientColor' % shader, 0.1, 0.1, 0.1)
    cmds.setAttr('%s.color' % shader, *color)
    shadingGroup = cmds.sets(renderable=True, noSurfaceShader=True, empty=True)
    cmds.connectAttr(shader + '.outColor', shadingGroup + ".surfaceShader", force=True)
    cmds.sets(sphere, fe=shadingGroup)
    cmds.xform(sphere, t=position)
    return sphere


def _testMatrixOnCurve(count=4, pCount=None, degree=3):
    """
    주어진 CV 및 포인트 개수로 예제 커브를 생성합니다.

    Args:
        count(int): CV의 양.
        pCount(int): 커브에 붙일 포인트의 양.
        degree(int): 커브의 차수.
    """

    pCount = pCount or count * 4
    cRadius = 1.0
    pRadius = 0.5
    spacing = cRadius * 5

    # 제어점 생성
    cvMatrices = []
    for i in range(count):
        cv = _testSphere(cRadius, color=(0.7,1,1), name='cv%s' % i, position=(i * spacing, 0, 0))
        cvMatrices.append('%s.worldMatrix[0]' % cv)

    # 큐브 붙이기
    for i in range(pCount):
        t = i / (float(pCount) - 1)
        pNode = _testCube(pRadius, color=(0,0.5,1), name='p%s' % i)

        # 위치 행렬 생성
        pointMatrixWeights = pointOnCurveWeights(cvMatrices, t, degree=degree)
        pointMatrixNode = cmds.createNode('wtAddMatrix', name='pointMatrix0%s' % (i+1))
        pointMatrix = '%s.matrixSum' % pointMatrixNode
        for index, (matrix, weight) in enumerate(pointMatrixWeights):
            cmds.connectAttr(matrix, '%s.wtMatrix[%s].matrixIn' % (pointMatrixNode, index))
            cmds.setAttr('%s.wtMatrix[%s].weightIn' % (pointMatrixNode, index), weight)

        # 탄젠트 행렬 생성
        tangentMatrixWeights = tangentOnCurveWeights(cvMatrices, t, degree=degree)
        tangentMatrixNode = cmds.createNode('wtAddMatrix', name='tangentMatrix0%s' % (i+1))
        tangentMatrix = '%s.matrixSum' % tangentMatrixNode
        for index, (matrix, weight) in enumerate(tangentMatrixWeights):
            cmds.connectAttr(matrix, '%s.wtMatrix[%s].matrixIn' % (tangentMatrixNode, index))
            cmds.setAttr('%s.wtMatrix[%s].weightIn' % (tangentMatrixNode, index), weight)

        if _is2020():
            # aim 행렬 노드 생성
            aimMatrixNode = cmds.createNode('aimMatrix', name='aimMatrix0%s' % (i+1))
            cmds.connectAttr(pointMatrix, '%s.inputMatrix' % aimMatrixNode)
            cmds.connectAttr(tangentMatrix, '%s.primaryTargetMatrix' % aimMatrixNode)
            cmds.setAttr('%s.primaryMode' % aimMatrixNode, 1)
            cmds.setAttr('%s.primaryInputAxis' % aimMatrixNode, 1, 0, 0)
            cmds.setAttr('%s.secondaryInputAxis' % aimMatrixNode, 0, 1, 0)
            cmds.setAttr('%s.secondaryMode' % aimMatrixNode, 0)
            aimMatrixOutput = '%s.outputMatrix' % aimMatrixNode

            # 스케일 제거
            pickMatrixNode = cmds.createNode('pickMatrix', name='noScale0%s' % (i+1))
            cmds.connectAttr(aimMatrixOutput, '%s.inputMatrix' % pickMatrixNode)
            cmds.setAttr('%s.useScale' % pickMatrixNode, False)
            cmds.setAttr('%s.useShear' % pickMatrixNode, False)
            outputMatrix = '%s.outputMatrix' % pickMatrixNode

            cmds.connectAttr(outputMatrix, '%s.offsetParentMatrix' % pNode)
        else:
            # 위치 행렬 분해
            pointDecomposeNode = cmds.createNode('decomposeMatrix', name='pointDecompose0%s' % (i+1))
            cmds.connectAttr(pointMatrix, '%s.inputMatrix' % pointDecomposeNode)
            pointVector = '%s.outputTranslate' % pointDecomposeNode

            # 탄젠트 행렬을 벡터로 변환
            tangentDecomposeNode = cmds.createNode('decomposeMatrix', name='tangentVectorDecompose0%s' % (i+1))
            cmds.connectAttr(tangentMatrix, '%s.inputMatrix' % tangentDecomposeNode)
            tangentVector = '%s.outputTranslate' % tangentDecomposeNode

            # 탄젠트 벡터 정규화
            tangentNormalizeNode = cmds.createNode('vectorProduct', name='tangentVector0%s' % (i+1))
            cmds.setAttr('%s.operation' % tangentNormalizeNode, 0)
            cmds.setAttr('%s.normalizeOutput' % tangentNormalizeNode, True)
            cmds.connectAttr(tangentVector, '%s.input1' % tangentNormalizeNode)
            xVector = '%s.output' % tangentNormalizeNode

            # 위치 행렬에서 up 벡터 가져오기
            upVectorNode = cmds.createNode('vectorProduct', name='upVector0%s' % (i+1))
            cmds.setAttr('%s.operation' % upVectorNode, 3)
            cmds.setAttr('%s.normalizeOutput' % upVectorNode, True)
            cmds.setAttr('%s.input1' % upVectorNode, 0, 1, 0)
            cmds.connectAttr(pointMatrix, '%s.matrix' % upVectorNode)
            upVector = '%s.output' % upVectorNode

            # 외적(cross product)을 사용하여 z 벡터 찾기
            zVectorNode = cmds.createNode('vectorProduct', name='zVector0%s' % (i+1))
            cmds.setAttr('%s.operation' % zVectorNode, 2)
            cmds.setAttr('%s.normalizeOutput' % zVectorNode, True)
            cmds.connectAttr(xVector, '%s.input1' % zVectorNode)
            cmds.connectAttr(upVector, '%s.input2' % zVectorNode)
            zVector = '%s.output' % zVectorNode

            # 외적을 사용하여 y 벡터 찾기
            yVectorNode = cmds.createNode('vectorProduct', name='yVector0%s' % (i+1))
            cmds.setAttr('%s.operation' % yVectorNode, 2)
            cmds.setAttr('%s.normalizeOutput' % yVectorNode, True)
            cmds.connectAttr(xVector, '%s.input1' % yVectorNode)
            cmds.connectAttr(zVector, '%s.input2' % yVectorNode)
            yVector = '%s.output' % yVectorNode

            # 각 축에서 aim 행렬 생성
            outputMatrixNode = cmds.createNode('fourByFourMatrix', name='outputMatrix0%s' % (i+1))
            for row, vector in enumerate([xVector, yVector, zVector, pointVector]):
                for col, axis in enumerate(['X', 'Y', 'Z']):
                    cmds.connectAttr('%s%s' % (vector, axis), '%s.i%s%s' % (outputMatrixNode, row, col))

            # 행렬 변환 분해
            decomposeMatrixNode = cmds.createNode('decomposeMatrix', name='outputTransformations0%s' % (i+1))
            cmds.connectAttr('%s.output' % outputMatrixNode, '%s.inputMatrix' % decomposeMatrixNode)

            # 출력 연결
            cmds.connectAttr('%s.outputTranslate' % decomposeMatrixNode, '%s.translate' % pNode)
            cmds.connectAttr('%s.outputRotate' % decomposeMatrixNode, '%s.rotate' % pNode)


def _testMatrixOnCircularCurve(count=4, pCount=None, degree=3):
    """
    주어진 CV 및 포인트 개수로 예제 원형 커브를 생성합니다.

    Args:
        count(int): CV의 양.
        pCount(int): 커브에 붙일 포인트의 양.
        degree(int): 커브의 차수.
    """

    pCount = pCount or count * 4
    cRadius = 1.0
    pRadius = 0.5
    spacing = cRadius * 5

    # 제어점 생성
    cvMatrices = []
    for i in range(count):
        t = i / (float(count))
        x = math.cos(t * math.pi * 2)
        y = math.sin(t * math.pi * 2)
        cv = _testSphere(cRadius, color=(0.7,1,1), name='cv%s' % i, position=(x * spacing, 0, y * spacing))
        cvMatrices.append('%s.worldMatrix[0]' % cv)

    # 제어점 리스트를 루프되도록 수정
    cvMatrices = cvMatrices + cvMatrices[:3]
    knots = [i for i in range(len(cvMatrices) + degree + 1)]
    knots = [float(knot) for knot in knots]

    # 큐브 붙이기
    for i in range(pCount):
        t = i / (float(pCount) - 1)
        pNode = _testCube(pRadius, color=(0,0.5,1), name='p%s' % i)

        # 위치 행렬 생성
        pointMatrixWeights = pointOnCurveWeights(cvMatrices, t, degree=degree, knots=knots)
        pointMatrixNode = cmds.createNode('wtAddMatrix', name='pointMatrix0%s' % (i+1))
        pointMatrix = '%s.matrixSum' % pointMatrixNode
        for index, (matrix, weight) in enumerate(pointMatrixWeights):
            cmds.connectAttr(matrix, '%s.wtMatrix[%s].matrixIn' % (pointMatrixNode, index))
            cmds.setAttr('%s.wtMatrix[%s].weightIn' % (pointMatrixNode, index), weight)

        # 탄젠트 행렬 생성
        tangentMatrixWeights = tangentOnCurveWeights(cvMatrices, t, degree=degree, knots=knots)
        tangentMatrixNode = cmds.createNode('wtAddMatrix', name='tangentMatrix0%s' % (i+1))
        tangentMatrix = '%s.matrixSum' % tangentMatrixNode
        for index, (matrix, weight) in enumerate(tangentMatrixWeights):
            cmds.connectAttr(matrix, '%s.wtMatrix[%s].matrixIn' % (tangentMatrixNode, index))
            cmds.setAttr('%s.wtMatrix[%s].weightIn' % (tangentMatrixNode, index), weight)

        if _is2020():
            # aim 행렬 노드 생성
            aimMatrixNode = cmds.createNode('aimMatrix', name='aimMatrix0%s' % (i+1))
            cmds.connectAttr(pointMatrix, '%s.inputMatrix' % aimMatrixNode)
            cmds.connectAttr(tangentMatrix, '%s.primaryTargetMatrix' % aimMatrixNode)
            cmds.setAttr('%s.primaryMode' % aimMatrixNode, 1)
            cmds.setAttr('%s.primaryInputAxis' % aimMatrixNode, 1, 0, 0)
            cmds.setAttr('%s.secondaryInputAxis' % aimMatrixNode, 0, 1, 0)
            cmds.setAttr('%s.secondaryMode' % aimMatrixNode, 1)
            aimMatrixOutput = '%s.outputMatrix' % aimMatrixNode

            # 스케일 제거
            pickMatrixNode = cmds.createNode('pickMatrix', name='noScale0%s' % (i+1))
            cmds.connectAttr(aimMatrixOutput, '%s.inputMatrix' % pickMatrixNode)
            cmds.setAttr('%s.useScale' % pickMatrixNode, False)
            cmds.setAttr('%s.useShear' % pickMatrixNode, False)
            outputMatrix = '%s.outputMatrix' % pickMatrixNode

            cmds.connectAttr(outputMatrix, '%s.offsetParentMatrix' % pNode)
        else:
            # 위치 행렬 분해
            pointDecomposeNode = cmds.createNode('decomposeMatrix', name='pointDecompose0%s' % (i+1))
            cmds.connectAttr(pointMatrix, '%s.inputMatrix' % pointDecomposeNode)
            pointVector = '%s.outputTranslate' % pointDecomposeNode

            # 탄젠트 행렬을 벡터로 변환
            tangentDecomposeNode = cmds.createNode('decomposeMatrix', name='tangentVectorDecompose0%s' % (i+1))
            cmds.connectAttr(tangentMatrix, '%s.inputMatrix' % tangentDecomposeNode)
            tangentVector = '%s.outputTranslate' % tangentDecomposeNode

            # 탄젠트 벡터 정규화
            tangentNormalizeNode = cmds.createNode('vectorProduct', name='tangentVector0%s' % (i+1))
            cmds.setAttr('%s.operation' % tangentNormalizeNode, 0)
            cmds.setAttr('%s.normalizeOutput' % tangentNormalizeNode, True)
            cmds.connectAttr(tangentVector, '%s.input1' % tangentNormalizeNode)
            xVector = '%s.output' % tangentNormalizeNode

            # 위치 행렬에서 up 벡터 가져오기
            upVectorNode = cmds.createNode('vectorProduct', name='upVector0%s' % (i+1))
            cmds.setAttr('%s.operation' % upVectorNode, 3)
            cmds.setAttr('%s.normalizeOutput' % upVectorNode, True)
            cmds.setAttr('%s.input1' % upVectorNode, 0, 1, 0)
            cmds.connectAttr(pointMatrix, '%s.matrix' % upVectorNode)
            upVector = '%s.output' % upVectorNode

            # 외적을 사용하여 z 벡터 찾기
            zVectorNode = cmds.createNode('vectorProduct', name='zVector0%s' % (i+1))
            cmds.setAttr('%s.operation' % zVectorNode, 2)
            cmds.setAttr('%s.normalizeOutput' % zVectorNode, True)
            cmds.connectAttr(xVector, '%s.input1' % zVectorNode)
            cmds.connectAttr(upVector, '%s.input2' % zVectorNode)
            zVector = '%s.output' % zVectorNode

            # 외적을 사용하여 y 벡터 찾기
            yVectorNode = cmds.createNode('vectorProduct', name='yVector0%s' % (i+1))
            cmds.setAttr('%s.operation' % yVectorNode, 2)
            cmds.setAttr('%s.normalizeOutput' % yVectorNode, True)
            cmds.connectAttr(xVector, '%s.input1' % yVectorNode)
            cmds.connectAttr(zVector, '%s.input2' % yVectorNode)
            yVector = '%s.output' % yVectorNode

            # 각 축에서 aim 행렬 생성
            outputMatrixNode = cmds.createNode('fourByFourMatrix', name='outputMatrix0%s' % (i+1))
            for row, vector in enumerate([xVector, yVector, zVector, pointVector]):
                for col, axis in enumerate(['X', 'Y', 'Z']):
                    cmds.connectAttr('%s%s' % (vector, axis), '%s.i%s%s' % (outputMatrixNode, row, col))

            # 행렬 변환 분해
            decomposeMatrixNode = cmds.createNode('decomposeMatrix', name='outputTransformations0%s' % (i+1))
            cmds.connectAttr('%s.output' % outputMatrixNode, '%s.inputMatrix' % decomposeMatrixNode)

            # 출력 연결
            cmds.connectAttr('%s.outputTranslate' % decomposeMatrixNode, '%s.translate' % pNode)
            cmds.connectAttr('%s.outputRotate' % decomposeMatrixNode, '%s.rotate' % pNode)


def _testMatrixOnSurface(uCount=4, vCount=4, degree=3):
    """
    주어진 CV 개수로 matrixOnSurface를 테스트합니다.

    Args:
        uCount(int): u에 있는 CV의 양.
        vCount(int): v에 있는 CV의 양.
        degree(int): 커브의 차수.
    """

    pCountU = uCount * 3
    pCountV = vCount * 3
    cRadius = 1.0
    pRadius = 0.5
    spacing = cRadius * 5

    cvMatrices = []
    for i in range(uCount):
        row = []
        for j in range(vCount):
            cv = _testSphere(cRadius, color=(1, 1, 1), name='cv%s%s' % (i, j), position=(i * spacing, 0, j * spacing))
            row.append('%s.worldMatrix[0]' % cv)
        cvMatrices.append(row)

    for i in range(pCountU):
        for j in range(pCountV):
            u = i / (float(pCountU) - 1)
            v = j / (float(pCountV) - 1)
            pNode = _testCube(pRadius, color=(0, 0.5, 1), name='p%s%s' % (i, j))

            # 위치 행렬 생성
            pointMatrixWeights = pointOnSurfaceWeights(cvMatrices, u, v, degree=degree)
            pointMatrixNode = cmds.createNode('wtAddMatrix', name='pointMatrix0%s' % (i+1))
            pointMatrix = '%s.matrixSum' % pointMatrixNode
            for index, (matrix, weight) in enumerate(pointMatrixWeights):
                cmds.connectAttr(matrix, '%s.wtMatrix[%s].matrixIn' % (pointMatrixNode, index))
                cmds.setAttr('%s.wtMatrix[%s].weightIn' % (pointMatrixNode, index), weight)

            # 탄젠트 u 행렬 생성
            tangentUMatrixWeights = tangentUOnSurfaceWeights(cvMatrices, u, v, degree=degree)
            tangentUMatrixNode = cmds.createNode('wtAddMatrix', name='tangentUMatrix0%s' % (i+1))
            tangentUMatrix = '%s.matrixSum' % tangentUMatrixNode
            for index, (matrix, weight) in enumerate(tangentUMatrixWeights):
                cmds.connectAttr(matrix, '%s.wtMatrix[%s].matrixIn' % (tangentUMatrixNode, index))
                cmds.setAttr('%s.wtMatrix[%s].weightIn' % (tangentUMatrixNode, index), weight)

            # 탄젠트 v 행렬 생성
            tangentVMatrixWeights = tangentVOnSurfaceWeights(cvMatrices, u, v, degree=degree)
            tangentVMatrixNode = cmds.createNode('wtAddMatrix', name='tangentVMatrix0%s' % (i+1))
            tangentVMatrix = '%s.matrixSum' % tangentVMatrixNode
            for index, (matrix, weight) in enumerate(tangentVMatrixWeights):
                cmds.connectAttr(matrix, '%s.wtMatrix[%s].matrixIn' % (tangentVMatrixNode, index))
                cmds.setAttr('%s.wtMatrix[%s].weightIn' % (tangentVMatrixNode, index), weight)

            if _is2020():
                # aim 행렬 노드 생성
                aimMatrixNode = cmds.createNode('aimMatrix', name='aimMatrix0%s' % (i+1))
                cmds.connectAttr(pointMatrix, '%s.inputMatrix' % aimMatrixNode)
                cmds.connectAttr(tangentUMatrix, '%s.primaryTargetMatrix' % aimMatrixNode)
                cmds.setAttr('%s.primaryMode' % aimMatrixNode, 1)
                cmds.connectAttr(tangentVMatrix, '%s.secondaryTargetMatrix' % aimMatrixNode)
                cmds.setAttr('%s.secondaryMode' % aimMatrixNode, 1)
                aimMatrixOutput = '%s.outputMatrix' % aimMatrixNode

                # 스케일 제거
                pickMatrixNode = cmds.createNode('pickMatrix', name='noScale0%s' % (i+1))
                cmds.connectAttr(aimMatrixOutput, '%s.inputMatrix' % pickMatrixNode)
                cmds.setAttr('%s.useScale' % pickMatrixNode, False)
                cmds.setAttr('%s.useShear' % pickMatrixNode, False)
                outputMatrix = '%s.outputMatrix' % pickMatrixNode

                cmds.connectAttr(outputMatrix, '%s.offsetParentMatrix' % pNode)
            else:
                # 위치 행렬 분해
                pointDecomposeNode = cmds.createNode('decomposeMatrix', name='pointDecompose0%s' % (i+1))
                cmds.connectAttr(pointMatrix, '%s.inputMatrix' % pointDecomposeNode)
                pointVector = '%s.outputTranslate' % pointDecomposeNode

                # 탄젠트 u 행렬을 벡터로 변환
                tangentUDecomposeNode = cmds.createNode('decomposeMatrix', name='tangentUVectorDecompose0%s' % (i+1))
                cmds.connectAttr(tangentUMatrix, '%s.inputMatrix' % tangentUDecomposeNode)
                tangentUVector = '%s.outputTranslate' % tangentUDecomposeNode

                # 탄젠트 u 벡터 정규화
                tangentUNormalizeNode = cmds.createNode('vectorProduct', name='tangentUVector0%s' % (i+1))
                cmds.setAttr('%s.operation' % tangentUNormalizeNode, 0)
                cmds.setAttr('%s.normalizeOutput' % tangentUNormalizeNode, True)
                cmds.connectAttr(tangentUVector, '%s.input1' % tangentUNormalizeNode)
                xVector = '%s.output' % tangentUNormalizeNode

                # 탄젠트 v 행렬을 벡터로 변환
                tangentVDecomposeNode = cmds.createNode('decomposeMatrix', name='tangentVVectorDecompose0%s' % (i+1))
                cmds.connectAttr(tangentVMatrix, '%s.inputMatrix' % tangentVDecomposeNode)
                tangentVVector = '%s.outputTranslate' % tangentVDecomposeNode

                # 탄젠트 v 벡터 정규화
                tangentVNormalizeNode = cmds.createNode('vectorProduct', name='tangentVVector0%s' % (i+1))
                cmds.setAttr('%s.operation' % tangentVNormalizeNode, 0)
                cmds.setAttr('%s.normalizeOutput' % tangentVNormalizeNode, True)
                cmds.connectAttr(tangentVVector, '%s.input1' % tangentVNormalizeNode)
                zVector = '%s.output' % tangentVNormalizeNode

                # 외적을 사용하여 y 벡터 찾기
                yVectorNode = cmds.createNode('vectorProduct', name='yVector0%s' % (i+1))
                cmds.setAttr('%s.operation' % yVectorNode, 2)
                cmds.setAttr('%s.normalizeOutput' % yVectorNode, True)
                cmds.connectAttr(xVector, '%s.input1' % yVectorNode)
                cmds.connectAttr(zVector, '%s.input2' % yVectorNode)
                yVector = '%s.output' % yVectorNode

                # 각 축에서 aim 행렬 생성
                outputMatrixNode = cmds.createNode('fourByFourMatrix', name='outputMatrix0%s' % (i+1))
                for row, vector in enumerate([xVector, yVector, zVector, pointVector]):
                    for col, axis in enumerate(['X', 'Y', 'Z']):
                        cmds.connectAttr('%s%s' % (vector, axis), '%s.i%s%s' % (outputMatrixNode, row, col))

                # 행렬 변환 분해
                decomposeMatrixNode = cmds.createNode('decomposeMatrix', name='outputTransformations0%s' % (i+1))
                cmds.connectAttr('%s.output' % outputMatrixNode, '%s.inputMatrix' % decomposeMatrixNode)

                # 출력 연결
                cmds.connectAttr('%s.outputTranslate' % decomposeMatrixNode, '%s.translate' % pNode)
                cmds.connectAttr('%s.outputRotate' % decomposeMatrixNode, '%s.rotate' % pNode)
