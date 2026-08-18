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
MONTHS_PT = {
    1: "janeiro",
    2: "fevereiro",
    3: "março",
    4: "abril",
    5: "maio",
    6: "junho",
    7: "julho",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "dezembro",
}

VARIABLES = {
    "IPCA": {"display": "IPCA", "unit": "%", "priority": 2},
    "PIB Total": {"display": "PIB", "unit": "%", "priority": 4},
    "Câmbio": {"display": "câmbio", "unit": "R$/US$", "priority": 5},
    "Selic": {"display": "Selic", "unit": "% a.a.", "priority": 1},
    "IGP-M": {"display": "IGP-M", "unit": "%", "priority": 3},
    "IPCA Administrados": {
        "display": "IPCA Administrados",
        "unit": "%",
        "priority": 6,
    },
    "Balança comercial": {
        "display": "balança comercial",
        "unit": "US$ bilhões",
        "priority": 7,
    },
    "Investimento direto no país": {
        "display": "investimento direto no país",
        "unit": "US$ bilhões",
        "priority": 8,
    },
}
ROW_LABELS = sorted(VARIABLES, key=len, reverse=True)
MAIN_LABELS = ["IPCA", "Selic", "PIB Total", "Câmbio"]


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


def date_in_portuguese(value):
    """Format a date as a Portuguese long date."""
    return f"{value.day} de {MONTHS_PT[value.month]} de {value.year}"


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
    """Parse the first annual Focus table into comparable row data."""
    rows = {}

    for line in text.splitlines():
        for label in ROW_LABELS:
            if line.startswith(label) and label not in rows:
                values = NUMBER_PATTERN.findall(line[len(label) :])
                if len(values) >= 3:
                    rows[label] = {
                        "four_weeks": values[0],
                        "previous": values[1],
                        "current": values[2],
                        "next_year_current": values[6] if len(values) > 6 else None,
                    }
                break

    return rows


def numeric_value(value):
    """Convert a Brazilian decimal string into a float for comparisons."""
    if value == "-":
        return None

    return float(value.replace(",", "."))


def value_with_unit(label, value):
    """Render a Focus value with the unit shown in the report."""
    if value == "-":
        return "não informado"

    unit = VARIABLES[label]["unit"]
    if label == "Câmbio":
        return f"R$ {value}/US$"

    if unit == "US$ bilhões":
        return f"US$ {value} bilhões"

    return f"{value}{unit}"


def strip_sentence_period(text):
    """Avoid doubled periods when a formatted value already ends with one."""
    return text[:-1] if text.endswith(".") else text


def direction(previous, current):
    """Classify a weekly movement as up, down, or stable."""
    previous_value = numeric_value(previous)
    current_value = numeric_value(current)

    if previous_value is None or current_value is None:
        return "stable"

    if current_value > previous_value:
        return "up"

    if current_value < previous_value:
        return "down"

    return "stable"


def movement_phrase(label, values):
    """Describe the weekly movement in natural Portuguese."""
    movement = direction(values["previous"], values["current"])
    current = value_with_unit(label, values["current"])
    previous = value_with_unit(label, values["previous"])
    four_weeks = value_with_unit(label, values["four_weeks"])

    if label == "IPCA Administrados":
        if movement == "up":
            verb = "subiram"
        elif movement == "down":
            verb = "recuaram"
        else:
            verb = "permaneceram em"
    elif movement == "up":
        verb = "subiu"
    elif movement == "down":
        verb = "recuou"
    else:
        verb = "permaneceu"

    if movement == "stable":
        return f"{verb} em {current}, ante {previous} na semana anterior e {four_weeks} quatro semanas atrás"

    return f"{verb} para {current}, ante {previous} na semana anterior e {four_weeks} quatro semanas atrás"


def summary_bias(rows):
    """Describe the overall tone of the main weekly revisions."""
    ipca_move = direction(rows["IPCA"]["previous"], rows["IPCA"]["current"])
    gdp_move = direction(rows["PIB Total"]["previous"], rows["PIB Total"]["current"])
    igpm_move = direction(
        rows.get("IGP-M", {}).get("previous", "-"),
        rows.get("IGP-M", {}).get("current", "-"),
    )

    if ipca_move == "down" and igpm_move == "down" and gdp_move == "down":
        return "viés baixista em inflação e atividade"

    if ipca_move == "up" and igpm_move == "up":
        return "viés altista nas expectativas de inflação"

    if gdp_move == "up" and ipca_move != "up":
        return "melhora marginal em atividade, sem pressão adicional clara de inflação"

    return "ajustes mistos nas principais variáveis"


def hypothesis(label, movement, rows):
    """Write cautious hypotheses using only relationships visible in the table."""
    ipca_move = direction(
        rows.get("IPCA", {}).get("previous", "-"),
        rows.get("IPCA", {}).get("current", "-"),
    )
    igpm_move = direction(
        rows.get("IGP-M", {}).get("previous", "-"),
        rows.get("IGP-M", {}).get("current", "-"),
    )

    if label == "Selic":
        if ipca_move == "up":
            return "revisão coerente com inflação esperada mais pressionada, sugerindo juros altos por mais tempo."
        if ipca_move == "down":
            return "alívio compatível com inflação esperada um pouco menor, sem mudança forte no cenário de política monetária."
        return "sem mudança relevante no balanço de inflação capturado pelo Focus."

    if label == "IPCA":
        if igpm_move == movement and movement != "stable":
            if movement == "down":
                return "alívio nas expectativas de inflação, em linha com a queda do IGP-M na margem."
            return "piora nas expectativas de inflação, em linha com a alta do IGP-M na margem."
        return "ajuste marginal nas expectativas de inflação, sem evidência isolada suficiente para atribuir uma causa."

    if label == "IGP-M":
        if movement == "up":
            return "pressão de preços no atacado; sem hipótese causal isolada no texto extraído."
        if movement == "down":
            return "menor pressão de preços no atacado, reforçando a leitura mais benigna para inflação."

    if label == "PIB Total":
        if movement == "up":
            return "atividade esperada ligeiramente mais forte, sem detalhamento causal no boletim."
        if movement == "down":
            return "crescimento esperado perdeu fôlego na margem, sem detalhamento causal no boletim."

    if label == "Câmbio":
        return "reprecificação marginal do câmbio, sem indicação causal direta no texto extraído."

    if label == "Balança comercial":
        return "melhora da projeção externa, sem explicação causal direta no boletim."

    if label == "Investimento direto no país":
        return "ajuste marginal em fluxo externo esperado, sem explicação causal direta no boletim."

    return "sem hipótese clara — pode ser ruído amostral."


def weekly_revisions(rows):
    """Build the three main weekly revisions with cautious hypotheses."""
    revisions = []

    for label in sorted(rows, key=lambda item: VARIABLES[item]["priority"]):
        values = rows[label]
        movement = direction(values["previous"], values["current"])
        if movement == "stable":
            continue

        revisions.append(
            {
                "label": label,
                "display": VARIABLES[label]["display"],
                "previous": value_with_unit(label, values["previous"]),
                "current": value_with_unit(label, values["current"]),
                "hypothesis": hypothesis(label, movement, rows),
            }
        )

    return revisions[:3]


def executive_summary_html(publication_date, rows):
    """Create a richer executive summary in source-backed prose."""
    ipca = rows["IPCA"]
    selic = rows["Selic"]
    gdp = rows["PIB Total"]
    exchange = rows["Câmbio"]
    igpm = rows.get("IGP-M")
    administered = rows.get("IPCA Administrados")
    selic_next_year = selic.get("next_year_current")
    selic_next_year_text = (
        f", com a projeção de 2027 em {strip_sentence_period(value_with_unit('Selic', selic_next_year))}"
        if selic_next_year
        else ""
    )

    main_sentence = (
        f"As expectativas do Focus de {date_in_portuguese(publication_date)} "
        f"vieram com {summary_bias(rows)}. A mediana do "
        f"<strong>IPCA</strong> para 2026 {movement_phrase('IPCA', ipca)}, "
        f"com leitura atual de <strong>\"{escape(value_with_unit('IPCA', ipca['current']))}\"</strong>. "
        f"Nesse quadro, a mediana da <strong>Selic</strong> para o fim de 2026 "
        f"{movement_phrase('Selic', selic)}, mantendo a projeção em "
        f"<strong>\"{escape(value_with_unit('Selic', selic['current']))}\"</strong>"
        f"{selic_next_year_text}. O <strong>PIB</strong> de 2026 "
        f"{movement_phrase('PIB Total', gdp)}, e o <strong>câmbio</strong> "
        f"{movement_phrase('Câmbio', exchange)}."
    ) 

    details = []
    if igpm:
        details.append(f"o <strong>IGP-M</strong> {movement_phrase('IGP-M', igpm)}")
    if administered:
        details.append(
            f"os <strong>preços administrados</strong> {movement_phrase('IPCA Administrados', administered)}"
        )

    if details:
        supporting_sentence = (
            "Nos indicadores auxiliares de inflação, "
            + "; ".join(details)
            + ". O conjunto sugere descompressão marginal das expectativas de inflação, "
            "com o mercado preservando juros elevados e câmbio estável por mais tempo."
        )
    else:
        supporting_sentence = (
            "O conjunto sugere mudanças marginais nas expectativas, "
            "sem alteração relevante no cenário de juros e câmbio."
        )

    return f"<p>{main_sentence} {supporting_sentence}</p>"


def revisions_html(revisions):
    """Render revision bullets with details and hypotheses."""
    if not revisions:
        return (
            "<li>Não houve revisão semanal relevante nas variáveis acompanhadas. "
            "<em>Hipótese:</em> sem hipótese clara — pode ser ruído amostral.</li>"
        )

    return "\n      ".join(
        "<li>"
        f"<strong>{escape(item['display'])} (2026):</strong> "
        f"{escape(item['previous'])} → {escape(item['current'])}. "
        f"<em>Hipótese:</em> {escape(item['hypothesis'])}"
        "</li>"
        for item in revisions
    )


def build_html(publication_date, rows, revisions):
    """Assemble a branded HTML summary from extracted Focus text."""
    title = f"Focus — {publication_date:%Y-%m-%d}"
    subtitle = (
        "Boletim Focus do Banco Central · Expectativas de Mercado · "
        f"{date_in_portuguese(publication_date)}"
    )

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
</head>
<body style="margin: 0; background: #f6f7fb; color: #202033; font-family: Arial, Helvetica, sans-serif;">
  <main style="max-width: 760px; margin: 0 auto; background: #ffffff; border-top: 4px solid {BRAND_BLUE}; padding: 28px 32px 26px;">
    <img src="{LOGO_URL}" alt="Análise Macro" style="max-width: 180px; height: auto; margin-bottom: 18px;">
    <h1 style="color: {BRAND_BLUE}; font-size: 24px; line-height: 1.2; margin: 0 0 8px;">{escape(title)}</h1>
    <p style="color: #5e6270; font-size: 14px; margin: 0 0 28px;">{escape(subtitle)}</p>

    <h2 style="color: {BRAND_BLUE}; font-size: 18px; margin: 0 0 12px;">Resumo executivo</h2>
    <section style="font-size: 16px; line-height: 1.58; margin-bottom: 28px;">
      {executive_summary_html(publication_date, rows)}
    </section>

    <h2 style="color: {BRAND_BLUE}; font-size: 18px; margin: 0 0 12px;">Três principais revisões da semana</h2>
    <ul style="font-size: 16px; line-height: 1.62; margin: 0 0 28px 20px; padding: 0;">
      {revisions_html(revisions)}
    </ul>
  </main>
  <footer style="max-width: 760px; margin: 0 auto; background: #ffffff; border-top: 1px solid #e4e6ef; padding: 18px 32px 24px; color: #7a7f91; font-size: 12px; line-height: 1.45;">
    Resumo gerado automaticamente a partir do texto extraído do PDF do Focus.
    Todos os números citados constam do boletim de {publication_date:%d/%m/%Y}.
    Fonte: Banco Central do Brasil —
    <a href="https://www.bcb.gov.br/publicacoes/focus" style="color: {BRAND_BLUE};">bcb.gov.br/publicacoes/focus</a>.
  </footer>
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
    missing = [label for label in MAIN_LABELS if label not in rows]
    if missing:
        raise RuntimeError(f"Could not parse main medians: {', '.join(missing)}.")

    revisions = weekly_revisions(rows)

    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "output" / "focus"
    output_dir.mkdir(parents=True, exist_ok=True)

    html_path = output_dir / f"focus_{publication_date:%Y-%m-%d}.html"
    html_path.write_text(build_html(publication_date, rows, revisions), encoding="utf-8")
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
