import tempfile
from pathlib import Path

from core.importers import ImporterRegistry, TextImporter, MarkdownImporter, HtmlImporter
from core.transformers import CleanNoiseTransformer, NormalizeHeadingTransformer
from core.writers import MarkdownWriter, ReportWriter
from core.pipeline import KnowledgePipeline
from core.models.settings import ConvertSettings


def _pipeline():
    registry = ImporterRegistry()
    registry.register(TextImporter())
    registry.register(MarkdownImporter())
    registry.register(HtmlImporter())
    transformers = [CleanNoiseTransformer(), NormalizeHeadingTransformer()]
    writers = [MarkdownWriter(), ReportWriter()]
    return KnowledgePipeline(registry, transformers, writers)


def test_pipeline_basic(tmp_path):
    txt = tmp_path / "hello.txt"
    txt.write_text("Hello world\n\nSecond paragraph", encoding="utf-8")
    md = tmp_path / "doc.md"
    md.write_text("# Title\n\nBody text\n", encoding="utf-8")

    out = tmp_path / "out"
    settings = ConvertSettings(
        input_paths=[txt, md],
        out_dir=out,
        export_notebooklm=False,
        export_jsonl=False,
    )
    result = _pipeline().run(settings)

    assert result.document_count == 2
    assert result.section_count > 0
    assert result.markdown_file is not None
    assert result.markdown_file.exists()
    assert result.report_file is not None
    assert result.report_file.exists()


def test_pipeline_skips_unsupported(tmp_path):
    unsupported = tmp_path / "file.xyz"
    unsupported.write_text("data")
    out = tmp_path / "out"
    settings = ConvertSettings(
        input_paths=[unsupported],
        out_dir=out,
        export_notebooklm=False,
        export_jsonl=False,
    )
    result = _pipeline().run(settings)
    assert result.document_count == 0
    assert len(result.warnings) > 0
