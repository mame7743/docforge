from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Node:
    """Declarative description of a UI element before it is realized."""

    kind: str
    props: dict[str, Any] = field(default_factory=dict)
    children: list["Node"] = field(default_factory=list)

    def with_id(self, widget_id: str) -> "Node":
        self.props["id"] = widget_id
        return self
