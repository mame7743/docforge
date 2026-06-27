from dataclasses import dataclass, field


@dataclass
class KnowledgeSection:
    id: str
    title: str
    text: str

    level: int = 1
    order: int = 0

    source_ref: str | None = None
    section_path: list[str] = field(default_factory=list)

    links: list[str] = field(default_factory=list)
    assets: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)

    metadata: dict[str, str] = field(default_factory=dict)
