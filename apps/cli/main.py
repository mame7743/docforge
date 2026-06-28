import sys
from pathlib import Path
from typing import Callable

import click

from core.importers import (
    ImporterRegistry,
    TextImporter,
    MarkdownImporter,
    HtmlImporter,
    ChmImporter,
    GitRepoImporter,
)
from core.transformers import (
    CleanNoiseTransformer,
    NormalizeHeadingTransformer,
    EnrichMetadataTransformer,
    LinkNormalizerTransformer,
)
from core.writers import (
    MarkdownWriter,
    NotebookLMWriter,
    JsonlWriter,
    ReportWriter,
)
from core.pipeline import KnowledgePipeline
from core.models.settings import ConvertSettings


def _build_pipeline(
    split_size: int,
    log: Callable[[str], None] | None = None,
    progress: Callable[[int], None] | None = None,
) -> KnowledgePipeline:
    registry = ImporterRegistry()
    registry.register(TextImporter())
    registry.register(MarkdownImporter())
    registry.register(HtmlImporter())
    registry.register(ChmImporter())

    # MarkItDownImporter registered if available
    try:
        from core.importers.markitdown_importer import MarkItDownImporter
        registry.register(MarkItDownImporter())
    except Exception:
        pass

    # GitRepoImporter: ディレクトリを最後に登録（他の Importer が処理しないパスをキャッチ）
    registry.register(GitRepoImporter())

    transformers = [
        CleanNoiseTransformer(),
        NormalizeHeadingTransformer(),
        EnrichMetadataTransformer(),
        LinkNormalizerTransformer(),
    ]

    writers = [
        MarkdownWriter(),
        NotebookLMWriter(split_size_chars=split_size),
        JsonlWriter(),
        ReportWriter(),
    ]

    return KnowledgePipeline(
        registry=registry,
        transformers=transformers,
        writers=writers,
        log=log,
        progress=progress,
    )


@click.group()
def cli():
    """DocForge - converts documents into LLM-ready Markdown knowledge bases."""


@cli.command()
@click.argument("inputs", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("-o", "--out", "out_dir", required=True, type=click.Path(), help="Output directory")
@click.option("--notebooklm/--no-notebooklm", default=True, show_default=True, help="NotebookLM split output")
@click.option("--jsonl", is_flag=True, default=False, help="JSONL output for RAG")
@click.option("--no-report", is_flag=True, default=False, help="Skip conversion report")
@click.option("--split-size", default=100_000, show_default=True, help="NotebookLM chunk size (chars)")
@click.option("--encoding", default=None, help="Force input encoding (e.g. cp932)")
def build(inputs, out_dir, notebooklm, jsonl, no_report, split_size, encoding):
    """Convert INPUT files into Markdown knowledge base."""
    input_paths = [Path(p) for p in inputs]
    settings = ConvertSettings(
        input_paths=input_paths,
        out_dir=Path(out_dir),
        export_markdown=True,
        export_notebooklm=notebooklm,
        export_jsonl=jsonl,
        export_report=not no_report,
        split_size_chars=split_size,
        encoding_hint=encoding,
    )

    def log(msg: str) -> None:
        click.echo(msg)

    pipeline = _build_pipeline(split_size=split_size, log=log)
    result = pipeline.run(settings)

    click.echo("")
    click.echo("=== DocForge Complete ===")
    click.echo(f"Documents : {result.document_count}")
    click.echo(f"Sections  : {result.section_count}")
    click.echo(f"Assets    : {result.asset_count}")
    click.echo(f"Warnings  : {len(result.warnings)}")
    click.echo("")
    click.echo("Output files:")
    for f in result.output_files:
        click.echo(f"  {f}")

    if result.warnings:
        click.echo("")
        click.echo("Warnings:")
        for w in result.warnings:
            click.echo(f"  ! {w}")


@cli.command()
@click.argument("input", type=click.Path(exists=True))
def inspect(input):
    """Show import summary for a single file without writing output."""
    path = Path(input)
    pipeline = _build_pipeline(split_size=100_000, log=click.echo)
    from core.pipeline.context import PipelineContext
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        context = PipelineContext(work_dir=Path(tmp))
        try:
            importer = pipeline.registry.find(path)
        except ValueError as e:
            click.echo(f"Error: {e}")
            sys.exit(1)

        doc = importer.import_file(path, context)
        click.echo(f"Title   : {doc.title}")
        click.echo(f"Type    : {doc.source_type}")
        click.echo(f"Sections: {len(doc.sections)}")
        for sec in doc.sections[:10]:
            click.echo(f"  [{sec.level}] {sec.title} ({len(sec.text)} chars)")
        if len(doc.sections) > 10:
            click.echo(f"  ... and {len(doc.sections) - 10} more")
        if context.warnings:
            click.echo("Warnings:")
            for w in context.warnings:
                click.echo(f"  ! {w}")


@cli.command()
@click.option("--config", "config_path", required=True, type=click.Path(exists=True), help="YAMLバッチコンフィグファイルのパス")
def batch(config_path):
    """YAMLコンフィグファイルを使って一括変換する。"""
    try:
        import yaml  # noqa: F401
    except ImportError:
        click.echo("Error: PyYAML が必要です。`pip install PyYAML` を実行してください。", err=True)
        sys.exit(1)

    from core.config.loader import load_config

    cfg_path = Path(config_path)
    try:
        settings = load_config(cfg_path)
    except Exception as e:
        click.echo(f"Error: コンフィグの読み込みに失敗しました: {e}", err=True)
        sys.exit(1)

    if not settings.input_paths:
        click.echo("Warning: コンフィグに一致する入力ファイルが見つかりません。", err=True)
        sys.exit(1)

    click.echo(f"Config : {cfg_path}")
    click.echo(f"Inputs : {len(settings.input_paths)} ファイル")
    click.echo(f"Output : {settings.out_dir}")
    if settings.format_settings:
        click.echo(f"Formats: {', '.join(sorted(settings.format_settings))}")

    def log(msg: str) -> None:
        click.echo(msg)

    pipeline = _build_pipeline(split_size=settings.split_size_chars, log=log)
    result = pipeline.run(settings)

    click.echo("")
    click.echo("=== DocForge Batch Complete ===")
    click.echo(f"Documents : {result.document_count}")
    click.echo(f"Sections  : {result.section_count}")
    click.echo(f"Assets    : {result.asset_count}")
    click.echo(f"Warnings  : {len(result.warnings)}")
    click.echo("")
    click.echo("Output files:")
    for f in result.output_files:
        click.echo(f"  {f}")

    if result.warnings:
        click.echo("")
        click.echo("Warnings:")
        for w in result.warnings:
            click.echo(f"  ! {w}")


@cli.command()
def plugins():
    """List registered importers."""
    pipeline = _build_pipeline(split_size=100_000)
    click.echo("Registered importers:")
    for imp in pipeline.registry.importers:
        exts = ", ".join(sorted(imp.supported_extensions))
        click.echo(f"  {imp.name:<20} {exts}")


if __name__ == "__main__":
    cli()
