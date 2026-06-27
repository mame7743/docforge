from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ConvertSettings:
    input_paths: list[Path]
    out_dir: Path

    export_markdown: bool = True
    export_notebooklm: bool = True
    export_jsonl: bool = False
    export_report: bool = True

    copy_assets: bool = True
    split_size_chars: int = 100_000

    encoding_hint: str | None = None

    enabled_importers: list[str] = field(default_factory=list)
    enabled_transformers: list[str] = field(default_factory=list)
