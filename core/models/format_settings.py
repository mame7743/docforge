"""フォーマット別変換設定。拡張子ごとにパイプラインの動作を上書きできる。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FormatSettings:
    """拡張子単位の変換設定。None のフィールドは ConvertSettings のグローバル値を継承する。"""

    encoding: str | None = None
    extra_noise_patterns: list[str] = field(default_factory=list)
    enabled_transformers: list[str] | None = None  # None=全て使用, []=なし
    split_size_chars: int | None = None            # None=グローバル値を使用
