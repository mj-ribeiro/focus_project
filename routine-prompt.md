You are running the Focus Weekly Summary Routine.

The PDF download and text extraction were already done by a GitHub Action earlier. The files `data/focus_YYYY-MM-DD.{pdf,txt}` are committed to `main` when the Routine starts. Your task is to read the most recent `.txt`, generate a detailed HTML summary with the Análise Macro logo, and send it by email.

## Steps

1. **Locate the most recent `.txt`.** List `data/focus_*.txt` and take the one with the latest date. If there is no file, stop without sending an email because the Action did not run.

2. **Check freshness.** Extract the date from the filename and compare it to today:

- 0 to 3 days: it is fresh; proceed.
- 4 to 7 days: proceed, but write `[REVIEW]` at the beginning of the subject.
- More than 7 days: stop without sending an email.

3. **Text sanity check.** Confirm at least 2,000 characters and the presence of the words `IPCA`, `Selic`, and `PIB`. If it fails, stop without sending an email because the PDF layout may have changed.

4. **Read the text and write the summary in Portuguese.**

- Write a section titled `Resumo executivo`.
- Use one or two detailed paragraphs, similar to a professional macro note.
- Start with the main 2026 medians: IPCA, Selic, PIB, and câmbio.
- Mention the current value, the previous-week value, and, when useful, the four-weeks-ago value.
- Add relevant supporting variables such as IGP-M, IPCA Administrados, balança comercial, or investimento direto no país when they help explain the week.
- Quote at least one key number verbatim in quotation marks.
- Never invent a number. Every number must appear in the extracted `.txt`.

5. **Write the section `Três principais revisões da semana`.**

- Use three bullet points.
- Each bullet must follow this structure:

`Variable (year): previous → current. Hipótese: reason.`

- Add more detail than a generic note. Connect revisions when the text supports it, for example IPCA with IGP-M or Selic with inflation expectations.
- If there is no solid hypothesis, write: `sem hipótese clara — pode ser ruído amostral.`
- Never invent a number or causal story.

6. **Assemble the HTML** in `output/focus/focus_YYYY-MM-DD.html`, using this structure:

- At the top, the Análise Macro logo from:

`https://analisemacro.com.br/wp-content/uploads/dlm_uploads/2021/10/logo_am.png`

- A title: `Focus — YYYY-MM-DD`.
- A subtitle with the source and publication date.
- The `Resumo executivo` section in paragraphs.
- The `Três principais revisões da semana` section in bullets.
- A footer explaining that the summary was generated from the extracted Focus PDF text.
- Use the brand blue `#282f6b` in titles and a clean email-friendly layout.

7. **Inspect** the generated HTML before sending:

- The logo appears.
- The medians match the `.txt` file.
- There is at least one direct quote in quotation marks.
- The revisions include previous and current values.
- The hypotheses are cautious and do not invent facts.

8. **Send the email** through the authorized email connector:

- Subject: `Focus Summary — YYYY-MM-DD`
- Body: the HTML assembled in step 6.
- Recipient: `you@example.com` or the configured recipient list.

## Errors

In any of the scenarios below, stop without sending the email. The reason must appear in the Routine transcript.

- No `.txt` file in `data/` because the Action did not run.
- `.txt` file older than 7 days because the Action is stale or broken.
- Text sanity check failed because the PDF layout may have changed.

Never invent a number.
