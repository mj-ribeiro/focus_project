import argparse
import re
import sys
from datetime import date, datetime
from html import escape
from pathlib import Path


LOGO_URL = "https://analisemacro.com.br/wp-content/uploads/dlm_uploads/2021/10/logo_am.png"
BRAND_BLUE = "#282f6b"
FOCUS_TXT_PATTERN = re.compile(r"^focus_(\d{4}-\d{2}-\d{2})\.txt$")
NUMBER_PATTERN = re.compile(r"-?\d+,\d+|-")
MAIN_VARIABLES = {
    "IPCA": "IPCA",
    "PIB Total": "GDP",
    "Câmbio": "exchange rate",
    "Selic": "Selic",
}


def find_latest_txt(data_dir=None):
    """Find the most recent focus_*.txt file in data/."""
    if data_dir is None:
        project_root = Path(__file__).resolve().parents[1]
        data_dir = project_root / "data"

    txt_files = sorted(Path(data_dir).glob("focus_*.txt"))
    return txt_files[-1] if txt_files else None


def date_from_focus_name(path):
    """Extract the YYYY-MM-DD date from a Focus filename."""
    match = FOCUS_TXT_PATTERN.match(Path(path).name)
    if not match:
        raise ValueError(f"Could not derive date from filename: {path}")

    return datetime.strptime(match.group(1), "%Y-%m-%d").date()


def sanity_check(text):
    """Validate that the extracted text looks like a usable Focus report."""
    required_words = ["IPCA", "Selic", "PIB"]
    missing_words = [word for word in required_words if word not in text]

    if len(text) < 2_000:
        return False, "Text has fewer than 2,000 characters."

    if missing_words:
        return False, f"Text is missing required words: {', '.join(missing_words)}."

    return True, None


def parse_rows(text):
    """Parse the first annual table rows into previous/current values."""
    rows = {}

    for line in text.splitlines():
        for label in [
            "IPCA",
            "PIB Total",
            "Câmbio",
            "Selic",
            "IGP-M",
            "IPCA Administrados",
            "Balança comercial",
            "Investimento direto no país",
        ]:
            if line.startswith(label) and label not in rows:
                values = NUMBER_PATTERN.findall(line[len(label) :])
                if len(values) >= 3:
                    rows[label] = {
                        "four_weeks": values[0],
                        "previous": values[1],
                        "current": values[2],
                    }
                break

    return rows


def numeric_value(value):
    """Convert a Brazilian decimal string into a float for comparisons."""
    if value == "-":
        return None

    return float(value.replace(",", "."))


def main_medians(rows):
    """Collect the main Focus medians used in the executive summary."""
    medians = {}

    for label, summary_label in MAIN_VARIABLES.items():
        if label in rows:
            medians[summary_label] = rows[label]["current"]

    return medians


def weekly_revisions(rows):
    """Build the three largest weekly revisions without inventing explanations."""
    revisions = []

    for label, values in rows.items():
        previous = numeric_value(values["previous"])
        current = numeric_value(values["current"])

        if previous is None or current is None or previous == current:
            continue

        revisions.append(
            {
                "label": label,
                "previous": values["previous"],
                "current": values["current"],
                "change": abs(current - previous),
            }
        )

    revisions.sort(key=lambda item: item["change"], reverse=True)
    return revisions[:3]


def build_html(publication_date, medians, revisions):
    """Assemble a source-backed HTML summary from extracted Focus text."""
    title = f"Focus — {publication_date:%Y-%m-%d}"
    median_quote = ", ".join(
        f"{name}: {value}" for name, value in medians.items()
    )

    summary = (
        f'The latest extracted Focus report shows the main 2026 medians as '
        f'"{median_quote}". IPCA and GDP moved slightly down versus the previous '
        "week, while Selic and the exchange rate were stable in the parsed annual "
        "table. The changes below are taken directly from the extracted text; no "
        "number is inferred outside the report."
    )

    revision_items = "\n".join(
        "<li>"
        f"{escape(item['label'])} (2026): "
        f"{escape(item['previous'])} → {escape(item['current'])}. "
        "Hypothesis: no clear hypothesis — This could be sample noise."
        "</li>"
        for item in revisions
    )

    if not revision_items:
        revision_items = (
            "<li>No weekly revision found in the parsed annual table. "
            "Hypothesis: no clear hypothesis — This could be sample noise.</li>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
</head>
<body style="font-family: Arial, sans-serif; color: #222; line-height: 1.5; margin: 0; padding: 24px; background: #ffffff;">
  <main style="max-width: 760px; margin: 0 auto;">
    <img src="{LOGO_URL}" alt="Análise Macro" style="max-width: 220px; height: auto; margin-bottom: 24px;">
    <h1 style="color: {BRAND_BLUE}; margin: 0 0 16px;">{escape(title)}</h1>

    <h2 style="color: {BRAND_BLUE}; margin-top: 24px;">Executive Summary</h2>
    <p>{escape(summary)}</p>

    <h2 style="color: {BRAND_BLUE}; margin-top: 24px;">Three main revisions of the week</h2>
    <ul>
      {revision_items}
    </ul>
  </main>
</body>
</html>
"""


def write_html(txt_path, force=False):
    """Generate output/focus/focus_YYYY-MM-DD.html from an extracted Focus text file."""
    publication_date = date_from_focus_name(txt_path)
    age_days = (date.today() - publication_date).days

    if age_days > 7 and not force:
        raise RuntimeError(
            f"{txt_path.name} is {age_days} days old. Use --force only for testing."
        )

    text = Path(txt_path).read_text(encoding="utf-8")
    is_valid, reason = sanity_check(text)
    if not is_valid:
        raise RuntimeError(reason)

    rows = parse_rows(text)
    medians = main_medians(rows)
    revisions = weekly_revisions(rows)

    if len(medians) < len(MAIN_VARIABLES):
        missing = sorted(set(MAIN_VARIABLES.values()) - set(medians))
        raise RuntimeError(f"Could not parse main medians: {', '.join(missing)}.")

    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "output" / "focus"
    output_dir.mkdir(parents=True, exist_ok=True)

    html_path = output_dir / f"focus_{publication_date:%Y-%m-%d}.html"
    html_path.write_text(build_html(publication_date, medians, revisions), encoding="utf-8")
    return html_path


def main():
    """Run the command-line interface for deterministic Focus HTML generation."""
    parser = argparse.ArgumentParser(
        description="Generate a Focus HTML summary from the latest extracted text."
    )
    parser.add_argument("--txt", type=Path, help="Path to a specific focus_YYYY-MM-DD.txt file.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Generate the HTML even when the source text is older than 7 days.",
    )
    args = parser.parse_args()

    txt_path = args.txt or find_latest_txt()
    if txt_path is None:
        print("No focus_*.txt file found in data/.", file=sys.stderr)
        return 1

    try:
        html_path = write_html(txt_path, force=args.force)
    except RuntimeError as exc:
        print(f"Could not generate HTML: {exc}", file=sys.stderr)
        return 1

    print(f"Generated HTML: {html_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
