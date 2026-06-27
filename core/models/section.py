"""KnowledgeDocument を構成するセクション（ページ・見出し単位）。"""

from dataclasses import dataclass, field


@dataclass
class KnowledgeSection:
    """見出しまたはページ単位のテキストブロック。

    RAG チャンクや NotebookLM ソースの最小単位になる。
    links / assets はメタデータとして保持し、Writer が出力形式に合わせて整形する。
    """

    id: str           # "{doc_id}_s{連番}" 形式
    title: str        # 見出しテキスト
    text: str         # 本文（Markdown または プレーンテキスト）

    level: int = 1    # 見出しレベル（h1=1, h2=2 ...）
    order: int = 0    # ドキュメント内の出現順

    source_ref: str | None = None           # 元ファイルパス（リンク解決用）
    section_path: list[str] = field(default_factory=list)  # 目次上の階層（例: ["基本操作", "通信設定"]）

    links: list[str] = field(default_factory=list)    # 本文中のリンク先URL
    assets: list[str] = field(default_factory=list)   # 本文中の画像パス
    keywords: list[str] = field(default_factory=list) # EnrichMetadataTransformer が付与するキーワード

    metadata: dict[str, str] = field(default_factory=dict)
