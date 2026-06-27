"""パイプライン実行中に共有される状態オブジェクト。

Importer・Transformer・Writer はすべてこの context を受け取り、
警告の収集や作業ディレクトリへのアクセスに使う。
PySide6 に依存しないため、CLI・テスト・GUI すべてで共通利用できる。
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PipelineContext:
    work_dir: Path                         # CHM 展開などに使う一時ディレクトリ
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    encoding_hint: str | None = None       # ConvertSettings から引き継ぐ

    def warn(self, message: str) -> None:
        """警告を記録する。変換は中断せず続行する。"""
        self.warnings.append(message)
