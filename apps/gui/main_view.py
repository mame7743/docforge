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
)


class MainView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ctx = UIContext()
        self._build_ui()

    def _build_ui(self) -> None:
        from PySide6.QtWidgets import QVBoxLayout

        layout_node = vbox(
            group(
                "入力ファイル",
                file_list(id="input_files", stretch=1),
                hbox(
                    button("ファイル追加", id="add_files"),
                    button("フォルダ追加", id="add_folder"),
                    button("削除", id="remove_file"),
                    button("バッチ設定読み込み...", id="load_config"),
                    spacer(),
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
                label("分割サイズ:"),
                spin_box(id="split_size", value=100_000, minimum=10_000, maximum=1_000_000, step=10_000),
                label("chars"),
                spacer(),
                button("フォーマット別設定...", id="format_settings_btn"),
            ),
            hbox(
                spacer(),
                button("変換開始", id="start", classes=["primary"]),
            ),
            progress_bar(id="progress"),
            group("ログ", text_edit(id="log", readonly=True, stretch=1), stretch=1),
        )

        root = build(self.ctx, layout_node)

        outer = QVBoxLayout(self)
        outer.addWidget(root, 1)
        outer.setContentsMargins(8, 8, 8, 8)

    # ------------------------------------------------------------------
    # Accessors used by MainController
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

    def out_dir(self) -> Path | None:
        text = self.ctx["out_dir"].text().strip()
        return Path(text) if text else None

    def set_out_dir(self, path: Path) -> None:
        self.ctx["out_dir"].setText(str(path))

    def export_markdown(self) -> bool:
        return self.ctx["export_markdown"].isChecked()

    def export_notebooklm(self) -> bool:
        return self.ctx["export_notebooklm"].isChecked()

    def export_jsonl(self) -> bool:
        return self.ctx["export_jsonl"].isChecked()

    def export_report(self) -> bool:
        return self.ctx["export_report"].isChecked()

    def split_size(self) -> int:
        return self.ctx["split_size"].value()

    def set_progress(self, value: int) -> None:
        self.ctx["progress"].setValue(value)

    def append_log(self, text: str) -> None:
        self.ctx["log"].append(text)

    def set_input_paths(self, paths: list[Path]) -> None:
        lw = self.ctx["input_files"]
        lw.clear()
        for p in paths:
            lw.addItem(str(p))

    def set_export_flags(
        self, *, markdown: bool, notebooklm: bool, jsonl: bool, report: bool
    ) -> None:
        self.ctx["export_markdown"].setChecked(markdown)
        self.ctx["export_notebooklm"].setChecked(notebooklm)
        self.ctx["export_jsonl"].setChecked(jsonl)
        self.ctx["export_report"].setChecked(report)

    def set_split_size(self, value: int) -> None:
        self.ctx["split_size"].setValue(value)

    def set_running(self, running: bool) -> None:  # noqa: FBT001
        self.ctx["start"].setEnabled(not running)
        self.ctx["add_files"].setEnabled(not running)
        self.ctx["add_folder"].setEnabled(not running)
        self.ctx["load_config"].setEnabled(not running)
