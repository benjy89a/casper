# scripts/01_asset/test_asset_script.py

# core.utils.maya_util 모듈을 임포트합니다.
# 프로젝트의 루트 디렉토리(casper)가 Python 경로에 포함되어 있다고 가정합니다.
from core.utils import maya_util

def run_test():
    """
    maya_util 모듈의 함수를 사용하는 테스트 함수입니다.
    """
    print("test_asset_script.py가 실행되었습니다.")
    # maya_util 모듈의 함수를 여기에 사용합니다.
    # 예시: maya_util.some_function()
    print(f"maya_util 모듈이 성공적으로 임포트되었습니다: {maya_util.__name__}")

if __name__ == "__main__":
    run_test()
