# DocForge

**DocForge converts documents into LLM-ready Markdown knowledge bases.**

CHM / HTML / Markdown / テキストなどの雑多なドキュメントを、NotebookLM・RAG・LLM が扱いやすい Markdown ナレッジベースへ変換します。

---

## 特徴

- **本文抽出** — ナビゲーションやフッターなどのノイズを除去して本文だけを取り出す
- **メタ情報保持** — 元ファイル名・目次上の位置・リンク先をメタデータとして残す
- **NotebookLM 向け分割** — ページ境界を維持しつつ指定文字数で複数 Markdown に分割
- **RAG 向け JSONL** — セクション単位のチャンクを JSONL で出力
- **変換レポート** — 変換結果・警告をまとめた `docforge_report.md` を生成
- **GUI / CLI 両対応** — PySide6 GUI と Click ベースの CLI を同じ変換パイプラインで動かす

---

## 対応フォーマット

| 形式 | 拡張子 |
|------|--------|
| プレーンテキスト | `.txt` `.log` |
| Markdown | `.md` |
| HTML | `.html` `.htm` |
| CHM | `.chm` ※ Windows のみ |
| Office / PDF | `.docx` `.xlsx` `.pptx` `.pdf` ※ オプション |

---

## インストール

```bash
git clone https://github.com/yourname/docforge.git
cd docforge

# CLI のみ
pip install -e .

# GUI も使う場合
pip install -e ".[gui]"

# Office / PDF 対応を追加する場合
pip install -e ".[markitdown]"
```

---

## CLI の使い方

```bash
# 基本: 複数ファイルをまとめて変換
docforge build manual.chm spec.md notes.txt -o out

# JSONL も出力する
docforge build input.html -o out --jsonl

# NotebookLM 分割を無効にする
docforge build input.md -o out --no-notebooklm

# 分割サイズを変更する（デフォルト: 100,000文字）
docforge build input.html -o out --split-size 50000

# ファイルの内容を確認する（変換せずに）
docforge inspect document.chm

# 登録済み Importer 一覧
docforge plugins
```

### 出力ファイル

```
out/
├── knowledge_base.md        # 全ドキュメントをまとめた Markdown
├── notebooklm/
│   ├── source_001.md        # NotebookLM 向け分割ファイル
│   └── source_002.md
├── chunks.jsonl             # RAG 向けチャンク（--jsonl 指定時）
└── docforge_report.md       # 変換レポート
```

---

## GUI の使い方

```bash
python -m apps.gui.app
```

ファイルをドラッグ＆ドロップして出力先を選び、「変換開始」を押すだけです。

---

## アーキテクチャ

変換はパイプラインで行います。

```
入力ファイル
  └─ Importer（形式ごとの読み込み）
       └─ KnowledgeDocument / KnowledgeSection（中間モデル）
            └─ Transformer（ノイズ除去・正規化・メタ情報付与）
                 └─ Writer（Markdown / JSONL / レポート出力）
```

`core/` は PySide6 に依存しないため、CLI・GUI・テストで同じパイプラインを共有できます。

---

## テスト

```bash
pip install -e ".[dev]"
pytest
```

---

## ライセンス

MIT
