from pathlib import Path

from core.models import KnowledgeDocument, KnowledgeSection
from core.pipeline.context import PipelineContext
from core.writers.notebooklm_writer import NotebookLMWriter, _collect_chunks


def _doc_with_large_section():
    doc = KnowledgeDocument(
        id="big", title="Big Doc", source_path=None, source_type="text",
        metadata={"source_file": "big.txt"},
    )
    doc.sections = [
        KnowledgeSection(
            id="s0", title="Huge Section", text="word " * 200,
            level=1, order=0, section_path=["Huge Section"],
        )
    ]
    return doc


def test_notebooklm_splits_large_section(tmp_path):
    ctx = PipelineContext(work_dir=tmp_path)
    writer = NotebookLMWriter(split_size_chars=100)
    docs = [_doc_with_large_section()]
    files = writer.write(docs, tmp_path, ctx)
    assert len(files) > 1


def test_collect_chunks_respects_size():
    doc = KnowledgeDocument(
        id="d", title="D", source_path=None, source_type="text",
        metadata={"source_file": "d.txt"},
    )
    for i in range(10):
        doc.sections.append(
            KnowledgeSection(id=f"s{i}", title=f"Sec {i}", text="x" * 500, level=1, order=i)
        )
    chunks = _collect_chunks([doc], split_size=1000)
    assert len(chunks) > 1
