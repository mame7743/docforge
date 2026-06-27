"""変換パイプラインを流れる中間データモデル。

入力ファイルの形式に関係なく、Importer はすべての内容を
KnowledgeDocument に変換する。Transformer・Writer はこのモデルだけを扱う。
"""

from dataclasses import dataclass, field
from pathlib import Path

from .section import KnowledgeSection
from .asset import KnowledgeAsset


@dataclass
class KnowledgeDocument:
    """1つの入力ファイルに対応するドキュメント全体。"""

    id: str                          # ファイル名から生成する英数字ID
    title: str                       # ドキュメントのタイトル
    source_path: Path | None         # 元ファイルのパス（テスト時は None の場合あり）
    source_type: str                 # "text" / "markdown" / "html" / "chm" など

    sections: list[KnowledgeSection] = field(default_factory=list)
    assets: list[KnowledgeAsset] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)  # このドキュメント固有の警告
