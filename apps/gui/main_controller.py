"""メインウィンドウの Controller。

ボタンイベントを受け取り、入力を検証してから ConvertWorker を起動する。
変換結果・ログ・進捗は Worker のシグナル経由で View に届く。

スレッド安全性:
    KnowledgePipeline の log / progress コールバックは Worker スレッドから呼ばれる。
    直接 Qt ウィジェットを操作すると未定義動作になるため、
    Worker が Signal.emit() し、Qt のキュー接続でメインスレッドへ届ける設計にしている。
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QFileDialog, QMessageBox

# macOS + PySide6 でネイティブダイアログ (NSOpenPanel) を使うと
# Qt のバックバッファと衝突して segfault が起きるバグを回避する
_DIALOG_OPTIONS = QFileDialog.Option.DontUseNativeDialog

from .main_view import MainView
from core.importers import (
    ImporterRegistry,
    TextImporter,
    MarkdownImporter,
    HtmlImporter,
    ChmImporter,
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
from core.models.result import ConvertResult


class ConvertWorker(QObject):
    """KnowledgePipeline を別スレッドで実行し、結果をシグナルで通知する。"""

    log_message = Signal(str)
    progress_changed = Signal(int)
    finished = Signal(object)   # ConvertResult
    error = Signal(str)

    def __init__(self, pipeline: KnowledgePipeline, settings: ConvertSettings):
        super().__init__()
        self.settings = settings
        # pipeline の log / progress を Signal.emit にワイヤリングする。
        # emit はスレッドセーフで、Qt がキュー接続経由でメインスレッドへ届ける。
        pipeline.log = lambda msg: self.log_message.emit(msg)
        pipeline.progress = lambda v: self.progress_changed.emit(v)
        self.pipeline = pipeline

    @Slot()
    def run(self):
        try:
            result = self.pipeline.run(self.settings)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainController(QObject):
    def __init__(self, view: MainView, parent=None):
        super().__init__(parent)
        self.view = view
        self._thread: QThread | None = None
        self._worker: ConvertWorker | None = None
        self._connect_signals()

    def _connect_signals(self):
        ctx = self.view.ctx
        ctx["add_files"].clicked.connect(self._on_add_files)
        ctx["add_folder"].clicked.connect(self._on_add_folder)
        ctx["remove_file"].clicked.connect(self._on_remove_file)
        ctx["browse_out"].clicked.connect(self._on_browse_out)
        ctx["start"].clicked.connect(self._on_start)

    def _on_add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self.view,
            "ファイルを追加",
            "",
            "Documents (*.txt *.md *.html *.htm *.chm *.pdf *.docx *.xlsx *.pptx);;All Files (*)",
            options=_DIALOG_OPTIONS,
        )
        self.view.add_input_paths([Path(p) for p in paths])

    def _on_add_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self.view, "フォルダを追加", options=_DIALOG_OPTIONS
        )
        if folder:
            folder_path = Path(folder)
            exts = {".txt", ".md", ".html", ".htm", ".chm", ".pdf", ".docx", ".xlsx", ".pptx"}
            files = [p for p in folder_path.rglob("*") if p.suffix.lower() in exts]
            self.view.add_input_paths(sorted(files))

    def _on_remove_file(self):
        self.view.remove_selected_input()

    def _on_browse_out(self):
        folder = QFileDialog.getExistingDirectory(
            self.view, "出力先を選択", options=_DIALOG_OPTIONS
        )
        if folder:
            self.view.set_out_dir(Path(folder))

    def _on_start(self):
        input_paths = self.view.input_paths()
        out_dir = self.view.out_dir()

        if not input_paths:
            QMessageBox.warning(self.view, "エラー", "入力ファイルを追加してください。")
            return
        if not out_dir:
            QMessageBox.warning(self.view, "エラー", "出力先を指定してください。")
            return

        settings = ConvertSettings(
            input_paths=input_paths,
            out_dir=out_dir,
            export_markdown=self.view.export_markdown(),
            export_notebooklm=self.view.export_notebooklm(),
            export_jsonl=self.view.export_jsonl(),
            export_report=self.view.export_report(),
            split_size_chars=self.view.split_size(),
        )

        pipeline = self._build_pipeline(settings.split_size_chars)
        self._start_worker(pipeline, settings)

    def _build_pipeline(self, split_size: int) -> KnowledgePipeline:
        registry = ImporterRegistry()
        registry.register(TextImporter())
        registry.register(MarkdownImporter())
        registry.register(HtmlImporter())
        registry.register(ChmImporter())
        try:
            from core.importers.markitdown_importer import MarkItDownImporter
            registry.register(MarkItDownImporter())
        except Exception:
            pass

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
        )

    def _start_worker(self, pipeline: KnowledgePipeline, settings: ConvertSettings):
        self.view.set_running(True)
        self.view.set_progress(0)
        self.view.append_log("=== 変換開始 ===")

        self._thread = QThread()
        self._worker = ConvertWorker(pipeline, settings)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.log_message.connect(self.view.append_log)
        self._worker.progress_changed.connect(self.view.set_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    @Slot(object)
    def _on_finished(self, result: ConvertResult):
        self.view.set_progress(100)
        self.view.append_log("")
        self.view.append_log("=== 変換完了 ===")
        self.view.append_log(f"Documents : {result.document_count}")
        self.view.append_log(f"Sections  : {result.section_count}")
        self.view.append_log(f"Warnings  : {len(result.warnings)}")
        self.view.append_log("")
        self.view.append_log("出力ファイル:")
        for f in result.output_files:
            self.view.append_log(f"  {f}")
        self.view.set_running(False)

    @Slot(str)
    def _on_error(self, msg: str):
        self.view.append_log(f"エラー: {msg}")
        self.view.set_running(False)
