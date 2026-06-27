from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PipelineContext:
    work_dir: Path
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    encoding_hint: str | None = None

    def warn(self, message: str) -> None:
        self.warnings.append(message)
