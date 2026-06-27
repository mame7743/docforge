"""変換パイプライン全体の設定値。CLI・GUI どちらから呼ばれても同じ構造を使う。"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ConvertSettings:
    input_paths: list[Path]  # 変換対象ファイルのリスト
    out_dir: Path            # 出力ディレクトリ

    # --- 出力形式の選択 ---
    export_markdown: bool = True       # knowledge_base.md
    export_notebooklm: bool = True     # notebooklm/source_NNN.md
    export_jsonl: bool = False         # chunks.jsonl（RAG用）
    export_report: bool = True         # docforge_report.md

    copy_assets: bool = True           # 画像などをアセットとして出力先へコピーする
    split_size_chars: int = 100_000    # NotebookLM 分割の目安文字数（デフォルト10万字）

    encoding_hint: str | None = None   # 入力ファイルのエンコーディング強制指定（例: "cp932"）

    # 空リストのときはすべての登録済み Importer / Transformer を使用する
    enabled_importers: list[str] = field(default_factory=list)
    enabled_transformers: list[str] = field(default_factory=list)
