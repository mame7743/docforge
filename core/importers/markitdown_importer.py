"""
MarkItDown Importer - uses markitdown library as backend.
Converts Office/PDF to Markdown, then delegates to MarkdownImporter.
"""

from pathlib import Path

from .base import Importer
from .markdown_importer import MarkdownImporter
from core.models.document import KnowledgeDocument

try:
    from markitdown import MarkItDown
    _MARKITDOWN_AVAILABLE = True
except ImportError:
    _MARKITDOWN_AVAILABLE = False


class MarkItDownImporter(Importer):
    name = "markitdown"
    supported_extensions = {".pdf", ".docx", ".xlsx", ".pptx", ".doc", ".xls"}

    def __init__(self):
        self._md_importer = MarkdownImporter()

    def import_file(self, path: Path, context) -> KnowledgeDocument:
        if not _MARKITDOWN_AVAILABLE:
            context.warn(
                f"markitdown not installed; cannot import {path.name}. "
                "Install with: pip install docforge[markitdown]"
            )
            return KnowledgeDocument(
                id=path.stem,
                title=path.stem,
                source_path=path,
                source_type=path.suffix.lstrip("."),
            )

        try:
            md = MarkItDown()
            result = md.convert(str(path))
            markdown_text = result.text_content
        except Exception as e:
            context.warn(f"MarkItDown failed for {path.name}: {e}")
            return KnowledgeDocument(
                id=path.stem,
                title=path.stem,
                source_path=path,
                source_type=path.suffix.lstrip("."),
            )

        tmp_path = _TempMarkdownPath(path, markdown_text)
        doc = self._md_importer.import_file(tmp_path, context)
        doc.source_type = path.suffix.lstrip(".")
        doc.metadata["source_file"] = str(path.name)
        return doc


class _TempMarkdownPath:
    """Thin wrapper so MarkdownImporter can read in-memory Markdown."""

    def __init__(self, original: Path, content: str):
        self.stem = original.stem
        self.suffix = ".md"
        self.name = original.stem + ".md"
        self._content = content

    def read_text(self, encoding="utf-8", errors="replace") -> str:
        return self._content

    def __str__(self) -> str:
        return self.name
