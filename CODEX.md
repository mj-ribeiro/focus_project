# Project Brief

## Objective

Download the Focus report from the Brazilian Central Bank every Monday, extract the text, and prepare an executive summary.

## Source

- Report page: https://www.bcb.gov.br/publicacoes/focus
- PDF pattern: https://www.bcb.gov.br/content/focus/focus/(AAAAMM).pdf

## Conventions

1. Files must be named as `focus_aaaa_mm_dd`, using the report release date.
2. `data/` stores downloaded PDFs and extracted text files.
3. `output/focus/` stores summaries in Markdown.

## Rules

1. Never make up numbers.
2. If Monday is a holiday, the Brazilian Central Bank publishes the Focus report on Tuesday.
