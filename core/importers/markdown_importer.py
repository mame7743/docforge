import re
from pathlib import Path

from .base import Importer
from core.models.document import KnowledgeDocument
from core.models.section import KnowledgeSection


class MarkdownImporter(Importer):
    name = "markdown"
    supported_extensions = {".md", ".markdown"}

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
            title=_extract_title(text) or path.stem,
            source_path=path,
            source_type="markdown",
            metadata={"source_file": str(path.name)},
        )

        sections = _parse_sections(text, doc_id, path)
        if not sections:
            sec = KnowledgeSection(
                id=f"{doc_id}_body",
                title=path.stem,
                text=text.strip(),
                level=1,
                order=0,
                source_ref=str(path),
                section_path=[path.stem],
                metadata={"source_file": str(path.name)},
            )
            doc.sections.append(sec)
        else:
            doc.sections = sections

        return doc


def _make_id(path: Path) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", path.stem)[:64]


def _extract_title(text: str) -> str | None:
    m = re.match(r"^#\s+(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else None


def _parse_sections(text: str, doc_id: str, path: Path) -> list[KnowledgeSection]:
    heading_re = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    matches = list(heading_re.finditer(text))

    if not matches:
        return []

    sections: list[KnowledgeSection] = []
    heading_stack: list[str] = []

    for i, m in enumerate(matches):
        level = len(m.group(1))
        title = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()

        while len(heading_stack) >= level:
            heading_stack.pop()
        heading_stack.append(title)

        links = _extract_links(body)
        assets = _extract_image_refs(body)

        sec = KnowledgeSection(
            id=f"{doc_id}_s{i:04d}",
            title=title,
            text=body,
            level=level,
            order=i,
            source_ref=str(path),
            section_path=list(heading_stack),
            links=links,
            assets=assets,
            metadata={"source_file": str(path.name)},
        )
        sections.append(sec)

    return sections


def _extract_links(text: str) -> list[str]:
    return re.findall(r"\[.*?\]\((.+?)\)", text)


def _extract_image_refs(text: str) -> list[str]:
    return re.findall(r"!\[.*?\]\((.+?)\)", text)
