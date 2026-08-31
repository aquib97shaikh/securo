"""Filenames for workspace archives stored on Google Drive.

Drive is instance-wide: one folder holds every workspace, distinguished by
the workspace name in the file. Characters Drive (and Windows) reject in a
name are stripped so an otherwise-valid workspace still produces a usable
zip name. Latest is a stable name that is overwritten; dated copies are
kept separately so retention can delete the oldest without touching latest.
"""
from __future__ import annotations

import re
from datetime import date

_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_DATED = re.compile(r"^(.+)-(\d{4}-\d{2}-\d{2})\.zip$")
_MAX_STEM = 80


def workspace_backup_stem(name: str) -> str:
    """Stable filename prefix derived from a workspace name."""
    cleaned = _UNSAFE.sub("", name).strip(" .")
    if not cleaned:
        return "workspace"
    return cleaned[:_MAX_STEM]


def latest_filename(stem: str) -> str:
    return f"{stem}-latest.zip"


def dated_filename(stem: str, day: date) -> str:
    return f"{stem}-{day.isoformat()}.zip"


def files_to_delete(names: list[str], stem: str, keep: int = 3) -> list[str]:
    """Dated files for `stem` older than the newest `keep`. Latest is never deleted."""
    dated: list[tuple[date, str]] = []
    for name in names:
        match = _DATED.fullmatch(name)
        if match is None or match.group(1) != stem:
            continue
        try:
            day = date.fromisoformat(match.group(2))
        except ValueError:
            continue
        dated.append((day, name))
    dated.sort(key=lambda item: item[0], reverse=True)
    return [name for _, name in dated[keep:]]
