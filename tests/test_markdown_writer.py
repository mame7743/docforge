from pathlib import Path

from core.models import KnowledgeDocument, KnowledgeSection
from core.pipeline.context import PipelineContext
from core.writers import MarkdownWriter, NotebookLMWriter


def _ctx(tmp_path):
    return PipelineContext(work_dir=tmp_path)


def _doc():
    doc = KnowledgeDocument(
        id="test_doc",
        title="Test Doc",
        source_path=Path("test.md"),
        source_type="markdown",
        metadata={"source_file": "test.md"},
    )
    doc.sections = [
        KnowledgeSection(id="s0", title="Intro", text="Introduction text.", level=1, order=0, section_path=["Intro"]),
        KnowledgeSection(id="s1", title="Details", text="Detailed content here.", level=2, order=1, section_path=["Intro", "Details"]),
    ]
    return doc


def test_markdown_writer_creates_file(tmp_path):
    ctx = _ctx(tmp_path)
    writer = MarkdownWriter()
    files = writer.write([_doc()], tmp_path, ctx)
    assert len(files) == 1
    assert files[0].name == "knowledge_base.md"
    content = files[0].read_text(encoding="utf-8")
    assert "Test Doc" in content
    assert "Introduction text." in content
    assert "source_type: markdown" in content


def test_notebooklm_writer_creates_files(tmp_path):
    ctx = _ctx(tmp_path)
    writer = NotebookLMWriter(split_size_chars=50)
    files = writer.write([_doc()], tmp_path, ctx)
    assert len(files) >= 1
    assert all(f.suffix == ".md" for f in files)
    assert files[0].parent.name == "notebooklm"
