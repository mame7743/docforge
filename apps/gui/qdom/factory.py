"""qdom ファクトリ — Node ツリーを PySide6 ウィジェットに変換する。

使い方:
    ctx = UIContext()
    root = build(ctx, vbox(
        button("クリック", id="btn"),
        progress_bar(id="progress"),
    ))
    ctx["btn"].clicked.connect(handler)
    ctx["progress"].setValue(50)

仮想 DOM・差分更新・双方向バインディングは持たない。
あくまでウィジェットツリーを宣言的に書くための薄いラッパー。
"""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .context import UIContext
from .node import Node


# ---------------------------------------------------------------------------
# Node コンストラクタ — 宣言的な記述用のヘルパー関数
# ---------------------------------------------------------------------------

def vbox(*children: Node, **props: Any) -> Node:
    return Node("vbox", props, list(children))


def hbox(*children: Node, **props: Any) -> Node:
    return Node("hbox", props, list(children))


def group(title: str, *children: Node, **props: Any) -> Node:
    """QGroupBox を作る。タイトルは枠線に表示される。"""
    return Node("group", {"title": title, **props}, list(children))


def spacer(**props: Any) -> Node:
    """水平方向に伸縮するスペーサー（hbox 内のボタン右寄せなどに使う）。"""
    return Node("spacer", props)


def label(text: str, **props: Any) -> Node:
    return Node("label", {"text": text, **props})


def button(text: str, **props: Any) -> Node:
    """classes=["primary"] を指定するとデフォルトボタンになる。"""
    return Node("button", {"text": text, **props})


def line_edit(**props: Any) -> Node:
    return Node("line_edit", props)


def checkbox(text: str, **props: Any) -> Node:
    """checked=True で初期チェック状態にする。"""
    return Node("checkbox", {"text": text, **props})


def text_edit(**props: Any) -> Node:
    """readonly=True でログ表示などの読み取り専用テキスト欄にする。"""
    return Node("text_edit", props)


def progress_bar(**props: Any) -> Node:
    return Node("progress_bar", props)


def spin_box(**props: Any) -> Node:
    """value / minimum / maximum / step を props で指定できる。"""
    return Node("spin_box", props)


def file_list(**props: Any) -> Node:
    """入力ファイルの一覧表示に使う QListWidget。"""
    return Node("file_list", props)


def combo_box(*items: str, **props: Any) -> Node:
    """選択肢を持つドロップダウン。items で選択肢を指定し current で初期選択インデックスを指定する。"""
    return Node("combo_box", {"items": list(items), **props})


# ---------------------------------------------------------------------------
# Realizer — Node ツリーを実際の PySide6 ウィジェットに変換する
# ---------------------------------------------------------------------------

def build(ctx: UIContext, node: Node) -> QWidget:
    """Node ツリーを PySide6 ウィジェットとして構築し、id を ctx に登録する。"""
    return _realize(ctx, node)


def _realize(ctx: UIContext, node: Node) -> QWidget:
    kind = node.kind
    props = node.props

    widget: QWidget

    if kind == "vbox":
        widget = _layout_widget(ctx, node, QVBoxLayout)
    elif kind == "hbox":
        widget = _layout_widget(ctx, node, QHBoxLayout)
    elif kind == "group":
        widget = _group(ctx, node)
    elif kind == "spacer":
        widget = _spacer_widget()
    elif kind == "label":
        widget = QLabel(props.get("text", ""))
    elif kind == "button":
        w = QPushButton(props.get("text", ""))
        if "classes" in props and "primary" in props["classes"]:
            w.setDefault(True)
        widget = w
    elif kind == "line_edit":
        w = QLineEdit()
        if "placeholder" in props:
            w.setPlaceholderText(props["placeholder"])
        widget = w
    elif kind == "checkbox":
        w = QCheckBox(props.get("text", ""))
        w.setChecked(bool(props.get("checked", False)))
        widget = w
    elif kind == "text_edit":
        w = QTextEdit()
        if props.get("readonly"):
            w.setReadOnly(True)
        widget = w
    elif kind == "progress_bar":
        w = QProgressBar()
        w.setValue(0)
        w.setRange(0, 100)
        widget = w
    elif kind == "spin_box":
        w = QSpinBox()
        w.setMinimum(props.get("minimum", 0))
        w.setMaximum(props.get("maximum", 999_999_999))
        w.setValue(props.get("value", 0))
        if "step" in props:
            w.setSingleStep(props["step"])
        widget = w
    elif kind == "file_list":
        widget = QListWidget()
    elif kind == "combo_box":
        w = QComboBox()
        for item in props.get("items", []):
            w.addItem(item)
        if "current" in props:
            w.setCurrentIndex(props["current"])
        widget = w
    else:
        widget = QWidget()

    # id が指定されていれば UIContext に登録する
    widget_id: str | None = props.get("id")
    if widget_id:
        ctx.register(widget_id, widget)

    return widget


def _layout_widget(ctx: UIContext, node: Node, layout_cls: type) -> QWidget:
    """vbox / hbox 共通の実装。stretch プロパティで引き伸ばし比率を指定する。"""
    container = QWidget()
    layout = layout_cls(container)
    layout.setContentsMargins(0, 0, 0, 0)

    for child in node.children:
        child_widget = _realize(ctx, child)
        stretch: int = child.props.get("stretch", 0)
        layout.addWidget(child_widget, stretch)

    return container


def _group(ctx: UIContext, node: Node) -> QGroupBox:
    box = QGroupBox(node.props.get("title", ""))
    layout = QVBoxLayout(box)

    for child in node.children:
        child_widget = _realize(ctx, child)
        stretch: int = child.props.get("stretch", 0)
        layout.addWidget(child_widget, stretch)

    return box


def _spacer_widget() -> QWidget:
    """Expanding ポリシーにより hbox 内で残りスペースを埋める。"""
    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    return spacer
