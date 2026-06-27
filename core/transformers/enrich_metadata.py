import re

from .base import Transformer
from core.models.document import KnowledgeDocument


class EnrichMetadataTransformer(Transformer):
    """Enriches section metadata with source info and derived keywords."""

    name = "enrich_metadata"

    def transform(self, document: KnowledgeDocument, context) -> KnowledgeDocument:
        for sec in document.sections:
            sec.metadata.setdefault("source_type", document.source_type)
            if document.source_path:
                sec.metadata.setdefault("source_file", document.source_path.name)
            if not sec.keywords:
                sec.keywords = _extract_keywords(sec.text)
        return document


def _extract_keywords(text: str, top_n: int = 10) -> list[str]:
    words = re.findall(r"[一-龯ぁ-んァ-ンa-zA-Z]{3,}", text)
    freq: dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq, key=lambda w: freq[w], reverse=True)
    return sorted_words[:top_n]
