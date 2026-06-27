"""DocForge の変換パイプライン本体。

処理の流れ:
    入力ファイル
      → Importer（形式ごとの読み込み）
      → KnowledgeDocument（中間モデル）
      → Transformer チェーン（ノイズ除去・正規化・メタ情報付与）
      → Writer チェーン（Markdown / JSONL / レポート 出力）
      → ConvertResult

1ファイルの失敗は警告として記録し、残りの処理を続行する。
"""

import tempfile
from pathlib import Path
from typing import Callable

from .context import PipelineContext
from core.importers.registry import ImporterRegistry
from core.models.settings import ConvertSettings
from core.models.result import ConvertResult
from core.transformers.base import Transformer
from core.writers.base import Writer


class KnowledgePipeline:
    def __init__(
        self,
        registry: ImporterRegistry,
        transformers: list[Transformer],
        writers: list[Writer],
        log: Callable[[str], None] | None = None,
        progress: Callable[[int], None] | None = None,
    ):
        self.registry = registry
        self.transformers = transformers
        self.writers = writers
        # log / progress は GUI では Signal.emit に、CLI では print に差し替えられる
        self.log = log or (lambda msg: None)
        self.progress = progress or (lambda value: None)

    def run(self, settings: ConvertSettings) -> ConvertResult:
        # 作業ディレクトリは run() のスコープ内でのみ有効。CHM 展開などに使う。
        with tempfile.TemporaryDirectory(prefix="docforge_work_") as work_dir:
            context = PipelineContext(
                work_dir=Path(work_dir),
                encoding_hint=settings.encoding_hint,
            )
            return self._run_with_context(settings, context)

    def _run_with_context(
        self, settings: ConvertSettings, context: PipelineContext
    ) -> ConvertResult:
        documents = []
        total = len(settings.input_paths)

        # --- Import フェーズ（進捗 0〜50%） ---
        for i, path in enumerate(settings.input_paths):
            try:
                importer = self.registry.find(path)
            except ValueError as e:
                context.warn(str(e))
                self.log(f"Skipped: {path.name} (unsupported)")
                self.progress(int((i + 1) / total * 50))
                continue

            self.log(f"Import: {path.name} [{importer.name}]")
            try:
                doc = importer.import_file(path, context)
            except Exception as e:
                context.warn(f"Import failed for {path.name}: {e}")
                self.log(f"Error: {path.name}: {e}")
                self.progress(int((i + 1) / total * 50))
                continue

            # Transformer は直列に適用する（順序依存あり）
            for transformer in self.transformers:
                try:
                    doc = transformer.transform(doc, context)
                except Exception as e:
                    context.warn(f"Transform error ({transformer.name}) on {path.name}: {e}")

            documents.append(doc)
            self.log(f"  -> {len(doc.sections)} sections")
            self.progress(int((i + 1) / total * 50))

        settings.out_dir.mkdir(parents=True, exist_ok=True)
        output_files: list[Path] = []

        # --- Write フェーズ（進捗 50〜100%） ---
        active_writers = self._select_writers(settings)
        for j, writer in enumerate(active_writers):
            self.log(f"Write: {writer.name}")
            try:
                files = writer.write(documents, settings.out_dir, context)
                output_files.extend(files)
            except Exception as e:
                context.warn(f"Write failed ({writer.name}): {e}")
                self.log(f"Error: {writer.name}: {e}")
            self.progress(50 + int((j + 1) / len(active_writers) * 50))

        result = ConvertResult(
            output_files=output_files,
            document_count=len(documents),
            section_count=sum(len(d.sections) for d in documents),
            asset_count=sum(len(d.assets) for d in documents),
            warnings=list(context.warnings),
        )

        # 主要出力ファイルへのショートカットを設定する
        for f in output_files:
            if f.name == "knowledge_base.md":
                result.markdown_file = f
            elif f.parent.name == "notebooklm":
                result.notebooklm_dir = f.parent
            elif f.name == "chunks.jsonl":
                result.jsonl_file = f
            elif f.name == "docforge_report.md":
                result.report_file = f

        return result

    def _select_writers(self, settings: ConvertSettings) -> list[Writer]:
        """settings のフラグに基づいて有効な Writer だけを返す。"""
        selected: list[Writer] = []
        names = {w.name: w for w in self.writers}

        if settings.export_markdown and "markdown" in names:
            selected.append(names["markdown"])
        if settings.export_notebooklm and "notebooklm" in names:
            selected.append(names["notebooklm"])
        if settings.export_jsonl and "jsonl" in names:
            selected.append(names["jsonl"])
        if settings.export_report and "report" in names:
            selected.append(names["report"])

        return selected
