"""ソース情報の補完とキーワード抽出を行う Transformer。

Importer が設定し忘れたメタデータを補完し、
本文の頻出語をキーワードとして付与する。
キーワードは RAG 検索やレポート表示に使われる。
"""

import re

from .base import Transformer
from core.models.document import KnowledgeDocument


class EnrichMetadataTransformer(Transformer):
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
    """出現頻度の高い単語を上位 top_n 件返す。
    日本語・英語の3文字以上の語を対象にする。
    """
    words = re.findall(r"[一-龯ぁ-んァ-ンa-zA-Z]{3,}", text)
    freq: dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq, key=lambda w: freq[w], reverse=True)
    return sorted_words[:top_n]
