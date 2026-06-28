"""NotebookLM 出力の分割設定。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class SplitSettings:
    enabled: bool = False
    metric: Literal["chars", "tokens", "bytes"] = "chars"
    threshold: int = 500_000         # NotebookLM の1ソースあたり文字数上限
    max_sources: int = 50            # NotebookLM の1ノートあたりソース数上限
    overflow: Literal["warn", "merge", "trim_tail", "trim_even"] = "warn"
    # overflow 戦略（ファイル数 or 文字数が制限を超えた場合）:
    #   "warn"      : 警告のみ、全ファイルをそのまま出力（データ損失なし）
    #   "merge"     : max_sources に収まるよう統合（1ファイルが threshold を超える可能性あり）
    #   "trim_tail" : max_sources に統合した上で末尾コンテンツを切り捨てて threshold を守る
    #   "trim_even" : max_sources に統合した上で均等サンプリングして threshold を守る
