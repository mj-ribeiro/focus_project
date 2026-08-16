import sys
from datetime import date, timedelta
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

# Add src/ to the import path, matching the local demo pipeline.
sys.path.insert(0, str(SRC_DIR))

from baixar_focus import download as baixar, last_monday


def test_last_monday_from_thursday():
    assert last_monday(date(2024, 1, 4)) == date(2024, 1, 1)


def test_last_monday_from_tuesday():
    assert last_monday(date(2024, 1, 2)) == date(2024, 1, 1)


def test_last_monday_from_monday_goes_back_one_week():
    assert last_monday(date(2024, 1, 1)) == date(2023, 12, 25)


def test_last_monday_from_sunday():
    assert last_monday(date(2024, 1, 7)) == date(2024, 1, 1)


def test_last_monday_is_always_prior_monday_for_60_day_scan():
    start = date(2024, 1, 1)

    for offset in range(60):
        today = start + timedelta(days=offset)
        result = last_monday(today)

        assert result.weekday() == 0
        assert result < today
        assert 1 <= (today - result).days <= 7


@pytest.mark.network
def test_download_focus_pdf_from_bcb(tmp_path):
    publication_date, file_path = baixar(tmp_path)
    file_path = Path(file_path)

    assert file_path.exists()
    assert file_path.read_bytes().startswith(b"%PDF")
    assert file_path.stat().st_size > 50 * 1024
    assert file_path.name == f"focus_{publication_date:%Y-%m-%d}.pdf"

    expected_latest = last_monday(date.today())
    expected_earliest = expected_latest - timedelta(days=6)

    assert expected_earliest <= publication_date <= expected_latest
