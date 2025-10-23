
# Yeti Standalone Cache Exporter

Standalone 환경에서 Maya Yeti 캐시를 추출하는 Python 스크립트입니다.  
마야 GUI 없이 `mayapy`로 실행 가능하며, 씬 파일 경로만 지정하면 자동으로 Yeti 노드를 검색하고 캐시를 추출합니다.

---
### 버전히스토리
- **v1.5** (2025-10-23)
  - 네임스페이스 있는 Yeti 노드 처리 방식 개선
  - 원하는 Yeti 노드만 익스포트 가능하게 개선
  - 아규먼트 사용할 수 있게 기능 개선


- **v1.0** (2025-09-10)
  - Standalone 환경에서 실행
  - 기본 Yeti 캐시 추출 스크립트
  - 모든 Yeti 노드 익스포트
---
### 아규먼트

- scene_file : 예티캐쉬를 뽑기 위한 씬 파일 경로(필수)
- start_frame / end_frame : 캐시 추출 프레임 범위
  - 지정하지 않으면 씬 내 플레이백 범위를 자동으로 사용합니다.
  - 모션 블러용으로 시작 프레임 -5, 끝 프레임 +5를 적용합니다.
- samples : Yeti 캐시 샘플 값 (기본: 5)
- nodes : 추출한 Yeti 노드 리스트(선택)
  - 입력하지 않으면 씬 내 모든 Yeti 노드를 대상으로 합니다.
  - 노드 이름에 네임스페이스가 포함되어 있다면 **반드시 네임스페이스까지 포함** 해서 입력해야합니다.
    예시: '--nodes "dogA:dog_yeti" "dogB:dog_yeti"'

---

### 사용법

1. 터미널에서 쉘 스크립트 실행 (예시):
'''
run_yeti_standalone_export.sh --scenefile "씬패스경로"
'''

---
### 참고사항

- 쉘 스크립트 파일 위치
'''
/storage/inhouse/rez/bin//run_yeti_standalone_export.sh
'''
- 터미널에서 예티캐시 뽑을때 강제종료 하는법
  - ctrl + c 를 누르면 캐쉬를 뽑는도중 강제종료가 됩니다.
