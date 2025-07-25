
from PySide2 import QtWidgets, QtCore
import maya.cmds as mc
import shiboken2
import maya.OpenMayaUI as omui


def get_maya_main_window():
    """마야의 메인 윈도우를 PySide2 윈도우로 변환하여 반환"""
    main_window_ptr = omui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(main_window_ptr), QtWidgets.QWidget)



class GmanCombineUI(QtWidgets.QDialog):
    def __init__(self, parent=get_maya_main_window()):
        super(GmanCombineUI, self).__init__(parent)
        self.setWindowTitle("Gman Combine Tool")
        self.setFixedSize(300, 250)
        self.setup_ui()
        self.create_connections()

    def setup_ui(self):
        """UI를 설정합니다."""
        # 레이아웃 설정
        self.main_layout = QtWidgets.QVBoxLayout(self)

        # 선택된 버텍스 입력
        self.vertex_label = QtWidgets.QLabel("Selected Head Mesh Vertices:")
        self.vertex_input = QtWidgets.QLineEdit()
        self.vertex_input.setPlaceholderText("Select vertices and click 'Get Selection'")

        # 버튼: 선택된 버텍스 가져오기
        self.get_selection_button = QtWidgets.QPushButton("Get Selected Vertices")

        # 몸체 매쉬 입력
        self.body_label = QtWidgets.QLabel("Body Mesh:")
        self.body_input = QtWidgets.QLineEdit()
        self.body_input.setPlaceholderText("Select body mesh and click 'Get Body Mesh'")
        self.get_body_mesh_button = QtWidgets.QPushButton("Get Body Mesh")

        # 머지 거리 (Threshold)
        self.threshold_label = QtWidgets.QLabel("Merge Threshold:")
        self.threshold_input = QtWidgets.QDoubleSpinBox()
        self.threshold_input.setRange(0.001, 1.0)
        self.threshold_input.setSingleStep(0.01)
        self.threshold_input.setValue(0.01)

        # 실행 버튼
        self.run_button = QtWidgets.QPushButton("Run Combine")

        # 레이아웃 구성
        self.main_layout.addWidget(self.vertex_label)
        self.main_layout.addWidget(self.vertex_input)
        self.main_layout.addWidget(self.get_selection_button)
        self.main_layout.addWidget(self.body_label)
        self.main_layout.addWidget(self.body_input)
        self.main_layout.addWidget(self.get_body_mesh_button)
        self.main_layout.addWidget(self.threshold_label)
        self.main_layout.addWidget(self.threshold_input)
        self.main_layout.addWidget(self.run_button)

    def create_connections(self):
        """버튼과 동작 연결."""
        self.get_selection_button.clicked.connect(self.get_selected_vertices)
        self.get_body_mesh_button.clicked.connect(self.get_selected_body_mesh)
        self.run_button.clicked.connect(self.run_gman_combine)

    def get_selected_vertices(self):
        """선택된 버텍스를 가져와 UI 입력란에 표시."""
        selection = mc.ls(selection=True, flatten=True)
        if selection:
            self.vertex_input.setText(",".join(selection))
        else:
            mc.warning("No vertices selected!")

    def get_selected_body_mesh(self):
        """선택된 몸체 매쉬를 가져와 UI 입력란에 표시."""
        selection = mc.ls(selection=True, type="transform")
        if selection and len(selection) == 1:
            self.body_input.setText(selection[0])
        elif len(selection) > 1:
            mc.warning("Multiple objects selected. Please select only one body mesh.")
        else:
            mc.warning("No body mesh selected!")

    def run_gman_combine(self):
        """Combine 스크립트 실행."""
        # 입력값 가져오기
        selected_vertices = self.vertex_input.text().split(",")
        body_mesh = self.body_input.text().strip()
        threshold = self.threshold_input.value()

        if not selected_vertices or not body_mesh:
            mc.warning("Please provide both selected vertices and body mesh.")
            return

        # gman_combine_tool 실행
        try:
            gman_combine(selected_vertices, body_mesh, threshold)
        except Exception as e:
            mc.error(f"Error during gman_combine: {e}")


def gman_combine(selected_vertices, body_mesh, threshold=0.01):
    """
    Gman Combine 기능
    """
    if not selected_vertices or not body_mesh:
        mc.error("Provide both selected vertices (head) and body mesh.")

    # 버텍스 위치 가져오기
    vertex_positions = [mc.pointPosition(vtx, world=True) for vtx in selected_vertices]
    print(f"Number of selected vertices: {len(vertex_positions)}")

    # 머리와 몸체 복사
    head_mesh = selected_vertices[0].split('.')[0]
    head_copy = mc.duplicate(head_mesh, name=f"{head_mesh}_copy")[0]
    body_copy = mc.duplicate(body_mesh, name=f"{body_mesh}_copy")[0]

    # 복사본 결합
    combined_mesh = mc.polyUnite(head_copy, body_copy, name="SKIN")[0]
    mc.delete(combined_mesh, constructionHistory=True)
    print(f"Combined mesh created: {combined_mesh}")

    # 로케이터 생성 및 병합
    merge_count = 0
    locators = []

    for pos in vertex_positions:
        # 로케이터 생성
        locator = mc.spaceLocator()[0]
        mc.xform(locator, worldSpace=True, translation=pos)
        locators.append(locator)

        # 가까운 버텍스 찾기
        vertices = mc.ls(f"{combined_mesh}.vtx[*]", flatten=True)
        close_vertices = []
        for vtx in vertices:
            vtx_pos = mc.pointPosition(vtx, world=True)
            distance = ((vtx_pos[0] - pos[0]) ** 2 +
                        (vtx_pos[1] - pos[1]) ** 2 +
                        (vtx_pos[2] - pos[2]) ** 2) ** 0.5
            if distance <= threshold:
                close_vertices.append(vtx)

        # 머지 처리
        if len(close_vertices) > 1:
            mc.polyMergeVertex(close_vertices, distance=threshold)
            merge_count += 1

    # 로케이터 삭제
    mc.delete(locators)

    mc.select(combined_mesh)
    mc.delete(combined_mesh, constructionHistory=True)

    # 결과 출력
    print(f"Merges performed: {merge_count}")
    if merge_count == len(vertex_positions):
        print("Merge process completed successfully!")
    else:
        print(f"Warning: Only {merge_count} merges were performed out of {len(vertex_positions)} selected vertices.")


# UI 실행
def show_ui():
    global gman_combine_ui
    try:
        gman_combine_ui.close()  # 기존 UI 닫기
    except:
        pass
    gman_combine_ui = GmanCombineUI()
    gman_combine_ui.show()


# UI 호출
show_ui()

