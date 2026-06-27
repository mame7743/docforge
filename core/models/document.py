from dataclasses import dataclass, field
from pathlib import Path

from .section import KnowledgeSection
from .asset import KnowledgeAsset


@dataclass
class KnowledgeDocument:
    id: str
    title: str
    source_path: Path | None
    source_type: str

    sections: list[KnowledgeSection] = field(default_factory=list)
    assets: list[KnowledgeAsset] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
