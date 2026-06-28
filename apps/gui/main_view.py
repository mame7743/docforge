from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QWidget

from .qdom import (
    UIContext,
    build,
    vbox,
    hbox,
    group,
    spacer,
    label,
    button,
    line_edit,
    checkbox,
    text_edit,
    progress_bar,
    spin_box,
    file_list,
    combo_box,
)

from core.models.split_settings import SplitSettings

_METRIC_LABELS = ["文字数 (chars)", "トークン数 (tokens)", "ファイルサイズ (bytes)"]
_METRIC_VALUES = ["chars", "tokens", "bytes"]


class MainView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ctx = UIContext()
        self._build_ui()

    def _build_ui(self) -> None:
        from PySide6.QtWidgets import QVBoxLayout

        layout_node = vbox(
            group(
                "ドキュメント入力（ファイル単位）",
                file_list(id="input_files", stretch=1),
                hbox(
                    button("ファイルを追加...", id="add_files"),
                    button("フォルダから追加（展開）...", id="add_folder"),
                    button("削除", id="remove_file"),
                    spacer(),
                    button("バッチ設定読み込み...", id="load_config"),
                    button("フォーマット別設定...", id="format_settings_btn"),
                ),
                stretch=1,
            ),
            group(
                "フォルダ / リポジトリ入力（一括単位）",
                file_list(id="repo_list", stretch=1),
                hbox(
                    button("追加...", id="add_repo"),
                    button("削除", id="remove_repo"),
                    spacer(),
                    button("取り込み設定...", id="repo_settings_btn"),
                ),
                stretch=1,
            ),
            group(
                "出力先",
                hbox(
                    line_edit(id="out_dir", placeholder="出力ディレクトリを選択...", stretch=1),
                    button("参照", id="browse_out"),
                ),
            ),
            group(
                "出力形式",
                checkbox("Markdown Knowledge Base", id="export_markdown", checked=True),
                checkbox("NotebookLM向け分割", id="export_notebooklm", checked=True),
                checkbox("JSONL for RAG", id="export_jsonl"),
                checkbox("変換レポート", id="export_report", checked=True),
            ),
            hbox(
                checkbox("分割する", id="split_enable"),
                label("  単位:"),
                combo_box(*_METRIC_LABELS, id="split_metric"),
                label("  しきい値:"),
                spin_box(id="split_threshold", value=100_000, minimum=1_000, maximum=10_000_000, step=10_000),
                spacer(),
            ),
            hbox(
                spacer(),
                button("変換開始", id="start", classes=["primary"]),
            ),
            progress_bar(id="progress"),
            group("ログ", text_edit(id="log", readonly=True, stretch=1), stretch=1),
        )

        root = build(self.ctx, layout_node)

        # split_threshold はデフォルト無効（split_enable が OFF のとき）
        self.ctx["split_threshold"].setEnabled(False)
        self.ctx["split_metric"].setEnabled(False)
        self.ctx["split_enable"].toggled.connect(self._on_split_enable_toggled)

        outer = QVBoxLayout(self)
        outer.addWidget(root, 1)
        outer.setContentsMargins(8, 8, 8, 8)

    def _on_split_enable_toggled(self, checked: bool) -> None:
        self.ctx["split_threshold"].setEnabled(checked)
        self.ctx["split_metric"].setEnabled(checked)

    # ------------------------------------------------------------------
    # ドキュメント入力アクセサ
    # ------------------------------------------------------------------

    def input_paths(self) -> list[Path]:
        lw = self.ctx["input_files"]
        return [Path(lw.item(i).text()) for i in range(lw.count())]

    def add_input_paths(self, paths: list[Path]) -> None:
        lw = self.ctx["input_files"]
        existing = {lw.item(i).text() for i in range(lw.count())}
        for p in paths:
            if str(p) not in existing:
                lw.addItem(str(p))

    def remove_selected_input(self) -> None:
        lw = self.ctx["input_files"]
        for item in lw.selectedItems():
            lw.takeItem(lw.row(item))

    def set_input_paths(self, paths: list[Path]) -> None:
        lw = self.ctx["input_files"]
        lw.clear()
        for p in paths:
            lw.addItem(str(p))

    # ------------------------------------------------------------------
    # リポジトリ入力アクセサ
    # ------------------------------------------------------------------

    def repo_paths(self) -> list[Path]:
        lw = self.ctx["repo_list"]
        return [Path(lw.item(i).text()) for i in range(lw.count())]

    def add_repo_paths(self, paths: list[Path]) -> None:
        lw = self.ctx["repo_list"]
        existing = {lw.item(i).text() for i in range(lw.count())}
        for p in paths:
            if str(p) not in existing:
                lw.addItem(str(p))

    def remove_selected_repo(self) -> None:
        lw = self.ctx["repo_list"]
        for item in lw.selectedItems():
            lw.takeItem(lw.row(item))

    def set_repo_paths(self, paths: list[Path]) -> None:
        lw = self.ctx["repo_list"]
        lw.clear()
        for p in paths:
            lw.addItem(str(p))

    # ------------------------------------------------------------------
    # 出力先アクセサ
    # ------------------------------------------------------------------

    def out_dir(self) -> Path | None:
        text = self.ctx["out_dir"].text().strip()
        return Path(text) if text else None

    def set_out_dir(self, path: Path) -> None:
        self.ctx["out_dir"].setText(str(path))

    # ------------------------------------------------------------------
    # 出力形式アクセサ
    # ------------------------------------------------------------------

    def export_markdown(self) -> bool:
        return self.ctx["export_markdown"].isChecked()

    def export_notebooklm(self) -> bool:
        return self.ctx["export_notebooklm"].isChecked()

    def export_jsonl(self) -> bool:
        return self.ctx["export_jsonl"].isChecked()

    def export_report(self) -> bool:
        return self.ctx["export_report"].isChecked()

    def set_export_flags(
        self, *, markdown: bool, notebooklm: bool, jsonl: bool, report: bool
    ) -> None:
        self.ctx["export_markdown"].setChecked(markdown)
        self.ctx["export_notebooklm"].setChecked(notebooklm)
        self.ctx["export_jsonl"].setChecked(jsonl)
        self.ctx["export_report"].setChecked(report)

    # ------------------------------------------------------------------
    # 分割設定アクセサ
    # ------------------------------------------------------------------

    def split_enabled(self) -> bool:
        return self.ctx["split_enable"].isChecked()

    def split_metric(self) -> str:
        idx = self.ctx["split_metric"].currentIndex()
        return _METRIC_VALUES[idx] if 0 <= idx < len(_METRIC_VALUES) else "chars"

    def split_threshold(self) -> int:
        return self.ctx["split_threshold"].value()

    def split_size(self) -> int:
        """後退互換: split_enable=False のとき threshold をそのまま返す。"""
        return self.ctx["split_threshold"].value()

    def set_split_size(self, value: int) -> None:
        self.ctx["split_threshold"].setValue(value)

    def set_split_settings(self, ss: SplitSettings) -> None:
        self.ctx["split_enable"].setChecked(ss.enabled)
        idx = _METRIC_VALUES.index(ss.metric) if ss.metric in _METRIC_VALUES else 0
        self.ctx["split_metric"].setCurrentIndex(idx)
        self.ctx["split_threshold"].setValue(ss.threshold)

    # ------------------------------------------------------------------
    # ログ / 進捗
    # ------------------------------------------------------------------

    def set_progress(self, value: int) -> None:
        self.ctx["progress"].setValue(value)

    def append_log(self, text: str) -> None:
        self.ctx["log"].append(text)

    # ------------------------------------------------------------------
    # 実行中状態
    # ------------------------------------------------------------------

    def set_running(self, running: bool) -> None:  # noqa: FBT001
        self.ctx["start"].setEnabled(not running)
        self.ctx["add_files"].setEnabled(not running)
        self.ctx["add_folder"].setEnabled(not running)
        self.ctx["load_config"].setEnabled(not running)
        self.ctx["add_repo"].setEnabled(not running)
        self.ctx["remove_repo"].setEnabled(not running)
