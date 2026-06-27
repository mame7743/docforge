from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class KnowledgeAsset:
    id: str
    source_path: Path
    output_path: Path
    kind: str

    alt_text: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
