"""qdom の宣言的 UI 記述ノード。build() に渡すことで PySide6 ウィジェットに変換される。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Node:
    """UI 要素の宣言的記述。PySide6 には依存しない純粋なデータクラス。"""

    kind: str
    props: dict[str, Any] = field(default_factory=dict)
    children: list[Node] = field(default_factory=list)

    def with_id(self, widget_id: str) -> Node:
        self.props["id"] = widget_id
        return self
