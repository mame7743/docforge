from abc import ABC, abstractmethod
from pathlib import Path

from core.models.document import KnowledgeDocument


class Writer(ABC):
    name: str

    @abstractmethod
    def write(self, documents: list[KnowledgeDocument], out_dir: Path, context) -> list[Path]:
        pass
