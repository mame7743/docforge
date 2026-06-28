"""フォーマット別設定がパイプラインに正しく適用されるかのテスト。"""

from pathlib import Path

import pytest

from core.models.format_settings import FormatSettings
from core.models.settings import ConvertSettings
from core.models.result import ConvertResult
from core.pipeline.context import PipelineContext
from core.pipeline.pipeline import KnowledgePipeline
from core.importers import ImporterRegistry, TextImporter, MarkdownImporter
from core.transformers import (
    CleanNoiseTransformer,
    NormalizeHeadingTransformer,
    EnrichMetadataTransformer,
    LinkNormalizerTransformer,
)
from core.writers import MarkdownWriter, NotebookLMWriter, ReportWriter


def _build_pipeline(**kwargs) -> KnowledgePipeline:
    registry = ImporterRegistry()
    registry.register(TextImporter())
    registry.register(MarkdownImporter())
    transformers = [
        CleanNoiseTransformer(),
        NormalizeHeadingTransformer(),
        EnrichMetadataTransformer(),
        LinkNormalizerTransformer(),
    ]
    writers = [MarkdownWriter(), NotebookLMWriter(), ReportWriter()]
    return KnowledgePipeline(registry=registry, transformers=transformers, writers=writers)


def test_extra_noise_patterns_applied(tmp_path):
    """extra_noise_patterns がテキスト内の対象行を除去すること。"""
    f = tmp_path / "doc.txt"
    f.write_text("本文テキスト\n\nSTOP HERE\n\n続きのテキスト\n", encoding="utf-8")

    settings = ConvertSettings(
        input_paths=[f],
        out_dir=tmp_path / "out",
        export_notebooklm=False,
        export_report=False,
        format_settings={
            ".txt": FormatSettings(extra_noise_patterns=["^STOP HERE$"])
        },
    )
    pipeline = _build_pipeline()
    result = pipeline.run(settings)
    kb = (tmp_path / "out" / "knowledge_base.md").read_text(encoding="utf-8")
    assert "STOP HERE" not in kb
    assert "本文テキスト" in kb


def test_enabled_transformers_filters_chain(tmp_path):
    """enabled_transformers=[clean_noise] のとき normalize_heading が実行されないこと。

    見出しレベルが h3 から始まるドキュメントでテスト。
    normalize_heading が動くと h1 に引き上げられるが、無効化されれば h3 のまま残る。
    """
    f = tmp_path / "doc.md"
    # h3 から始まるMarkdown（normalize_heading が動けば h1 になる）
    f.write_text("### セクション見出し\n\nテキスト本文\n", encoding="utf-8")

    settings = ConvertSettings(
        input_paths=[f],
        out_dir=tmp_path / "out",
        export_notebooklm=False,
        export_report=False,
        format_settings={
            ".md": FormatSettings(enabled_transformers=["clean_noise"])
        },
    )
    pipeline = _build_pipeline()
    result = pipeline.run(settings)
    kb = (tmp_path / "out" / "knowledge_base.md").read_text(encoding="utf-8")
    # normalize_heading が無効なので ### が残る（h1 には変換されない）
    assert "### セクション見出し" in kb


def test_per_format_split_size(tmp_path):
    """フォーマット別 split_size_chars が NotebookLM 出力に反映されること。"""
    # 十分長いテキストを作成（1000文字）
    f = tmp_path / "doc.txt"
    section_text = "あ" * 200 + "\n\nい" * 200 + "\n\nう" * 200
    f.write_text(section_text, encoding="utf-8")

    # split_size を 100文字に設定 → 複数ファイルに分割される
    settings = ConvertSettings(
        input_paths=[f],
        out_dir=tmp_path / "out",
        export_notebooklm=True,
        export_report=False,
        split_size_chars=100_000,
        format_settings={
            ".txt": FormatSettings(split_size_chars=100)
        },
    )
    pipeline = _build_pipeline()
    pipeline.run(settings)

    nb_dir = tmp_path / "out" / "notebooklm"
    nb_files = list(nb_dir.glob("source_*.md"))
    assert len(nb_files) > 1, "小さい split_size なので複数ファイルに分割されるはず"


def test_path_encoding_overrides_format_encoding(tmp_path):
    """パス別エンコーディングがフォーマット別エンコーディングより優先されること。

    encoding_hint の適用を TextImporter の動作で間接確認する。
    """
    f = tmp_path / "doc.txt"
    f.write_text("テストコンテンツ\n\n本文テキスト\n", encoding="utf-8")

    settings = ConvertSettings(
        input_paths=[f],
        out_dir=tmp_path / "out",
        export_notebooklm=False,
        export_report=False,
        format_settings={".txt": FormatSettings(encoding="cp932")},
        input_encodings={f: "utf-8"},  # パス別で utf-8 を上書き
    )
    pipeline = _build_pipeline()
    result = pipeline.run(settings)
    # エンコーディングが正しく utf-8 として読まれていれば警告なし
    assert not any("decode" in w.lower() or "codec" in w.lower() for w in result.warnings)
    assert result.document_count == 1


def test_no_format_settings_uses_defaults(tmp_path):
    """format_settings が空のとき従来と同じ動作をすること（後退互換）。"""
    f = tmp_path / "doc.md"
    f.write_text("# タイトル\n\nテキスト\n", encoding="utf-8")

    settings = ConvertSettings(
        input_paths=[f],
        out_dir=tmp_path / "out",
        export_notebooklm=False,
        export_report=False,
    )
    pipeline = _build_pipeline()
    result = pipeline.run(settings)
    assert result.document_count == 1
    assert result.section_count >= 1
