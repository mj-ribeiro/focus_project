You are running the Focus Weekly Summary Routine.

The PDF download and text extraction were already done by a GitHub Action earlier (Monday 9:15 AM BRT). The files `data/focus_YYYY-MM-DD.{pdf,txt}` are already committed to `main` when the Routine starts. Your task is to read the most recent `.txt`, generate an HTML summary with the Macro Analysis logo, and send it by email.

## Steps

1. **Locate the most recent `.txt`.** List `data/focus_*.txt` and take the one with the latest date. If there isn't one, stop without sending an email — the Action did not run.

2. **Check freshness.** Extract the date from the name and compare it to today:

- 0 to 3 days: it's fresh, Follow.

- 4 to 7 days: follow, but write `[REVIEW]` at the beginning of the subject.

- More than 7 days: stop without sending an email.

3. **Text Sanity Check.** Confirm: at least 2,000 characters and
presence of the words `IPCA`, `Selic`, `PIB`. If it fails, the PDF layout may have changed — stop without sending an email.

4. **Read the text** and write the summary content:

- **Executive Summary** in up to 200 words, in flowing prose.

Start with the medians of the main variables (year-to-date IPCA,

year-end Selic, GDP, exchange rate). Quote verbatim in quotation marks
when there is a key number.

- **Three main revisions of the week** in bullet points in the format:

`Variable (year): previous → current. Hypothesis: reason.`

- Never invent a number. If there is no solid hypothesis, write
"no clear hypothesis — This could be sample noise.

5. **Assemble the HTML** of the email in `output/focus/focus_YYYY-MM-DD.html`, with this structure:

- At the top, the Análise Macro logo, loaded from this URL:

`https://analisemacro.com.br/wp-content/uploads/dlm_uploads/2021/10/logo_am.png`

- A title `Focus — YYYY-MM-DD`.

- The executive summary in paragraphs and the three revisions in a list.

- Use the brand colors: blue `#282f6b` in the titles.

6. **Inspect** the generated HTML: the logo appears, the medians match the `.txt` file, there is at least one direct quote in quotation marks.

7. **Send the email** through the authorized email connector:

- Subject: `Focus Summary — YYYY-MM-DD`

- Body: the HTML assembled in step 5.

- Recipient: `you@example.com` (replace with who should receive the summary; for more than one, separate with a comma:

`fulano@example.com, ciclano@example.com`).

## Errors

In any of the scenarios below, stop without sending the email. The reason appears in the Routine transcript.

- No `.txt` file in `date/` (Action did not run).

- `.txt` file older than 7 days (Broken Action).

- Text sanity check failed (PDF layout change).

Never invent a number.
