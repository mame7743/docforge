from __future__ import annotations

"""MarkItDown ライブラリを使った Office / PDF Importer。

markitdown が変換した Markdown テキストを MarkdownImporter と同じロジックで
KnowledgeDocument に変換する。MarkItDown はコアではなくバックエンドの1つとして扱う。

インストール: pip install docforge[markitdown]
"""

from pathlib import Path

from .base import Importer
from .markdown_importer import MarkdownImporter
from core.models.document import KnowledgeDocument
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.pipeline.context import PipelineContext

try:
    from markitdown import MarkItDown
    _MARKITDOWN_AVAILABLE = True
except ImportError:
    _MARKITDOWN_AVAILABLE = False


class MarkItDownImporter(Importer):
    name = "markitdown"
    supported_extensions = {".pdf", ".docx", ".xlsx", ".pptx", ".doc", ".xls"}

    def __init__(self) -> None:
        self._md_importer = MarkdownImporter()

    def import_file(self, path: Path, context: PipelineContext) -> KnowledgeDocument:
        if not _MARKITDOWN_AVAILABLE:
            raise ImportError(
                f"markitdown not installed. Install with: uv sync --extra markitdown"
            )

        md = MarkItDown()
        result = md.convert(str(path))
        markdown_text: str = result.text_content

        # MarkdownImporter に in-memory Markdown を渡すためのアダプタ
        tmp_path = _TempMarkdownPath(path, markdown_text)
        doc = self._md_importer.import_file(tmp_path, context)  # type: ignore[arg-type]
        doc.source_type = path.suffix.lstrip(".")
        doc.metadata["source_file"] = str(path.name)
        return doc


class _TempMarkdownPath:
    """MarkdownImporter が Path として扱えるよう、インメモリ文字列をラップするアダプタ。"""

    def __init__(self, original: Path, content: str) -> None:
        self.stem = original.stem
        self.suffix = ".md"
        self.name = original.stem + ".md"
        self._content = content

    def read_text(self, encoding: str = "utf-8", errors: str = "replace") -> str:
        return self._content

    def __str__(self) -> str:
        return self.name
