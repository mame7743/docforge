from pathlib import Path

from .base import Importer
from core.models.document import KnowledgeDocument


class ImporterRegistry:
    def __init__(self):
        self.importers: list[Importer] = []

    def register(self, importer: Importer) -> None:
        self.importers.append(importer)

    def find(self, path: Path) -> Importer:
        for importer in self.importers:
            if importer.can_import(path):
                return importer
        raise ValueError(f"Unsupported file type: {path.suffix} ({path.name})")

    def supported_extensions(self) -> set[str]:
        result = set()
        for importer in self.importers:
            result.update(importer.supported_extensions)
        return result
