import json
import re
from pathlib import Path

from .base import Writer
from core.models.document import KnowledgeDocument


class JsonlWriter(Writer):
    name = "jsonl"

    def write(self, documents: list[KnowledgeDocument], out_dir: Path, context) -> list[Path]:
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "chunks.jsonl"

        records: list[dict] = []
        for doc in documents:
            for i, sec in enumerate(doc.sections):
                record = {
                    "id": _safe_id(f"{doc.id}_{sec.id}_{i:04d}"),
                    "doc_id": doc.id,
                    "source_type": doc.source_type,
                    "source_file": doc.metadata.get("source_file", ""),
                    "title": sec.title,
                    "section_path": " > ".join(sec.section_path) if sec.section_path else "",
                    "chunk_index": i,
                    "text": sec.text,
                }
                records.append(record)

        lines = [json.dumps(r, ensure_ascii=False) for r in records]
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return [out_path]


def _safe_id(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", s)[:128]
