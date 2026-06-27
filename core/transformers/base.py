from __future__ import annotations

"""Transformer の抽象基底クラス。

Transformer は KnowledgeDocument を受け取って加工し、同じ型を返す。
パイプライン上で直列に適用されるため、入力と出力の型が同じであることが重要。
"""

from abc import ABC, abstractmethod

from core.models.document import KnowledgeDocument
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.pipeline.context import PipelineContext


class Transformer(ABC):
    name: str  # パイプラインのログに表示される識別子

    @abstractmethod
    def transform(self, document: KnowledgeDocument, context: PipelineContext) -> KnowledgeDocument:
        """ドキュメントを加工して返す。元のオブジェクトを直接変更してもよい。"""
