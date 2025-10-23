"""
Yeti standalone Cache Exporter
Version: 1.5
"""


__version__ = "1.5"

import re
import os
import sys
import argparse

import maya.standalone
import maya.cmds as cmds



class YetiCacheExporter:
    """
    Standalone 환경에서 Yeti 캐시를 추출하는 클래스
    (UI 없이, 원본 스크립트 캐시 이름 방식 그대로)
    """

    def __init__(self, scene_file, nodes=None, start_frame=None, end_frame=None, samples=5):
        """
        :param scene_file: 캐시를 뽑을 마야 씬 경로
        :param nodes: Yeti 노드 리스트 (없으면 씬 내 모든 Yeti 노드)
        :param start_frame: 시작 프레임
        :param end_frame: 끝 프레임
        :param samples: Yeti 샘플 값
        """
        self.scene_file = scene_file
        self.samples = samples
        self.root_path = self._get_root_path(scene_file)
        self.output_root = os.path.join(self.root_path,'pub','caches','fur')
        self.nodes = nodes  # None이면 자동 탐색

        # 프레임 범위
        self.start_frame = start_frame
        self.end_frame = end_frame

        # 씬 버전 추출
        self.version = self._get_scene_version(scene_file)

        # Standalone 초기화
        maya.standalone.initialize(name="python")

    @staticmethod
    def parse_args(args):
        parser = argparse.ArgumentParser(
            description = "Yeti standalone exportor"
        )
        parser.add_argument(
            "--scenefile",
            help = "Scene file name",
            default = None
        )
        parser.add_argument(
            "--start_frame",
            type = int,
            help = "start frame",
            default = None
        )
        parser.add_argument(
            "--end_frame",
            type =int,
            help="end frame",
            default = None
        )

        parser.add_argument(
            "--samples",
            type= int,
            help="Sample count",
            default = 5
        )

        parser.add_argument(
            "--nodes",
            nargs="+",
            help=(
                "Yeti node(s) to export (optional)"
                "If the node has a namespace, please include the namespace, e.g., 'dogA:dog_yeti'."
            )
        )
        return parser.parse_args(args)

    @staticmethod
    def are_valid_arguments(opt):
        if not opt.scenefile:
            print("Scene file should be added.")
            return False
        if opt.samples <= 0:
            print("Samples must be > 0")
            return False
        return True


    def _get_root_path(self, path):
        parts = path.replace("//","/").split("/")

        root_path = "/".join(parts[:9])
        '''
        if "hair" in parts:
            hair_index = parts.index("hair")
            root_path = "/".join(parts[:hair_index + 1])
        else:
            root_path = os.path.dirname(path)
        '''
        return root_path

    def _get_scene_version(self, path):
        """씬 파일 이름에서 _v 패턴 추출"""
        m = re.search(r"v([0-9]{2,3})", path)
        return int(m.group(1)) if m else 1

    def _get_yeti_nodes(self):
        """씬 내 Yeti 노드 탐색"""
        all_nodes = cmds.ls(type="pgYetiMaya") or []

        if self.nodes:
            shapes_from_transforms = []
            for n in self.nodes:
                shapes = cmds.listRelatives(n, shapes=True, type="pgYetiMaya") or []
                if not shapes:
                    raise RuntimeError(f"[ERROR] 씬에서 Yeti 노드를 찾을 수 없습니다: {n}")
                shapes_from_transforms.extend(shapes)
            return shapes_from_transforms

        if not all_nodes:
            raise RuntimeError("[ERROR] 씬에 Yeti 노드가 존재하지 않습니다.")
        return all_nodes

    def _get_cache_path(self, node):
        """
        노드별 캐시 경로 생성 (원본 스크립트 방식) + 네임스페이스 처리
        - 네임스페이스가 있으면 캐시 폴더는 namespace/part_name
        - 네임스페이스가 없으면 asset_name/part_name

        """
        node_long = cmds.ls(node,long=True)[0]
        node_clean = node_long.split("|")[-1]

        #네임스페이스 분리
        if ":" in node_clean:
            namespace, base_name = node_clean.split(":",1)
        else:
            namespace, base_name = None, node_clean

        # 노드에서 _yetiShape 제거
        base_name = base_name.replace("_yetiShape", "")

        # assetName / partName 추출
        if "_" in base_name:
            asset_name, part_name = base_name.split("_",1)
        else:
            asset_name, part_name = base_name , "main"

        # part_name에서 _yeti 제거
        if part_name.endswith("_yeti"):
            part_name = part_name.rsplit("_",1)[0]

        file_name = f"{asset_name}_{part_name}.%04d.fur"

        # 기본 폴더: output_root / 버전 / asset_name(namespace) / part_name
        if namespace:
            cache_dir = os.path.join(self.output_root, f"v{self.version:03d}", namespace, part_name)
        else:
            cache_dir = os.path.join(self.output_root, f"v{self.version:03d}", asset_name, part_name)

        os.makedirs(cache_dir, exist_ok=True)

        # 캐시 파일 경로
        cache_path = os.path.join(cache_dir, file_name)
        return cache_path

    def export(self):
        """Yeti 캐시 추출"""
        # 씬 열기
        print(f"[START] Exporting Yeti caches from scene: {self.scene_file}")
        cmds.file(self.scene_file, o=True, force=True)

        # 프레임 범위가 None으로 입력 받을경우 자동 추출
        start = (self.start_frame - 5) if self.start_frame else int(cmds.playbackOptions(q=True, min=True)) - 5
        end = (self.end_frame + 5) if self.end_frame else int(cmds.playbackOptions(q=True, max=True)) + 5

        exported_paths = []
        for node in self._get_yeti_nodes():
            cache_path = self._get_cache_path(node)
            # pgYetiCommand 실행
            cmds.pgYetiCommand(node, writeCache=cache_path, range=(start, end), samples=self.samples)
            print(f"[SUCCESS] Exported: {cache_path}")
            exported_paths.append(cache_path)

        return exported_paths

    def cleanup(self):
        """Standalone 종료"""
        maya.standalone.uninitialize()

if __name__ == '__main__':

    opts = YetiCacheExporter.parse_args(sys.argv[1:])
    if not YetiCacheExporter.are_valid_arguments(opts):
        sys.exit(1)

    if not os.path.exists(opts.scenefile):
        print(f"[WARNING] 씬 파일을 찾을 수 없습니다: {opts.scenefile}")
        sys.exit(1)


    exporter = YetiCacheExporter(
        scene_file=opts.scenefile,
        start_frame=opts.start_frame,
        end_frame=opts.end_frame,
        samples=opts.samples,
        nodes=opts.nodes
    )
    exported_paths = exporter.export()
    exporter.cleanup()
    print(f"[ALL DONE] Export finished for {len(exported_paths)} nodes.")
