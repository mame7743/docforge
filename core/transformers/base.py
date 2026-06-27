from abc import ABC, abstractmethod

from core.models.document import KnowledgeDocument


class Transformer(ABC):
    name: str

    @abstractmethod
    def transform(self, document: KnowledgeDocument, context) -> KnowledgeDocument:
        pass
