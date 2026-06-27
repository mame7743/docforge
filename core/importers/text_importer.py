import re
import uuid
from pathlib import Path

from .base import Importer
from core.models.document import KnowledgeDocument
from core.models.section import KnowledgeSection


class TextImporter(Importer):
    name = "text"
    supported_extensions = {".txt", ".log"}

    def import_file(self, path: Path, context) -> KnowledgeDocument:
        encoding = getattr(context, "encoding_hint", None) or "utf-8"
        try:
            text = path.read_text(encoding=encoding, errors="replace")
        except Exception as e:
            context.warn(f"Failed to read {path.name}: {e}")
            text = ""

        doc_id = _make_id(path)
        doc = KnowledgeDocument(
            id=doc_id,
            title=path.stem,
            source_path=path,
            source_type="text",
            metadata={"source_file": str(path.name)},
        )

        paragraphs = _split_paragraphs(text)
        if not paragraphs:
            context.warn(f"Empty file: {path.name}")
            return doc

        for i, para in enumerate(paragraphs):
            sec = KnowledgeSection(
                id=f"{doc_id}_p{i:04d}",
                title=path.stem if i == 0 else f"{path.stem} ({i + 1})",
                text=para.strip(),
                level=1,
                order=i,
                source_ref=str(path),
                section_path=[path.stem],
                metadata={"source_file": str(path.name)},
            )
            doc.sections.append(sec)

        return doc


def _make_id(path: Path) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", path.stem)[:64]


def _split_paragraphs(text: str) -> list[str]:
    blocks = re.split(r"\n{2,}", text)
    return [b.strip() for b in blocks if b.strip()]
