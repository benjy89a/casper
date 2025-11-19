# -*- coding: utf-8 -*-

"""
============================
Casper Script Runner for Maya (v5.0 Final)
============================

[기능]
- 지정된 폴더와 그 하위 폴더의 .py 스크립트 목록을 탭으로 구분하여 UI에 표시합니다.
- 스크립트 버튼을 좌클릭하면 스크립트를 실행하고, 우클릭하면 해당 스크립트의 도움말(docstring)을 표시합니다.
- 마지막으로 사용한 폴더 경로를 'casper_config.txt'에 자동 저장하여 다음 실행 시 자동으로 로드합니다.
- '폴더 변경' 버튼을 통해 언제든지 스크립트 루트 폴더를 변경하고 저장할 수 있습니다.
- UI는 항상 Maya 위에 표시되며, Maya 종료 시 함께 닫힙니다.
- 상세한 에러 로그, 새로고침, 스크롤 등 다양한 편의 기능을 제공합니다.

[실행 방법]
Maya 스크립트 에디터에서 이 파일의 모든 코드를 실행하거나,
아래의 `launch()` 함수를 호출하세요.

launch()
"""

import os
import sys
import traceback
import random
import ast

from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QMessageBox, QScrollArea, QTabWidget
)
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
import maya.utils

# --- 설정 파일 관리 ---
# 이 스크립트 파일이 있는 디렉토리를 기준으로 설정 파일 경로를 정합니다.
CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "casper_config.txt")


def read_config():
    """설정 파일에서 마지막으로 사용한 폴더 경로를 읽어옵니다."""
    if os.path.exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def write_config(path):
    """선택한 폴더 경로를 설정 파일에 저장합니다."""
    with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(path)


# --- Maya UI 및 스크립트 분석 유틸리티 ---
def get_maya_main_window():
    """Maya의 메인 윈도우 위젯을 반환합니다."""
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QWidget)


def _extract_docstring(file_path):
    """Python 스크립트 파일에서 최상위 docstring을 안전하게 추출합니다."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        return ast.get_docstring(tree)
    except Exception:
        return ""


# --- 커스텀 UI 위젯 ---
class CustomScriptButton(QPushButton):
    """좌클릭과 우클릭 이벤트를 구분하는 커스텀 버튼입니다."""
    rightClicked = Signal(str)

    def __init__(self, text, script_path, parent=None):
        super().__init__(text, parent)
        self.script_path = script_path

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.rightClicked.emit(self.script_path)
        else:
            super().mousePressEvent(event)


# --- 메인 UI 클래스 ---
class ScriptRunner(QWidget):
    BUTTON_COLORS = ["#555555", "#666666", "#4a6a7f", "#7f6c4a", "#4f7f4a"]
    IGNORE_FOLDERS = {"__pycache__", ".git", ".venv", ".vscode"}
    IGNORE_FILES = {"__init__.py"}

    def __init__(self, folder_path, parent=get_maya_main_window()):
        super().__init__(parent)
        self.folder_path = folder_path
        self.setWindowFlags(Qt.Window)
        self.setWindowTitle("Casper Script Runner v5.0 (Final)")
        self.setGeometry(300, 200, 450, 550)

        main_layout = QVBoxLayout(self)

        # --- 상단 UI (폴더 경로, 버튼들) ---
        top_layout = QHBoxLayout()
        self.label = QLabel(f"📁 루트 폴더: {self.folder_path}")
        self.label.setWordWrap(True)

        change_folder_btn = QPushButton("📂 폴더 변경")
        change_folder_btn.clicked.connect(self.change_folder)

        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.clicked.connect(self.refresh_scripts)

        top_layout.addWidget(self.label, 1)
        top_layout.addWidget(change_folder_btn)
        top_layout.addWidget(refresh_btn)
        main_layout.addLayout(top_layout)

        # --- 탭 위젯 UI ---
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #333; background-color: #3a3a3a; }
            QTabBar::tab { background: #454545; border: 1px solid #333; border-bottom-color: #3a3a3a; border-top-left-radius: 4px; border-top-right-radius: 4px; padding: 5px 10px; color: #ccc; font-weight: bold; }
            QTabBar::tab:selected { background: #606060; border-color: #333; border-bottom-color: #606060; color: white; }
            QTabBar::tab:hover { background: #505050; }
        """)
        main_layout.addWidget(self.tab_widget)

        self.load_scripts()

    def change_folder(self):
        """'폴더 변경' 버튼 클릭 시, 새로운 폴더를 선택하고 UI를 갱신합니다."""
        new_folder = QFileDialog.getExistingDirectory(self, "새로운 스크립트 루트 폴더를 선택하세요", self.folder_path)
        if new_folder and new_folder != self.folder_path:
            self.folder_path = new_folder
            write_config(new_folder)  # 새로운 경로를 설정 파일에 저장
            self.label.setText(f"📁 루트 폴더: {new_folder}")
            self.refresh_scripts()

    def _create_script_tab(self, target_folder, tab_name):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        scroll_widget = QWidget()
        button_layout = QVBoxLayout(scroll_widget)
        button_layout.setAlignment(Qt.AlignTop)

        scroll_area.setWidget(scroll_widget)

        try:
            py_files = sorted(
                [f for f in os.listdir(target_folder) if f.endswith(".py") and f not in self.IGNORE_FILES],
                key=str.lower)

            if not py_files:
                button_layout.addWidget(QLabel("⚠️ 이 폴더에 실행할 .py 파일이 없습니다."))
            else:
                last_color_index = -1
                for f in py_files:
                    current_color_index = last_color_index
                    while current_color_index == last_color_index:
                        current_color_index = random.randint(0, len(self.BUTTON_COLORS) - 1)

                    color = self.BUTTON_COLORS[current_color_index]
                    last_color_index = current_color_index

                    full_script_path = os.path.join(target_folder, f)
                    display_name = os.path.splitext(f)[0]

                    btn = CustomScriptButton(f"▶ {display_name}", full_script_path)
                    btn.setStyleSheet(f"background-color: {color}; color: white; font-size: 12pt; padding: 5px;")
                    btn.clicked.connect(lambda checked=False, path=full_script_path: self.run_script(path))
                    btn.rightClicked.connect(self.show_script_help)
                    button_layout.addWidget(btn)
        except Exception as e:
            button_layout.addWidget(QLabel(f"🚫 폴더를 읽는 중 에러 발생:\n{e}"))

        self.tab_widget.addTab(scroll_area, tab_name)

    def refresh_scripts(self):
        self.tab_widget.clear()
        self.load_scripts()
        print("스크립트 목록을 새로고침했습니다.")

    def load_scripts(self):
        root_folder_name = os.path.basename(self.folder_path)
        self._create_script_tab(self.folder_path, f"📁 {root_folder_name}")

        try:
            subfolders = sorted([d for d in os.listdir(self.folder_path) if
                                 os.path.isdir(os.path.join(self.folder_path, d)) and d not in self.IGNORE_FOLDERS],
                                key=str.lower)
            for folder in subfolders:
                full_folder_path = os.path.join(self.folder_path, folder)
                self._create_script_tab(full_folder_path, f"📂 {folder}")
        except Exception as e:
            QMessageBox.critical(self, "폴더 스캔 에러", f"하위 폴더를 스캔하는 중 에러가 발생했습니다:\n{str(e)}")

    def run_script(self, script_path):
        filename = os.path.basename(script_path)
        if not os.path.exists(script_path):
            QMessageBox.warning(self, "파일 없음", f"{filename} 파일을 찾을 수 없습니다.")
            return

        print(f"'{filename}' 스크립트 실행을 시작합니다... (경로: {script_path})")
        try:
            def _execute():
                with open(script_path, "r", encoding="utf-8") as f:
                    code = f.read()
                exec(code, globals())

            maya.utils.executeInMainThreadWithResult(_execute)
            print(f"'{filename}' 스크립트 실행이 완료되었습니다.")
        except Exception as e:
            detailed_error_message = traceback.format_exc()
            print(f"'{filename}' 실행 중 에러 발생:\n{detailed_error_message}")
            QMessageBox.critical(self, "스크립트 실행 에러", f"'{filename}' 실행 중 에러가 발생했습니다:\n\n{detailed_error_message}")

    def show_script_help(self, script_path):
        filename = os.path.basename(script_path)
        docstring = _extract_docstring(script_path)

        if not docstring:
            docstring = "이 스크립트에는 작성된 도움말(docstring)이 없습니다."

        QMessageBox.information(self, f"'{filename}' 도움말", docstring)


# --- Maya에서 실행하기 위한 코드 ---
casper_runner_instance = None


def launch():
    """Casper 스크립트 실행기를 시작하는 함수."""
    global casper_runner_instance
    if casper_runner_instance:
        casper_runner_instance.close()
        casper_runner_instance.deleteLater()

    # 프로젝트 루트 경로를 sys.path에 추가하여 다른 모듈을 임포트할 수 있도록 합니다.
    # 이 스크립트(casper_ui.py)는 runner 폴더 안에 있으므로,
    # os.path.dirname(os.path.abspath(__file__))은 'runner' 폴더 경로를 반환합니다.
    # 여기서 한 번 더 os.path.dirname을 사용하여 'casper' 프로젝트 루트 경로를 얻습니다.
    project_root = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(project_root)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"프로젝트 루트 경로를 sys.path에 추가했습니다: {project_root}")

    folder_to_load = read_config()

    # 설정 파일에 유효한 경로가 없으면 사용자에게 폴더 선택을 요청
    if not folder_to_load or not os.path.isdir(folder_to_load):
        folder_to_load = QFileDialog.getExistingDirectory(get_maya_main_window(), "실행할 스크립트가 있는 루트 폴더를 선택하세요")

    # 사용자가 폴더를 선택했거나 유효한 경로가 있는 경우에만 UI 실행
    if folder_to_load:
        write_config(folder_to_load)  # 선택된 경로를 다음 실행을 위해 저장
        casper_runner_instance = ScriptRunner(folder_to_load)
        casper_runner_instance.show()
    else:
        print("Casper 실행기: 폴더가 선택되지 않아 실행을 취소했습니다.")

# Maya 스크립트 에디터에서 아래 함수를 실행하세요.
# launch()

