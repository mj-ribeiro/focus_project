# Projeto Focus BCB

This project is a local and scheduled pipeline for the Brazilian Central Bank Focus report.

The Python scripts only do the mechanical parts:

1. Download the latest available Focus PDF from the BCB website.
2. Extract the PDF text into a UTF-8 `.txt` file.

The executive summary is written later by an agent that reads the extracted text. In the scheduled automation, that agent is responsible for generating the summary and sending it by email. The scripts must not invent numbers; they only download and extract the source material.

## Source

- Focus page: https://www.bcb.gov.br/publicacoes/focus
- PDF pattern used by the downloader: `https://www.bcb.gov.br/content/focus/focus/RAAAAMMDD.pdf`

If Monday is a holiday, BCB may publish the Focus report on Tuesday. The downloader starts from the most recent Monday strictly before the current date and checks up to 7 prior dates.

## Folder Tree

```text
.
|-- .github/
|   `-- workflows/
|       `-- focus-download.yml
|-- data/
|-- output/
|   `-- focus/
|       `-- .gitkeep
|-- src/
|   |-- baixar_focus.py
|   |-- download_focus.py
|   |-- extract_text.py
|   `-- extrair_texto.py
|-- tests/
|   `-- test_baixar_focus.py
|-- CODEX.md
|-- README.md
|-- demo.py
|-- pytest.ini
`-- requirements.txt
```

## Run Locally

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the full local pipeline:

```bash
python demo.py
```

Open the generated text file after extraction:

```bash
python demo.py --open
```

On Windows, if `python` points to an interpreter without pip or the installed packages, use:

```bash
py -m pip install -r requirements.txt
py demo.py --open
```

## Run Individual Steps

Download the Focus PDF:

```bash
python src/baixar_focus.py
```

Extract text from the latest PDF in `data/`:

```bash
python src/extrair_texto.py
```

Extract text from a specific PDF:

```bash
python src/extrair_texto.py --pdf data/focus_aaaa-mm-dd.pdf
```

## Run Tests

Run the offline tests:

```bash
python -m pytest -m "not network"
```

Run the network test explicitly:

```bash
python -m pytest -m network
```

Run the whole suite:

```bash
python -m pytest
```

## Scheduled Automation

The GitHub Actions workflow runs every Monday at 12:15 PM UTC, which is 9:15 AM BRT, and can also be started manually with `workflow_dispatch`.

The workflow downloads the latest Focus PDF, extracts the text, and commits matching `data/focus_*.pdf` and `data/focus_*.txt` files back to the repository.

Future automation should use the extracted `.txt` file as the input for the summary-writing agent, save Markdown summaries in `output/focus/`, and send the executive summary by email.
