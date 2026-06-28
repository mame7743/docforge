"""リポジトリ取り込み設定ダイアログ。"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QCheckBox,
    QSpinBox,
    QVBoxLayout,
)

from core.models.repo_settings import RepoSettings


class RepoSettingsDialog(QDialog):
    def __init__(self, initial: RepoSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("リポジトリ設定")
        self.setMinimumWidth(480)
        self._build_ui(initial)

    def _build_ui(self, rs: RepoSettings) -> None:
        layout = QVBoxLayout(self)

        # --- ブランチ / タグ ---
        branch_group = QGroupBox("ブランチ / タグ")
        branch_layout = QFormLayout(branch_group)

        self._branch = QLineEdit(rs.branch or "")
        self._branch.setPlaceholderText("（空欄 = デフォルトブランチ）")
        branch_layout.addRow("ブランチ:", self._branch)

        self._tag = QLineEdit(rs.tag or "")
        self._tag.setPlaceholderText("（空欄 = タグ指定なし）")
        branch_layout.addRow("タグ:", self._tag)

        layout.addWidget(branch_group)

        # --- インクルードパターン ---
        inc_group = QGroupBox("インクルードパターン（1行1パターン、空=全ファイル）")
        inc_layout = QVBoxLayout(inc_group)
        self._include = QPlainTextEdit("\n".join(rs.include_patterns))
        self._include.setPlaceholderText("例: *.py\n*.md")
        self._include.setFixedHeight(80)
        inc_layout.addWidget(self._include)
        layout.addWidget(inc_group)

        # --- エクスクルードパターン ---
        exc_group = QGroupBox("エクスクルードパターン（1行1パターン）")
        exc_layout = QVBoxLayout(exc_group)
        self._exclude = QPlainTextEdit("\n".join(rs.exclude_patterns))
        self._exclude.setPlaceholderText("例: node_modules/\n*.min.js")
        self._exclude.setFixedHeight(80)
        exc_layout.addWidget(self._exclude)
        layout.addWidget(exc_group)

        # --- ファイルサイズ上限 / オプション ---
        opt_group = QGroupBox("オプション")
        opt_layout = QFormLayout(opt_group)

        size_row = QHBoxLayout()
        self._max_file_size = QSpinBox()
        self._max_file_size.setRange(1_000, 10_000_000)
        self._max_file_size.setSingleStep(10_000)
        self._max_file_size.setValue(rs.max_file_size)
        size_row.addWidget(self._max_file_size)
        size_row.addWidget(QLabel("bytes"))
        size_row.addStretch()
        opt_layout.addRow("ファイルサイズ上限:", size_row)

        self._include_gitignored = QCheckBox(".gitignore されたファイルも含める")
        self._include_gitignored.setChecked(rs.include_gitignored)
        opt_layout.addRow("", self._include_gitignored)

        self._include_submodules = QCheckBox("サブモジュールを含める")
        self._include_submodules.setChecked(rs.include_submodules)
        opt_layout.addRow("", self._include_submodules)

        layout.addWidget(opt_group)

        # --- ボタン ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_settings(self) -> RepoSettings:
        include_patterns = [
            line.strip()
            for line in self._include.toPlainText().splitlines()
            if line.strip()
        ]
        exclude_patterns = [
            line.strip()
            for line in self._exclude.toPlainText().splitlines()
            if line.strip()
        ]
        return RepoSettings(
            max_file_size=self._max_file_size.value(),
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            branch=self._branch.text().strip() or None,
            tag=self._tag.text().strip() or None,
            include_gitignored=self._include_gitignored.isChecked(),
            include_submodules=self._include_submodules.isChecked(),
        )
