from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ConvertResult:
    output_files: list[Path] = field(default_factory=list)
    markdown_file: Path | None = None
    notebooklm_dir: Path | None = None
    jsonl_file: Path | None = None
    report_file: Path | None = None

    document_count: int = 0
    section_count: int = 0
    asset_count: int = 0

    warnings: list[str] = field(default_factory=list)
