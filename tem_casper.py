'''
디벨롭할거
유아이가 있는걸 실행시킬때는 확인대화창 뜨면서 마야 뒤로 가는게 조금 불편 수정필요

런스크립트 매소드부분 이해가..

스크립트 애러발생시에 스크립트마다 차이가 있는데 이거 좀 자세한 확인 필요

'''

import os
import sys
from PySide2.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QLabel, QMessageBox
)
import maya.utils  # 메인스레드 안전 실행용


class ScriptRunner(QWidget):
    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.setWindowTitle("Python Script Runner")
        self.setGeometry(300, 200, 400, 500)

        self.layout = QVBoxLayout()
        self.label = QLabel(f"📁 스크립트 폴더: {folder_path}")
        self.layout.addWidget(self.label)

        self.load_scripts()
        self.setLayout(self.layout)

    def load_scripts(self):
        py_files = [f for f in os.listdir(self.folder_path) if f.endswith(".py")]
        if not py_files:
            msg = QLabel("⚠️ 폴더 안에 실행할 .py 파일이 없습니다.")
            self.layout.addWidget(msg)
            return

        for f in py_files:
            btn = QPushButton(f"▶ {f}")
            btn.clicked.connect(lambda checked=False, filename=f: self.run_script(filename))
            self.layout.addWidget(btn)

    def run_script(self, filename):
        """선택된 파이썬 스크립트를 Maya 내부에서 실행"""
        script_path = os.path.join(self.folder_path, filename)

        if not os.path.exists(script_path):
            QMessageBox.warning(self, "파일 없음", f"{filename} 파일을 찾을 수 없습니다.")
            return

        try:
            def _execute():
                with open(script_path, "r", encoding="utf-8") as f:
                    code = f.read()
                exec(code, globals())  # Maya 내부에서 직접 실행

            # Maya의 메인스레드에서 실행 (UI 관련 코드 포함 대비)
            maya.utils.executeInMainThreadWithResult(_execute)

            QMessageBox.information(self, "실행 완료", f"{filename} 실행이 완료되었습니다.")
        except Exception as e:
            QMessageBox.critical(self, "에러 발생", str(e))


if __name__ == "__main__":
    folder = QFileDialog.getExistingDirectory(None, "스크립트 폴더 선택")
    if folder:
        window = ScriptRunner(folder)
        window.show()
