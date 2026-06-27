from __future__ import annotations

"""見出しレベルを正規化する Transformer。

CHM の内部 HTML は h2 始まりになっているケースが多く、
そのまま出力すると Markdown の構造が崩れる。
最小レベルが 1 になるようにシフトする。
"""

from .base import Transformer
from core.models.document import KnowledgeDocument
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.pipeline.context import PipelineContext


class NormalizeHeadingTransformer(Transformer):
    name = "normalize_heading"

    def transform(self, document: KnowledgeDocument, context: PipelineContext) -> KnowledgeDocument:
        if not document.sections:
            return document

        levels = [sec.level for sec in document.sections]
        min_level = min(levels)

        if min_level != 1:
            shift = 1 - min_level
            for sec in document.sections:
                sec.level = max(1, sec.level + shift)

        return document
