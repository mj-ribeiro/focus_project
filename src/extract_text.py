import argparse
import sys
from pathlib import Path

import pdfplumber


def extract(pdf_path):
    """Extract all text from a Focus PDF and save it beside the PDF as UTF-8 text."""
    pdf_file = Path(pdf_path)
    txt_file = pdf_file.with_suffix(".txt")

    with pdfplumber.open(pdf_file) as pdf:
        page_texts = []

        for page in pdf.pages:
            # Some PDF pages can return None when no extractable text is found.
            page_texts.append(page.extract_text() or "")

    txt_file.write_text("\n\n".join(page_texts), encoding="utf-8")
    return txt_file


def _latest_focus_pdf(data_dir):
    """Return the most recent Focus PDF from data/, based on the filename date."""
    pdfs = sorted(data_dir.glob("focus_*.pdf"))
    return pdfs[-1] if pdfs else None


def main():
    """Run the command-line interface for Focus PDF text extraction."""
    parser = argparse.ArgumentParser(
        description="Extract text from a Focus PDF and save it as a .txt file."
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        help="Path to a specific Focus PDF. Defaults to the latest PDF in data/.",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"

    pdf_path = args.pdf
    if pdf_path is None:
        pdf_path = _latest_focus_pdf(data_dir)
        if pdf_path is None:
            print(
                "No Focus PDFs found in data/. Run src/download_focus.py first.",
                file=sys.stderr,
            )
            return 1

    if not pdf_path.exists():
        print(f"PDF file not found: {pdf_path}", file=sys.stderr)
        return 1

    txt_path = extract(pdf_path)
    print(f"Text extracted to: {txt_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
