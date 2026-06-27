import datetime
from pathlib import Path

from .base import Writer
from core.models.document import KnowledgeDocument
from core.models.section import KnowledgeSection


class MarkdownWriter(Writer):
    name = "markdown"

    def write(self, documents: list[KnowledgeDocument], out_dir: Path, context) -> list[Path]:
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "knowledge_base.md"

        lines: list[str] = []
        lines.append("# Knowledge Base")
        lines.append("")
        lines.append(f"generated_by: DocForge")
        lines.append(f"generated_at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"source_count: {len(documents)}")
        lines.append("")
        lines.append("---")
        lines.append("")

        for doc in documents:
            lines.extend(_render_document(doc))

        out_path.write_text("\n".join(lines), encoding="utf-8")
        return [out_path]


def _render_document(doc: KnowledgeDocument) -> list[str]:
    lines: list[str] = []
    lines.append(f"# Document: {doc.title}")
    lines.append("")

    if doc.metadata.get("source_file"):
        lines.append(f"source_type: {doc.source_type}")
        lines.append(f"source_file: {doc.metadata['source_file']}")
        lines.append("")

    for sec in doc.sections:
        lines.extend(_render_section(sec))

    lines.append("")
    lines.append("---")
    lines.append("")

    return lines


def _render_section(sec: KnowledgeSection) -> list[str]:
    lines: list[str] = []
    heading = "#" * (sec.level + 1)
    lines.append(f"{heading} {sec.title}")
    lines.append("")

    if sec.section_path:
        lines.append(f"section_path: {' > '.join(sec.section_path)}")
    if sec.source_ref:
        lines.append(f"source_ref: {sec.source_ref}")
    if sec.keywords:
        lines.append(f"keywords: {', '.join(sec.keywords)}")
    lines.append("")

    if sec.text:
        lines.append(sec.text)
        lines.append("")

    if sec.links:
        lines.append("参照リンク:")
        for lnk in sec.links:
            lines.append(f"- {lnk}")
        lines.append("")

    if sec.assets:
        lines.append("画像:")
        for asset in sec.assets:
            lines.append(f"- {asset}")
        lines.append("")

    return lines
