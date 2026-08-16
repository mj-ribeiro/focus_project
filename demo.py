import argparse
import sys
import webbrowser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

# Adiciona a pasta src/ ao caminho de importacao do Python.
sys.path.insert(0, str(SRC_DIR))

from download_focus import download
from extract_text import extract


def main():
    """Executa o pipeline local: baixa o PDF do Focus e extrai o texto."""
    parser = argparse.ArgumentParser(
        description="Baixa o relatorio Focus mais recente e extrai o texto."
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Abre o arquivo .txt gerado no navegador padrao.",
    )
    args = parser.parse_args()

    data_dir = PROJECT_ROOT / "data"

    # Primeiro baixa o PDF mais recente disponivel na fonte do BCB.
    _, pdf_path = download(data_dir)
    size_kb = pdf_path.stat().st_size / 1024
    print(f"[1/2] Downloaded PDF: {pdf_path.name} ({size_kb:.1f} KB)")

    # Depois extrai o texto do PDF baixado e salva um .txt ao lado dele.
    txt_path = extract(pdf_path)
    print(f"[2/2] Extracted text: {txt_path}")

    # Quando solicitado, abre o .txt gerado no navegador padrao do sistema.
    if args.open:
        webbrowser.open(txt_path.resolve().as_uri())

    return 0


if __name__ == "__main__":
    sys.exit(main())
