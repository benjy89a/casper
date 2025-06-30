
from PySide2 import QtCore, QtWidgets

import pymel.core as pm
import re

'''
코어함수에서 체크박스에서 선택된 컨트롤러만 선택 할 수있도록 수정 진행하기.


'''

####CORE################################################################################################################
def normalize_part_key(tokens):
    """
    예외 포함 파트 정규화 처리
    """
    if tokens == ["sub", "up"]:
        return "subUp"
    elif tokens == ["sub", "down"]:
        return "subDown"
    elif tokens == ["tail", "big"]:
        return "tail_big"
    elif tokens == ["tail", "small"]:
        return "tail_small"
    elif tokens == ["main"]:
        return "main"
    else:
        return "_".join(tokens)

def convert_mesh_to_ctrl_prefix(mesh_name):
    """
    매쉬 이름 → 컨트롤러 접두사, 부위, 번호 추출
    """
    side_map = {"lf": "lt", "rt": "rt", "cn": "cn"}
    side_match = re.search(r"jimjo_hi_(lf|rt|cn)_", mesh_name)
    side = side_map.get(side_match.group(1), "lt") if side_match else "lt"

    part_match = re.search(r"feather_(.+?)_(\d+)$", mesh_name)
    if not part_match:
        pm.warning("매쉬 이름에서 부위/번호 추출 실패")
        return None, None, None

    raw_part = part_match.group(1)
    number_raw = part_match.group(2)

    tokens = [t for t in raw_part.split("_") if t != "wing"]
    part = normalize_part_key(tokens)

    return side, part, number_raw

def build_controller_names(mesh_name):
    side, part, number_raw = convert_mesh_to_ctrl_prefix(mesh_name)
    if not all([side, part, number_raw]):
        return []

    ctrl_names = []

    # 파트에 따라 숫자 포맷 다르게 처리
    if part in ["subUp", "subDown"]:
        number = number_raw.zfill(3)
    else:
        number = number_raw.lstrip("0") or "0"

    is_tail = "tail" in part

    for i in range(7):
        if is_tail:
            name = f"{side}_feather_{part}_proxy_{number}_crv_fk_ctrl_{i}"
        else:
            name = f"{side}_feather_{part}_proxy_{number}_crv_drv_jnt_{i}_ctrl"

        if pm.objExists(name):
            ctrl_names.append(name)

    return ctrl_names

def select_controllers_for_selected_mesh():
    sel = pm.selected()
    if not sel:
        pm.warning("매쉬를 먼저 선택해주세요.")
        return

    mesh = sel[0].name()
    ctrl_names = build_controller_names(mesh)

    if ctrl_names:
        pm.select(ctrl_names, r=True)
        print(f"선택된 컨트롤러: {ctrl_names}")
    else:
        pm.warning("컨트롤러를 찾지 못했습니다.")


####UI##################################################################################################################
class SelectFeatherCtrlUI(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(SelectFeatherCtrlUI, self).__init__(parent)

        self.setWindowTitle("Select Feather FK Ctrl")
        self.setMinimumWidth(200)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_widgets(self):
        self.checkbox0 = QtWidgets.QCheckBox("0_fk_ctl")
        self.checkbox1 = QtWidgets.QCheckBox("1_fk_ctl")
        self.checkbox2 = QtWidgets.QCheckBox("2_fk_ctl")
        self.checkbox3 = QtWidgets.QCheckBox("3_fk_ctl")
        self.checkbox4 = QtWidgets.QCheckBox("4_fk_ctl")
        self.checkbox5 = QtWidgets.QCheckBox("5_fk_ctl")
        self.button1 = QtWidgets.QPushButton("Mesh")
        self.button2 = QtWidgets.QPushButton("Close")

        self.checkbox0.setChecked(True)
        self.checkbox1.setChecked(True)
        self.checkbox2.setChecked(True)
        self.checkbox3.setChecked(True)
        self.checkbox4.setChecked(True)
        self.checkbox5.setChecked(True)

    def create_layouts(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        check_layout = QtWidgets.QHBoxLayout(self)
        check_layout.addWidget(self.checkbox0)
        check_layout.addWidget(self.checkbox1)
        check_layout.addWidget(self.checkbox2)
        check_layout.addWidget(self.checkbox3)
        check_layout.addWidget(self.checkbox4)
        check_layout.addWidget(self.checkbox5)

        main_layout.addLayout(check_layout)

        main_layout.addWidget(self.button1)
        main_layout.addWidget(self.button2)

    def create_connections(self):
        self.button1.clicked.connect(select_controllers_for_selected_mesh)
        self.button2.clicked.connect(self.close)

    def select_checked_controllers(self):
        pass


def show_window():
    global select_jimjo_feather_ctrl_window

    try:
        select_jimjo_feather_ctrl_window.close()
    except:
        pass

    select_jimjo_feather_ctrl_window = SelectFeatherCtrlUI()
    select_jimjo_feather_ctrl_window.show()

