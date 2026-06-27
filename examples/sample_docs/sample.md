# DocForge Overview

DocForge converts documents into LLM-ready Markdown knowledge bases.

## Architecture

The pipeline consists of three main stages:

1. **Importers** read source files into a common `KnowledgeDocument` model
2. **Transformers** clean, normalize, and enrich the intermediate representation
3. **Writers** produce Markdown, NotebookLM splits, JSONL, and reports

## Supported Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| Plain text | .txt, .log | Paragraph-based splitting |
| Markdown | .md | Heading-based sections |
| HTML | .html, .htm | BeautifulSoup extraction |
| CHM | .chm | Windows hh.exe decompile |

## Usage

```bash
docforge build manual.chm spec.md notes.txt -o out
docforge build input.html -o out --jsonl
docforge inspect document.chm
```
