from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


class UIContext:
    """Widget registry — lookup widgets built by qdom factory functions by id."""

    def __init__(self):
        self._widgets: dict[str, QWidget] = {}

    def register(self, widget_id: str, widget: "QWidget") -> None:
        self._widgets[widget_id] = widget

    def __getitem__(self, widget_id: str) -> "QWidget":
        return self._widgets[widget_id]

    def get(self, widget_id: str) -> "QWidget | None":
        return self._widgets.get(widget_id)

    def __contains__(self, widget_id: str) -> bool:
        return widget_id in self._widgets
