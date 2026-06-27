"""Writer の抽象基底クラス。

Writer は KnowledgeDocument のリストを受け取り、
出力ファイルのパスリストを返す。
出力形式（Markdown / JSONL / レポートなど）は各サブクラスで決める。
"""

from abc import ABC, abstractmethod
from pathlib import Path

from core.models.document import KnowledgeDocument


class Writer(ABC):
    name: str  # パイプラインでの識別子

    @abstractmethod
    def write(self, documents: list[KnowledgeDocument], out_dir: Path, context) -> list[Path]:
        """ドキュメントを出力し、生成したファイルのパスリストを返す。"""
