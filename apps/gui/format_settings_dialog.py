"""フォーマット別変換設定を編集する QDialog。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.models.format_settings import FormatSettings

_TRANSFORMERS = [
    ("clean_noise", "ノイズ除去 (clean_noise)"),
    ("normalize_heading", "見出し正規化 (normalize_heading)"),
    ("enrich_metadata", "メタデータ付与 (enrich_metadata)"),
    ("link_normalizer", "リンク正規化 (link_normalizer)"),
]


class FormatSettingsDialog(QDialog):
    """拡張子ごとの変換設定を編集するダイアログ。"""

    def __init__(self, initial: dict[str, FormatSettings], parent=None):
        super().__init__(parent)
        self.setWindowTitle("フォーマット別設定")
        self.resize(680, 480)

        # 編集用バッファ（拡張子 → FormatSettings）
        self._buffer: dict[str, FormatSettings] = {
            ext: FormatSettings(
                encoding=fs.encoding,
                extra_noise_patterns=list(fs.extra_noise_patterns),
                enabled_transformers=(
                    list(fs.enabled_transformers) if fs.enabled_transformers is not None else None
                ),
                split_size_chars=fs.split_size_chars,
            )
            for ext, fs in initial.items()
        }
        self._current_ext: str | None = None

        self._build_ui()
        self._refresh_ext_list()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- 左ペイン: 拡張子リスト ---
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("対象拡張子"))

        self._ext_list = QListWidget()
        self._ext_list.currentRowChanged.connect(self._on_ext_changed)
        left_layout.addWidget(self._ext_list, 1)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("+")
        add_btn.setFixedWidth(32)
        add_btn.clicked.connect(self._on_add_ext)
        remove_btn = QPushButton("−")
        remove_btn.setFixedWidth(32)
        remove_btn.clicked.connect(self._on_remove_ext)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addStretch()
        left_layout.addLayout(btn_row)

        splitter.addWidget(left)

        # --- 右ペイン: 設定フォーム ---
        self._right = QWidget()
        right_layout = QVBoxLayout(self._right)
        right_layout.setContentsMargins(8, 0, 0, 0)

        # エンコーディング
        enc_group = QGroupBox("エンコーディング")
        enc_inner = QVBoxLayout(enc_group)
        enc_inner.addWidget(QLabel("空欄 = グローバル設定を継承（例: cp932, utf-8）"))
        self._encoding_edit = QLineEdit()
        enc_inner.addWidget(self._encoding_edit)
        right_layout.addWidget(enc_group)

        # 追加ノイズパターン
        noise_group = QGroupBox("追加ノイズパターン（1行1パターン、正規表現）")
        noise_inner = QVBoxLayout(noise_group)
        self._noise_edit = QPlainTextEdit()
        self._noise_edit.setPlaceholderText("例: Page \\d+ of \\d+")
        self._noise_edit.setMaximumHeight(100)
        noise_inner.addWidget(self._noise_edit)
        right_layout.addWidget(noise_group)

        # Transformer
        tf_group = QGroupBox("Transformer（チェックなし = 全て無効）")
        tf_inner = QVBoxLayout(tf_group)
        self._use_all_tf = QCheckBox("グローバル設定を継承（指定なし）")
        self._use_all_tf.setChecked(True)
        self._use_all_tf.stateChanged.connect(self._on_use_all_tf_changed)
        tf_inner.addWidget(self._use_all_tf)
        self._tf_checks: dict[str, QCheckBox] = {}
        for name, label_text in _TRANSFORMERS:
            cb = QCheckBox(label_text)
            cb.setChecked(True)
            self._tf_checks[name] = cb
            tf_inner.addWidget(cb)
        right_layout.addWidget(tf_group)

        # 分割サイズ上書き
        split_group = QGroupBox("分割サイズ上書き")
        split_inner = QHBoxLayout(split_group)
        self._split_override = QCheckBox("上書きする:")
        self._split_override.stateChanged.connect(self._on_split_override_changed)
        self._split_spin = QSpinBox()
        self._split_spin.setRange(1_000, 10_000_000)
        self._split_spin.setSingleStep(10_000)
        self._split_spin.setValue(100_000)
        self._split_spin.setEnabled(False)
        split_inner.addWidget(self._split_override)
        split_inner.addWidget(self._split_spin)
        split_inner.addWidget(QLabel("chars"))
        split_inner.addStretch()
        right_layout.addWidget(split_group)

        right_layout.addStretch()

        self._right.setEnabled(False)
        splitter.addWidget(self._right)
        splitter.setSizes([160, 500])

        layout.addWidget(splitter, 1)

        # ボタンボックス
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_ok)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    # ------------------------------------------------------------------
    # 内部ヘルパー
    # ------------------------------------------------------------------

    def _refresh_ext_list(self) -> None:
        self._ext_list.clear()
        for ext in sorted(self._buffer):
            self._ext_list.addItem(ext)

    def _save_current(self) -> None:
        """現在表示中の設定をバッファに保存する。"""
        if self._current_ext is None:
            return

        encoding = self._encoding_edit.text().strip() or None

        noise_lines = self._noise_edit.toPlainText().splitlines()
        extra_noise = [ln.strip() for ln in noise_lines if ln.strip()]

        if self._use_all_tf.isChecked():
            enabled_tf = None
        else:
            enabled_tf = [name for name, _ in _TRANSFORMERS if self._tf_checks[name].isChecked()]

        split_chars = self._split_spin.value() if self._split_override.isChecked() else None

        self._buffer[self._current_ext] = FormatSettings(
            encoding=encoding,
            extra_noise_patterns=extra_noise,
            enabled_transformers=enabled_tf,
            split_size_chars=split_chars,
        )

    def _load_ext(self, ext: str) -> None:
        """バッファから設定をフォームに反映する。"""
        fs = self._buffer.get(ext, FormatSettings())

        self._encoding_edit.setText(fs.encoding or "")

        self._noise_edit.setPlainText("\n".join(fs.extra_noise_patterns))

        if fs.enabled_transformers is None:
            self._use_all_tf.setChecked(True)
            for cb in self._tf_checks.values():
                cb.setChecked(True)
                cb.setEnabled(False)
        else:
            self._use_all_tf.setChecked(False)
            for name, cb in self._tf_checks.items():
                cb.setEnabled(True)
                cb.setChecked(name in fs.enabled_transformers)

        if fs.split_size_chars is not None:
            self._split_override.setChecked(True)
            self._split_spin.setValue(fs.split_size_chars)
        else:
            self._split_override.setChecked(False)
            self._split_spin.setValue(100_000)

    # ------------------------------------------------------------------
    # スロット
    # ------------------------------------------------------------------

    def _on_ext_changed(self, row: int) -> None:
        self._save_current()
        item = self._ext_list.item(row)
        if item is None:
            self._current_ext = None
            self._right.setEnabled(False)
            return
        self._current_ext = item.text()
        self._right.setEnabled(True)
        self._load_ext(self._current_ext)

    def _on_add_ext(self) -> None:
        text, ok = QInputDialog.getText(
            self, "拡張子を追加", "拡張子（例: .pdf）:", text="."
        )
        if not ok or not text.strip():
            return
        ext = text.strip().lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        if ext in self._buffer:
            QMessageBox.information(self, "情報", f"{ext} は既に登録されています。")
            return
        self._buffer[ext] = FormatSettings()
        self._refresh_ext_list()
        # 追加した拡張子を選択状態にする
        items = self._ext_list.findItems(ext, Qt.MatchFlag.MatchExactly)
        if items:
            self._ext_list.setCurrentItem(items[0])

    def _on_remove_ext(self) -> None:
        item = self._ext_list.currentItem()
        if item is None:
            return
        ext = item.text()
        self._save_current()
        self._buffer.pop(ext, None)
        self._current_ext = None
        self._right.setEnabled(False)
        self._refresh_ext_list()

    def _on_use_all_tf_changed(self, state: int) -> None:
        use_all = bool(state)
        for cb in self._tf_checks.values():
            cb.setEnabled(not use_all)
            if use_all:
                cb.setChecked(True)

    def _on_split_override_changed(self, state: int) -> None:
        self._split_spin.setEnabled(bool(state))

    def _on_ok(self) -> None:
        self._save_current()
        self.accept()

    # ------------------------------------------------------------------
    # 公開 API
    # ------------------------------------------------------------------

    def get_settings(self) -> dict[str, FormatSettings]:
        """OK 後に呼び出して編集結果を取得する。"""
        return dict(self._buffer)
