from abc import ABC, abstractmethod
from pathlib import Path

from core.models.document import KnowledgeDocument


class Importer(ABC):
    name: str
    supported_extensions: set[str]

    def can_import(self, path: Path) -> bool:
        return path.suffix.lower() in self.supported_extensions

    @abstractmethod
    def import_file(self, path: Path, context) -> KnowledgeDocument:
        pass
