"""Importer の登録・検索を管理するレジストリ。

登録順に can_import() を試し、最初にマッチした Importer を返す。
優先度を変えたい場合は register() の呼び出し順で制御する。
"""

from pathlib import Path

from .base import Importer


class ImporterRegistry:
    def __init__(self):
        self.importers: list[Importer] = []

    def register(self, importer: Importer) -> None:
        self.importers.append(importer)

    def find(self, path: Path) -> Importer:
        """対応する Importer を返す。見つからない場合は ValueError を送出する。"""
        for importer in self.importers:
            if importer.can_import(path):
                return importer
        raise ValueError(f"Unsupported file type: {path.suffix} ({path.name})")

    def supported_extensions(self) -> set[str]:
        result = set()
        for importer in self.importers:
            result.update(importer.supported_extensions)
        return result
