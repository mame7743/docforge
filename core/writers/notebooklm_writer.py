from __future__ import annotations

"""NotebookLM 向け分割 Markdown の Writer。

NotebookLM はソースを複数ファイルに分けてアップロードする形式を推奨している。
ページ（セクション）境界を維持しながら split_size_chars を超えないよう
新しいファイルへ移動させる。1セクションが巨大な場合は段落単位でさらに分割する。
"""

from pathlib import Path

from .base import Writer
from .markdown_writer import _render_section
from core.models.document import KnowledgeDocument
from core.models.section import KnowledgeSection
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.pipeline.context import PipelineContext

_DEFAULT_SPLIT_SIZE = 100_000


class NotebookLMWriter(Writer):
    name = "notebooklm"

    def __init__(self, split_size_chars: int = _DEFAULT_SPLIT_SIZE) -> None:
        self.split_size = split_size_chars

    def write(self, documents: list[KnowledgeDocument], out_dir: Path, context: PipelineContext) -> list[Path]:
        nb_dir = out_dir / "notebooklm"
        nb_dir.mkdir(parents=True, exist_ok=True)

        chunks = _collect_chunks_per_doc(documents, self.split_size)
        output_files: list[Path] = []

        for i, chunk_lines in enumerate(chunks, start=1):
            fname = nb_dir / f"source_{i:03d}.md"
            fname.write_text("\n".join(chunk_lines), encoding="utf-8")
            output_files.append(fname)

        return output_files


def _collect_chunks_per_doc(
    documents: list[KnowledgeDocument], default_split_size: int
) -> list[list[str]]:
    """ドキュメントごとに個別の split_size を適用してチャンクを収集する。"""
    all_chunks: list[list[str]] = []
    for doc in documents:
        doc_split = int(doc.metadata.get("split_size_chars", default_split_size))
        all_chunks.extend(_collect_chunks([doc], doc_split))
    return all_chunks


def _collect_chunks(
    documents: list[KnowledgeDocument], split_size: int
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
            sec_size = len(sec_text)

            # 現在のチャンクに追加するとサイズを超える場合はここで区切る
            if current_size + sec_size > split_size and current:
                flush()

            if not current:
                # 新しいチャンクの先頭にドキュメントヘッダを付ける
                current.extend(doc_header)
                current_size += sum(len(l) + 1 for l in doc_header)

            if sec_size > split_size:
                # 1セクションだけで上限を超える場合: 段落単位でさらに分割する
                for part_lines in _split_large_section(sec, split_size):
                    if current:
                        flush()
                    current.extend(doc_header)
                    current.extend(part_lines)
                    current_size = sum(len(l) + 1 for l in current)
            else:
                current.extend(sec_lines)
                current_size += sec_size

    flush()
    return chunks


def _split_large_section(sec: KnowledgeSection, split_size: int) -> list[list[str]]:
    """1セクションが split_size を超える場合に段落単位で分割する。"""
    paragraphs = sec.text.split("\n\n")
    parts: list[list[str]] = []
    current_paras: list[str] = []
    current_size = 0

    heading = "#" * (sec.level + 1)
    header = [f"{heading} {sec.title}", ""]

    for para in paragraphs:
        if current_size + len(para) > split_size and current_paras:
            lines = header + ["\n\n".join(current_paras), ""]
            parts.append(lines)
            current_paras = []
            current_size = 0
        current_paras.append(para)
        current_size += len(para)

    if current_paras:
        lines = header + ["\n\n".join(current_paras), ""]
        parts.append(lines)

    return parts
