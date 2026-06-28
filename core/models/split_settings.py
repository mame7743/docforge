"""NotebookLM 出力の分割設定。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class SplitSettings:
    enabled: bool = False                              # デフォルト: 分割なし（1ファイルに統合）
    metric: Literal["chars", "tokens", "bytes"] = "chars"
    threshold: int = 100_000
