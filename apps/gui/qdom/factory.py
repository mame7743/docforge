"""
qdom factory — build PySide6 widget trees declaratively.

Each helper returns a (QWidget, UIContext) or contributes into the caller's
context. The top-level build() call is the entry point.

Usage:
    ctx = UIContext()
    root_widget = build(ctx, vbox(...))
    ctx["progress"].setValue(50)
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
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
# Node constructors
# ---------------------------------------------------------------------------

def vbox(*children, **props) -> Node:
    return Node("vbox", props, list(children))


def hbox(*children, **props) -> Node:
    return Node("hbox", props, list(children))


def group(title: str, *children, **props) -> Node:
    return Node("group", {"title": title, **props}, list(children))


def spacer(**props) -> Node:
    return Node("spacer", props)


def label(text: str, **props) -> Node:
    return Node("label", {"text": text, **props})


def button(text: str, **props) -> Node:
    return Node("button", {"text": text, **props})


def line_edit(**props) -> Node:
    return Node("line_edit", props)


def checkbox(text: str, **props) -> Node:
    return Node("checkbox", {"text": text, **props})


def text_edit(**props) -> Node:
    return Node("text_edit", props)


def progress_bar(**props) -> Node:
    return Node("progress_bar", props)


def spin_box(**props) -> Node:
    return Node("spin_box", props)


def file_list(**props) -> Node:
    return Node("file_list", props)


# ---------------------------------------------------------------------------
# Realizer — turns Node tree into PySide6 widgets
# ---------------------------------------------------------------------------

def build(ctx: UIContext, node: Node) -> QWidget:
    """Realize a Node tree into PySide6 widgets, registering ids in ctx."""
    widget = _realize(ctx, node)
    return widget


def _realize(ctx: UIContext, node: Node) -> QWidget:
    kind = node.kind
    props = node.props

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
        widget = QPushButton(props.get("text", ""))
        if "classes" in props and "primary" in props["classes"]:
            widget.setDefault(True)
    elif kind == "line_edit":
        widget = QLineEdit()
        if "placeholder" in props:
            widget.setPlaceholderText(props["placeholder"])
    elif kind == "checkbox":
        widget = QCheckBox(props.get("text", ""))
        widget.setChecked(bool(props.get("checked", False)))
    elif kind == "text_edit":
        widget = QTextEdit()
        if props.get("readonly"):
            widget.setReadOnly(True)
    elif kind == "progress_bar":
        widget = QProgressBar()
        widget.setValue(0)
        widget.setRange(0, 100)
    elif kind == "spin_box":
        widget = QSpinBox()
        widget.setMinimum(props.get("minimum", 0))
        widget.setMaximum(props.get("maximum", 999_999_999))
        widget.setValue(props.get("value", 0))
        if "step" in props:
            widget.setSingleStep(props["step"])
    elif kind == "file_list":
        widget = QListWidget()
    else:
        widget = QWidget()

    widget_id = props.get("id")
    if widget_id:
        ctx.register(widget_id, widget)

    return widget


def _layout_widget(ctx: UIContext, node: Node, layout_cls) -> QWidget:
    container = QWidget()
    layout = layout_cls(container)
    layout.setContentsMargins(0, 0, 0, 0)

    for child in node.children:
        child_widget = _realize(ctx, child)
        stretch = child.props.get("stretch", 0)
        layout.addWidget(child_widget, stretch)

    return container


def _group(ctx: UIContext, node: Node) -> QGroupBox:
    box = QGroupBox(node.props.get("title", ""))
    layout = QVBoxLayout(box)

    for child in node.children:
        child_widget = _realize(ctx, child)
        stretch = child.props.get("stretch", 0)
        layout.addWidget(child_widget, stretch)

    return box


def _spacer_widget() -> QWidget:
    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    return spacer
