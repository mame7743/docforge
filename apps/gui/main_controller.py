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
from .format_settings_dialog import FormatSettingsDialog
from .repo_settings_dialog import RepoSettingsDialog
from core.models.format_settings import FormatSettings
from core.models.repo_settings import RepoSettings
from core.models.split_settings import SplitSettings
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
        pipeline.log = lambda msg: self.log_message.emit(msg)
        pipeline.progress = lambda v: self.progress_changed.emit(v)
        self.pipeline = pipeline

    @Slot()
    def run(self) -> None:
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
        self._format_settings: dict[str, FormatSettings] = {}
        self._file_encodings: dict[Path, str] = {}
        self._repo_settings: RepoSettings = RepoSettings()
        self._connect_signals()

    def _connect_signals(self) -> None:
        ctx = self.view.ctx
        ctx["add_files"].clicked.connect(self._on_add_files)
        ctx["add_folder"].clicked.connect(self._on_add_folder)
        ctx["remove_file"].clicked.connect(self._on_remove_file)
        ctx["browse_out"].clicked.connect(self._on_browse_out)
        ctx["start"].clicked.connect(self._on_start)
        ctx["format_settings_btn"].clicked.connect(self._on_format_settings)
        ctx["load_config"].clicked.connect(self._on_load_config)
        ctx["add_repo"].clicked.connect(self._on_add_repo)
        ctx["remove_repo"].clicked.connect(self._on_remove_repo)
        ctx["repo_settings_btn"].clicked.connect(self._on_repo_settings)

    def _on_add_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self.view,
            "ファイルを追加",
            "",
            "Documents (*.txt *.md *.html *.htm *.chm *.pdf *.docx *.xlsx *.pptx);;All Files (*)",
            options=_DIALOG_OPTIONS,
        )
        self.view.add_input_paths([Path(p) for p in paths])

    def _on_add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self.view, "フォルダを追加（ファイルを展開）", options=_DIALOG_OPTIONS
        )
        if folder:
            folder_path = Path(folder)
            exts = {".txt", ".md", ".html", ".htm", ".chm", ".pdf", ".docx", ".xlsx", ".pptx"}
            files = [p for p in folder_path.rglob("*") if p.suffix.lower() in exts]
            self.view.add_input_paths(sorted(files))

    def _on_remove_file(self) -> None:
        self.view.remove_selected_input()

    def _on_browse_out(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self.view, "出力先を選択", options=_DIALOG_OPTIONS
        )
        if folder:
            self.view.set_out_dir(Path(folder))

    def _on_format_settings(self) -> None:
        dlg = FormatSettingsDialog(self._format_settings, parent=self.view)
        from PySide6.QtWidgets import QDialog
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._format_settings = dlg.get_settings()

    def _on_add_repo(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self.view, "フォルダ / リポジトリを追加", options=_DIALOG_OPTIONS
        )
        if folder:
            self.view.add_repo_paths([Path(folder)])

    def _on_remove_repo(self) -> None:
        self.view.remove_selected_repo()

    def _on_repo_settings(self) -> None:
        dlg = RepoSettingsDialog(self._repo_settings, parent=self.view)
        from PySide6.QtWidgets import QDialog
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._repo_settings = dlg.get_settings()

    def _on_load_config(self) -> None:
        try:
            import yaml  # noqa: F401
        except ImportError:
            QMessageBox.critical(
                self.view,
                "エラー",
                "PyYAML が必要です。`pip install PyYAML` を実行してください。",
            )
            return

        path, _ = QFileDialog.getOpenFileName(
            self.view,
            "バッチコンフィグを開く",
            "",
            "YAML Files (*.yaml *.yml);;All Files (*)",
            options=_DIALOG_OPTIONS,
        )
        if not path:
            return

        from core.config.loader import load_config

        try:
            settings = load_config(Path(path))
        except Exception as e:
            QMessageBox.critical(self.view, "読み込みエラー", str(e))
            return

        # is_dir() でドキュメントとリポジトリに振り分け
        self.view.set_input_paths([p for p in settings.input_paths if not p.is_dir()])
        self.view.set_repo_paths([p for p in settings.input_paths if p.is_dir()])

        if settings.out_dir:
            self.view.set_out_dir(settings.out_dir)
        self.view.set_export_flags(
            markdown=settings.export_markdown,
            notebooklm=settings.export_notebooklm,
            jsonl=settings.export_jsonl,
            report=settings.export_report,
        )
        self.view.set_split_settings(settings.split_settings)
        self._format_settings = settings.format_settings
        self._file_encodings = settings.input_encodings
        self._repo_settings = settings.repo_settings

        n_files = len([p for p in settings.input_paths if not p.is_dir()])
        n_repos = len([p for p in settings.input_paths if p.is_dir()])
        nf = len(settings.format_settings)
        self.view.append_log(
            f"設定読み込み完了: ファイル {n_files} 件, リポジトリ {n_repos} 件, フォーマット設定 {nf} 件"
        )

    def _on_start(self) -> None:
        doc_paths = self.view.input_paths()
        repo_paths = self.view.repo_paths()
        input_paths = doc_paths + repo_paths
        out_dir = self.view.out_dir()

        if not input_paths:
            QMessageBox.warning(self.view, "エラー", "入力ファイルまたはリポジトリを追加してください。")
            return
        if not out_dir:
            QMessageBox.warning(self.view, "エラー", "出力先を指定してください。")
            return

        split_settings = SplitSettings(
            enabled=self.view.split_enabled(),
            metric=self.view.split_metric(),
            threshold=self.view.split_threshold(),
            max_sources=self.view.max_sources(),
            overflow=self.view.split_overflow(),
        )

        settings = ConvertSettings(
            input_paths=input_paths,
            out_dir=out_dir,
            export_markdown=self.view.export_markdown(),
            export_notebooklm=self.view.export_notebooklm(),
            export_jsonl=self.view.export_jsonl(),
            export_report=self.view.export_report(),
            split_size_chars=self.view.split_threshold(),
            format_settings=self._format_settings,
            input_encodings=self._file_encodings,
            repo_settings=self._repo_settings,
            split_settings=split_settings,
        )

        pipeline = self._build_pipeline(settings.split_size_chars, split_settings=split_settings)
        self._start_worker(pipeline, settings)

    def _build_pipeline(
        self,
        split_size: int,
        split_settings: SplitSettings | None = None,
    ) -> KnowledgePipeline:
        rs = self._repo_settings

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

        registry.register(GitRepoImporter(
            max_file_size=rs.max_file_size,
            include_patterns=set(rs.include_patterns) or None,
            exclude_patterns=set(rs.exclude_patterns) or None,
            branch=rs.branch,
            tag=rs.tag,
            include_gitignored=rs.include_gitignored,
            include_submodules=rs.include_submodules,
        ))

        transformers = [
            CleanNoiseTransformer(),
            NormalizeHeadingTransformer(),
            EnrichMetadataTransformer(),
            LinkNormalizerTransformer(),
        ]
        writers = [
            MarkdownWriter(),
            NotebookLMWriter(split_size_chars=split_size, split_settings=split_settings),
            JsonlWriter(),
            ReportWriter(),
        ]

        return KnowledgePipeline(
            registry=registry,
            transformers=transformers,
            writers=writers,
        )

    def _start_worker(self, pipeline: KnowledgePipeline, settings: ConvertSettings) -> None:
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
    def _on_finished(self, result: ConvertResult) -> None:
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
    def _on_error(self, msg: str) -> None:
        self.view.append_log(f"エラー: {msg}")
        self.view.set_running(False)
