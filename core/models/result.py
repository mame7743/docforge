"""KnowledgePipeline.run() が返す変換結果のサマリ。"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ConvertResult:
    output_files: list[Path] = field(default_factory=list)  # 生成したすべてのファイル

    # 主要出力へのショートカット（Pipeline が走査して設定する）
    markdown_file: Path | None = None
    notebooklm_dir: Path | None = None
    jsonl_file: Path | None = None
    report_file: Path | None = None

    # 統計
    document_count: int = 0
    section_count: int = 0
    asset_count: int = 0

    warnings: list[str] = field(default_factory=list)  # 全 context.warnings の集約
