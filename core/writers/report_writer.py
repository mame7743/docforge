import datetime
from pathlib import Path

from .base import Writer
from core.models.document import KnowledgeDocument


class ReportWriter(Writer):
    name = "report"

    def write(self, documents: list[KnowledgeDocument], out_dir: Path, context) -> list[Path]:
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "docforge_report.md"

        all_warnings = list(context.warnings)
        for doc in documents:
            all_warnings.extend(doc.warnings)

        section_count = sum(len(doc.sections) for doc in documents)
        asset_count = sum(len(doc.assets) for doc in documents)

        lines: list[str] = []
        lines.append("# DocForge Conversion Report")
        lines.append("")
        lines.append(
            f"generated_at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        lines.append("")

        lines.append("## Sources")
        lines.append("")
        for doc in documents:
            src = doc.metadata.get("source_file") or (
                str(doc.source_path.name) if doc.source_path else doc.id
            )
            lines.append(f"- {src}")
        lines.append("")

        lines.append("## Summary")
        lines.append("")
        lines.append(f"- Documents: {len(documents)}")
        lines.append(f"- Sections: {section_count}")
        lines.append(f"- Assets: {asset_count}")
        lines.append(f"- Warnings: {len(all_warnings)}")
        lines.append("")

        if all_warnings:
            lines.append("## Warnings")
            lines.append("")
            for w in all_warnings:
                lines.append(f"- {w}")
            lines.append("")

        out_path.write_text("\n".join(lines), encoding="utf-8")
        return [out_path]
