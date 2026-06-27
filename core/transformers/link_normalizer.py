"""内部リンクをメタデータに移動する Transformer。

RAG や LLM 向けの出力では、相対パスの内部リンク（例: "../page.htm"）は
そのままでは意味をなさない。内部リンクをメタデータとして保持し、
section.links には外部 URL のみ残す。
"""

from .base import Transformer
from core.models.document import KnowledgeDocument


class LinkNormalizerTransformer(Transformer):
    name = "link_normalizer"

    def transform(self, document: KnowledgeDocument, context) -> KnowledgeDocument:
        for sec in document.sections:
            internal = [lnk for lnk in sec.links if _is_internal(lnk)]
            external = [lnk for lnk in sec.links if not _is_internal(lnk)]

            if internal:
                # セミコロン区切りで1つの文字列として保存する
                sec.metadata["internal_links"] = "; ".join(internal)
            sec.links = external

        return document


def _is_internal(url: str) -> bool:
    return not url.startswith(("http://", "https://", "ftp://", "mailto:"))
