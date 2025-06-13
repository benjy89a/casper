from maya import cmds as mc
from maya import OpenMayaUI as omui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from PySide2 import QtWidgets, QtCore
from shiboken2 import wrapInstance
from functools import partial

from func import captureViewport
from func import centerLocator
from func import openScenePath
from func import create_asset_grp

custom_mixin_window = None

class CollapsibleSection(QtWidgets.QWidget):
    """접을 수 있는 섹터 클래스"""
    def __init__(self, title, buttons, section_color, parent=None):
        super(CollapsibleSection, self).__init__(parent)

        # 메인 레이아웃
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)

        # 섹터 타이틀 버튼 (열고 닫을 수 있음)
        self.toggle_button = QtWidgets.QPushButton(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setStyleSheet(f"background-color: {section_color}; color: white; font-weight: bold;")
        self.toggle_button.toggled.connect(self.toggle_section)
        self.layout.addWidget(self.toggle_button, alignment=QtCore.Qt.AlignTop)

        # 섹터 내용
        self.buttons_layout = QtWidgets.QVBoxLayout()
        self.buttons_layout.setAlignment(QtCore.Qt.AlignTop)  # 버튼 그룹을 상단 정렬

        # 버튼 추가
        for button_name, callback in buttons:
            button = QtWidgets.QPushButton(button_name)
            button.clicked.connect(callback)  # 버튼 클릭 시 개별 함수 연결
            self.buttons_layout.addWidget(button)

        # 버튼들을 감싸는 위젯
        self.buttons_widget = QtWidgets.QWidget()
        self.buttons_widget.setLayout(self.buttons_layout)
        self.buttons_widget.setVisible(False)  # 초기엔 숨김

        self.layout.addWidget(self.buttons_widget)

    def toggle_section(self, checked):
        """섹터 열고 닫기"""
        self.buttons_widget.setVisible(checked)


class MainDockWidget(MayaQWidgetDockableMixin, QtWidgets.QWidget):

    """메인 도킹 UI"""
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # 메인 레이아웃
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # 라벨 추가
        self.title_label = QtWidgets.QLabel("Casper UI 1.0.0")
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.main_layout.addWidget(self.title_label)
        self.main_layout.setAlignment(QtCore.Qt.AlignTop)

        # RIG + CFX 프레임
        self.section_frame = QtWidgets.QFrame()
        self.section_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)  # 프레임 스타일
        self.section_frame.setFrameShadow(QtWidgets.QFrame.Raised)

        # 프레임 내부 레이아웃
        frame_layout = QtWidgets.QVBoxLayout(self.section_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)  # 섹션 간 간격

        # RIG 섹션
        rig_buttons = [
            ("Capture Viewport", self.run_capture_viewport),
            ("Center Locator", self.run_center_locator),
            ("Run Temp Script", self.run_temp_script),
            ("Create Asset Grp", self.run_create_asset_grp),
        ]
        self.rig_section = CollapsibleSection("RIG", rig_buttons, "#4CAF50")
        frame_layout.addWidget(self.rig_section)

        # CFX 섹션
        cfx_buttons = [
            ("Open Folder", self.run_open_folder),  # 필요에 따라 함수 변경
            ("CFX Button 2", self.run_example_function_3),
            ("CFX Button 3", self.run_example_function_3),
            ("CFX Button 4", self.run_example_function_4),
        ]
        self.cfx_section = CollapsibleSection("CFX", cfx_buttons, "#2196F3")
        frame_layout.addWidget(self.cfx_section)

        frame_layout.addStretch(1)

        # 프레임을 메인 레이아웃에 추가
        self.main_layout.addWidget(self.section_frame)

    def run_capture_viewport(self):
        captureViewport.capture_viewport()

    def run_center_locator(self):
        centerLocator.center_locator()

    def run_open_folder(self):
        openScenePath.openScenePath()

    def run_create_asset_grp(self):
        create_asset_grp.create_asset_grp()

    def run_temp_script(self):
        import importlib
        import sys

        # 경로가 이미 등록되어 있는지 확인
        path_to_add = r'/home/mago/casper'
        if path_to_add not in sys.path:
            sys.path.append(path_to_add)

        import runTempScript
        importlib.reload(runTempScript)

    def run_example_function_3(self):
        """예제 함수 3"""
        print("Rig Button 3: Example Function 3 실행 중...")

    def run_example_function_4(self):
        """예제 함수 4"""
        print("Rig Button 4: Example Function 4 실행 중...")

def delete_existing_dock():
    """기존 도킹 창 및 workspaceControl 삭제"""
    global custom_mixin_window

    # 도킹 컨트롤 이름
    dock_name = "customMayaMixinWindowWorkspaceControl"

    # Maya UI 시스템에서 도킹 컨트롤 삭제
    if omui.MQtUtil.findControl(dock_name) or omui.MQtUtil.findLayout(dock_name):
        try:
            mc.deleteUI(dock_name)
            print(f"Deleted existing dock: {dock_name}")
        except RuntimeError as e:
            print(f"Error deleting dock: {e}")

    # Qt 객체가 남아 있다면 삭제
    if custom_mixin_window is not None:
        custom_mixin_window.setParent(None)
        custom_mixin_window.deleteLater()
        custom_mixin_window = None
        print("Deleted existing custom_mixin_window")


def create_dock(restore=False):
    """도킹 컨트롤 생성"""
    global custom_mixin_window

    # 기존 도킹 컨트롤 삭제
    delete_existing_dock()

    if restore:
        restoredControl = omui.MQtUtil.getCurrentParent()

    # 새로운 도킹 컨트롤 생성
    custom_mixin_window = MainDockWidget()
    custom_mixin_window.setObjectName("customMayaMixinWindow")
    custom_mixin_window.setWindowTitle("Casper UI")

    if restore:
        mixinPtr = omui.MQtUtil.findControl(custom_mixin_window.objectName())
        omui.MQtUtil.addWidgetToMayaLayout(int(mixinPtr), int(restoredControl))
    else:
        custom_mixin_window.show(dockable=True, height=600, width=480, uiScript='create_dock(restore=True)')


# 실행
create_dock()
