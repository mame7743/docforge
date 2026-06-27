"""ドキュメントに含まれる画像などのアセット情報。"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class KnowledgeAsset:
    id: str
    source_path: Path   # 変換前の元パス
    output_path: Path   # 出力先パス（assets/images/... に配置）
    kind: str           # "image" / "file" など

    alt_text: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
