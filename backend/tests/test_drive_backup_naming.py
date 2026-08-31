from datetime import date

from app.services.drive_backup_naming import (
    dated_filename,
    files_to_delete,
    latest_filename,
    workspace_backup_stem,
)


def test_stem_strips_characters_drive_rejects_in_a_name():
    assert workspace_backup_stem('Acme / "Q1"') == "Acme  Q1"


def test_stem_falls_back_when_the_name_is_only_junk():
    assert workspace_backup_stem("///") == "workspace"


def test_latest_and_dated_filenames_use_the_stem():
    stem = workspace_backup_stem("Personal")
    assert latest_filename(stem) == "Personal-latest.zip"
    assert dated_filename(stem, date(2026, 8, 31)) == "Personal-2026-08-31.zip"


def test_retention_keeps_latest_plus_the_three_newest_dated_files():
    stem = "Personal"
    names = [
        latest_filename(stem),
        dated_filename(stem, date(2026, 8, 31)),
        dated_filename(stem, date(2026, 8, 30)),
        dated_filename(stem, date(2026, 8, 29)),
        dated_filename(stem, date(2026, 8, 28)),
        dated_filename(stem, date(2026, 8, 27)),
        "Business-2026-08-31.zip",
    ]
    assert files_to_delete(names, stem, keep=3) == [
        dated_filename(stem, date(2026, 8, 28)),
        dated_filename(stem, date(2026, 8, 27)),
    ]


def test_retention_ignores_other_workspaces_and_unparseable_names():
    stem = "Personal"
    names = ["Personal-latest.zip", "readme.txt", "Personal-backup.zip"]
    assert files_to_delete(names, stem, keep=3) == []
