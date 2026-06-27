from .base import Transformer
from core.models.document import KnowledgeDocument


class NormalizeHeadingTransformer(Transformer):
    """Ensures heading levels start at 1 and have no gaps."""

    name = "normalize_heading"

    def transform(self, document: KnowledgeDocument, context) -> KnowledgeDocument:
        if not document.sections:
            return document

        levels = [sec.level for sec in document.sections]
        min_level = min(levels)

        if min_level != 1:
            shift = 1 - min_level
            for sec in document.sections:
                sec.level = max(1, sec.level + shift)

        return document
