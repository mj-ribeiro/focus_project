from datetime import date, timedelta
from pathlib import Path

import requests


FOCUS_URL_TEMPLATE = "https://www.bcb.gov.br/content/focus/focus/R{date:%Y%m%d}.pdf"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/127.0.0.0 Safari/537.36"
)
MAX_ATTEMPTS = 7


def last_monday(today):
    """Return the most recent Monday strictly before the given date."""
    days_since_monday = today.weekday()
    days_to_subtract = days_since_monday if days_since_monday > 0 else 7
    return today - timedelta(days=days_to_subtract)


def download(dest):
    """Download the latest available Focus PDF and return its date and path."""
    destination = Path(dest)
    destination.mkdir(parents=True, exist_ok=True)

    publication_date = last_monday(date.today())
    headers = {"User-Agent": USER_AGENT}

    for offset in range(MAX_ATTEMPTS):
        candidate_date = publication_date - timedelta(days=offset)
        url = FOCUS_URL_TEMPLATE.format(date=candidate_date)

        response = requests.get(url, headers=headers, timeout=30)
        content = response.content

        # Accept the response only when the server returns an actual PDF file.
        if response.ok and content.startswith(b"%PDF"):
            file_path = destination / f"focus_{candidate_date:%Y-%m-%d}.pdf"
            file_path.write_bytes(content)
            return candidate_date, file_path

    raise RuntimeError(
        f"Could not download a valid Focus PDF after {MAX_ATTEMPTS} attempts."
    )


def main():
    """Download the Focus PDF to data/ and print the saved path and size."""
    project_root = Path(__file__).resolve().parents[1]
    publication_date, file_path = download(project_root / "data")
    size_kb = file_path.stat().st_size / 1024

    print(f"Downloaded Focus report dated {publication_date:%Y-%m-%d}")
    print(f"Path: {file_path}")
    print(f"Size: {size_kb:.1f} KB")


if __name__ == "__main__":
    main()
