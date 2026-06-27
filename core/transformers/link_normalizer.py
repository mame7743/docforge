from .base import Transformer
from core.models.document import KnowledgeDocument


class LinkNormalizerTransformer(Transformer):
    """Moves internal links to section metadata for RAG compatibility."""

    name = "link_normalizer"

    def transform(self, document: KnowledgeDocument, context) -> KnowledgeDocument:
        for sec in document.sections:
            internal = [lnk for lnk in sec.links if _is_internal(lnk)]
            external = [lnk for lnk in sec.links if not _is_internal(lnk)]

            if internal:
                sec.metadata["internal_links"] = "; ".join(internal)
            sec.links = external

        return document


def _is_internal(url: str) -> bool:
    return not url.startswith(("http://", "https://", "ftp://", "mailto:"))
