import argparse
import os
import re
import smtplib
import sys
from email.message import EmailMessage
from html.parser import HTMLParser
from pathlib import Path


SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
DEFAULT_SENDER = "dry-run@example.com"
FOCUS_DATE_PATTERN = re.compile(r"^focus_(\d{4}-\d{2}-\d{2})\.html$")


class HtmlTextExtractor(HTMLParser):
    """Convert simple HTML content into readable plain text."""

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_starttag(self, tag, attrs):
        # Add light spacing around common block elements in the text fallback.
        if tag in {"p", "br", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data):
        text = data.strip()
        if text:
            self.parts.append(text)

    def get_text(self):
        return "\n".join(part for part in self.parts if part.strip()).strip()


def find_latest_html(output_dir=None):
    """Find the most recent focus_*.html file in output/focus/."""
    if output_dir is None:
        project_root = Path(__file__).resolve().parents[1]
        output_dir = project_root / "output" / "focus"

    html_files = sorted(Path(output_dir).glob("focus_*.html"))
    return html_files[-1] if html_files else None


def parse_recipients(value):
    """Parse comma-separated email addresses from an argument or environment value."""
    if not value:
        return []

    return [address.strip() for address in value.split(",") if address.strip()]


def subject_from_html_path(html_path):
    """Build the default subject from a focus_YYYY-MM-DD.html filename."""
    match = FOCUS_DATE_PATTERN.match(Path(html_path).name)
    if not match:
        raise ValueError(f"Could not derive date from HTML filename: {html_path}")

    return f"Focus Summary — {match.group(1)}"


def html_to_text(html):
    """Create a plain-text fallback body from the HTML summary."""
    parser = HtmlTextExtractor()
    parser.feed(html)
    text = parser.get_text()
    return text or "Focus summary attached in HTML format."


def build_message(sender, recipients, bcc_recipients, subject, html):
    """Assemble the email with plain-text and HTML bodies."""
    message = EmailMessage()
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject

    # BCC recipients are used in the SMTP envelope, not exposed as a header.
    message.set_content(html_to_text(html))
    message.add_alternative(html, subtype="html")

    all_recipients = recipients + bcc_recipients
    return message, all_recipients


def send_message(message, recipients, sender, app_password):
    """Send the email through Gmail SMTP over SSL."""
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
        smtp.login(sender, app_password)
        smtp.send_message(message, from_addr=sender, to_addrs=recipients)


def normalize_app_password(app_password):
    """Remove cosmetic spacing from a Gmail app password."""
    if not app_password:
        return app_password

    return "".join(app_password.split())


def main():
    """Run the command-line interface for sending a Focus HTML summary."""
    parser = argparse.ArgumentParser(
        description="Send the latest Focus HTML summary through Gmail SMTP."
    )
    parser.add_argument(
        "--html",
        type=Path,
        help="Path to a specific focus_YYYY-MM-DD.html file.",
    )
    parser.add_argument(
        "--dest",
        help="Comma-separated recipients. Defaults to FOCUS_EMAIL_DEST.",
    )
    parser.add_argument(
        "--subject",
        help="Email subject. Defaults to Focus Summary — YYYY-MM-DD.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Assemble and display the email without sending or requiring credentials.",
    )
    args = parser.parse_args()

    html_path = args.html or find_latest_html()
    if html_path is None:
        print("No focus_*.html file found in output/focus/.", file=sys.stderr)
        return 1

    if not html_path.exists():
        print(f"HTML file not found: {html_path}", file=sys.stderr)
        return 1

    html = html_path.read_text(encoding="utf-8")
    subject = args.subject or subject_from_html_path(html_path)
    recipients = parse_recipients(args.dest or os.getenv("FOCUS_EMAIL_DEST"))
    bcc_recipients = parse_recipients(os.getenv("FOCUS_EMAIL_BCC"))

    if args.dry_run:
        sender = os.getenv("FOCUS_SMTP_USER") or DEFAULT_SENDER
        message, all_recipients = build_message(
            sender, recipients, bcc_recipients, subject, html
        )

        print("DRY RUN: email assembled but not sent.")
        print(f"HTML: {html_path}")
        print(f"From: {sender}")
        print(f"To: {', '.join(recipients) if recipients else '(none)'}")
        print(f"BCC: {', '.join(bcc_recipients) if bcc_recipients else '(none)'}")
        print(f"Envelope recipients: {len(all_recipients)}")
        print(f"Subject: {subject}")
        print()
        print(message)
        return 0

    sender = os.getenv("FOCUS_SMTP_USER")
    app_password = normalize_app_password(os.getenv("FOCUS_SMTP_APP_PASSWORD"))

    if not sender:
        print("Missing FOCUS_SMTP_USER environment variable.", file=sys.stderr)
        return 1

    if not app_password:
        print("Missing FOCUS_SMTP_APP_PASSWORD environment variable.", file=sys.stderr)
        return 1

    if not recipients:
        print("Missing recipients. Set FOCUS_EMAIL_DEST or pass --dest.", file=sys.stderr)
        return 1

    message, all_recipients = build_message(
        sender, recipients, bcc_recipients, subject, html
    )
    try:
        send_message(message, all_recipients, sender, app_password)
    except smtplib.SMTPAuthenticationError:
        print(
            "Gmail rejected the SMTP login. Check that FOCUS_SMTP_USER is the full "
            "Gmail address for the same account that created the app password, and "
            "that FOCUS_SMTP_APP_PASSWORD is a Gmail app password, not the normal "
            "Google account password.",
            file=sys.stderr,
        )
        return 1
    except smtplib.SMTPException as exc:
        print(f"SMTP error while sending email: {exc}", file=sys.stderr)
        return 1

    print(f"Email sent: {subject}")
    print(f"Recipients: {', '.join(recipients)}")
    if bcc_recipients:
        print(f"BCC recipients: {len(bcc_recipients)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
