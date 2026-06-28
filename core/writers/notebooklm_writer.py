from __future__ import annotations

"""NotebookLM 向け分割 Markdown の Writer。

split_settings.enabled=False（デフォルト）: 全コンテンツを1ファイルに統合する。
split_settings.enabled=True: metric と threshold に基づいてファイルを分割する。
1セクションが巨大な場合は段落単位でさらに分割する。
"""

from pathlib import Path

from .base import Writer
from .markdown_writer import _render_section
from core.models.document import KnowledgeDocument
from core.models.section import KnowledgeSection
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.pipeline.context import PipelineContext
    from core.models.split_settings import SplitSettings

_DEFAULT_SPLIT_SIZE = 100_000


class NotebookLMWriter(Writer):
    name = "notebooklm"

    def __init__(
        self,
        split_size_chars: int = _DEFAULT_SPLIT_SIZE,
        split_settings: "SplitSettings | None" = None,
    ) -> None:
        self.split_size = split_size_chars
        self.split_settings = split_settings

    def write(self, documents: list[KnowledgeDocument], out_dir: Path, context: "PipelineContext") -> list[Path]:
        nb_dir = out_dir / "notebooklm"
        nb_dir.mkdir(parents=True, exist_ok=True)

        chunks = _collect_chunks_for_output(documents, self.split_size, self.split_settings)
        output_files: list[Path] = []

        for i, chunk_lines in enumerate(chunks, start=1):
            fname = nb_dir / f"source_{i:03d}.md"
            fname.write_text("\n".join(chunk_lines), encoding="utf-8")
            output_files.append(fname)

        return output_files


def _measure(text: str, metric: str) -> int:
    if metric == "tokens":
        return len(text) // 4
    elif metric == "bytes":
        return len(text.encode("utf-8"))
    return len(text)  # "chars"（デフォルト）


def _collect_chunks_for_output(
    documents: list[KnowledgeDocument],
    default_split_size: int,
    split_settings: "SplitSettings | None",
) -> list[list[str]]:
    if split_settings is None or not split_settings.enabled:
        # デフォルト動作: 後退互換の per-doc split_size ロジックを使う
        return _collect_chunks_per_doc(documents, default_split_size)
    return _collect_chunks_per_doc_with_metric(documents, split_settings)


def _collect_chunks_per_doc(
    documents: list[KnowledgeDocument], default_split_size: int
) -> list[list[str]]:
    """後退互換: ドキュメントごとに個別の split_size を適用してチャンクを収集する。"""
    all_chunks: list[list[str]] = []
    for doc in documents:
        doc_split = int(doc.metadata.get("split_size_chars", default_split_size))
        all_chunks.extend(_collect_chunks([doc], doc_split))
    return all_chunks


def _collect_chunks_per_doc_with_metric(
    documents: list[KnowledgeDocument], split_settings: "SplitSettings"
) -> list[list[str]]:
    """SplitSettings の metric と threshold を使ってチャンクを収集する。"""
    all_chunks: list[list[str]] = []
    for doc in documents:
        doc_threshold = int(doc.metadata.get("split_size_chars", split_settings.threshold))
        all_chunks.extend(_collect_chunks([doc], doc_threshold, split_settings.metric))
    return all_chunks


def _collect_chunks(
    documents: list[KnowledgeDocument], split_size: int, metric: str = "chars"
) -> list[list[str]]:
    """ドキュメントリストをセクション単位で分割し、各チャンクの行リストを返す。"""
    chunks: list[list[str]] = []
    current: list[str] = []
    current_size = 0

    def flush() -> None:
        nonlocal current, current_size
        if current:
            chunks.append(current)
        current = []
        current_size = 0

    for doc in documents:
        doc_header = [f"# {doc.title}", ""]
        if doc.metadata.get("source_file"):
            doc_header += [
                f"source_type: {doc.source_type}",
                f"source_file: {doc.metadata['source_file']}",
                "",
            ]

        for sec in doc.sections:
            sec_lines = _render_section(sec)
            sec_text = "\n".join(sec_lines)
            sec_size = _measure(sec_text, metric)

            if current_size + sec_size > split_size and current:
                flush()

            if not current:
                current.extend(doc_header)
                current_size += _measure("\n".join(doc_header), metric)

            if sec_size > split_size:
                for part_lines in _split_large_section(sec, split_size, metric):
                    if current:
                        flush()
                    current.extend(doc_header)
                    current.extend(part_lines)
                    current_size = _measure("\n".join(current), metric)
            else:
                current.extend(sec_lines)
                current_size += sec_size

    flush()
    return chunks


def _split_large_section(sec: KnowledgeSection, split_size: int, metric: str = "chars") -> list[list[str]]:
    """1セクションが split_size を超える場合に段落単位で分割する。"""
    paragraphs = sec.text.split("\n\n")
    parts: list[list[str]] = []
    current_paras: list[str] = []
    current_size = 0

    heading = "#" * (sec.level + 1)
    header = [f"{heading} {sec.title}", ""]

    for para in paragraphs:
        para_size = _measure(para, metric)
        if current_size + para_size > split_size and current_paras:
            lines = header + ["\n\n".join(current_paras), ""]
            parts.append(lines)
            current_paras = []
            current_size = 0
        current_paras.append(para)
        current_size += para_size

    if current_paras:
        lines = header + ["\n\n".join(current_paras), ""]
        parts.append(lines)

    return parts
