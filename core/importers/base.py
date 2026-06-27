"""Importer の抽象基底クラス。

各 Importer は対応する拡張子を宣言し、import_file() で
KnowledgeDocument を返す。出力形式（Markdown など）は知らなくてよい。
"""

from abc import ABC, abstractmethod
from pathlib import Path

from core.models.document import KnowledgeDocument


class Importer(ABC):
    name: str                        # ImporterRegistry での識別子
    supported_extensions: set[str]   # 例: {".html", ".htm"}

    def can_import(self, path: Path) -> bool:
        return path.suffix.lower() in self.supported_extensions

    @abstractmethod
    def import_file(self, path: Path, context) -> KnowledgeDocument:
        """ファイルを読み込み KnowledgeDocument を返す。
        失敗しても例外を投げず context.warn() に記録して空のドキュメントを返すことを推奨する。
        """
