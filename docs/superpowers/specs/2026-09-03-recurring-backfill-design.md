# Recurring backfill until today

Date: 2026-09-03

## Problem

Saving a recurring bill with a start date in the past only stores that date as `next_occurrence`. It does not create the Jan–today transactions. **Generate Pending** walks from `next_occurrence` forward, so it cannot fill history after the user later changes start date. Changing the system clock is not a solution: generation already uses today as the cutoff.

## Decision

Per-item **Backfill until today** (approach A).

- One explicit action for a single recurring bill.
- Rewind `next_occurrence` to `start_date`, then materialize every due occurrence whose effective date is `<= today`.
- Stop there. Dates after today stay projected / wait for the normal generator.
- After a successful run, `next_occurrence` is the first nominal date after today (or past `end_date`, in which case the bill deactivates as today).
- Existing match logic still applies: a real/imported/manual charge that already covers an occurrence is linked instead of duplicated.
- A second click is safe: already-created months match and are skipped.
- `skip_first` is not stored. If the first occurrence already exists as a real transaction, matching links it instead of duplicating.
- Does not require **Generate transactions automatically**. That flag still controls the hourly job and **Generate Pending**.
- **Generate Pending** is unchanged (all of the user’s auto-generate bills, from current `next_occurrence`, including the dashboard’s future `up_to`).

Example: monthly, start 1 Jan 2026, today 3 Sep 2026 → transactions for Jan through 1 Sep, then `next_occurrence` = 1 Oct 2026.

## Out of scope

- Changing the OS / container clock
- Backfilling every recurring bill in one click
- Generating future months
- Persisting a “backfill” setting on the row
- Rewinding **Generate Pending** to each bill’s start date

## API

`POST /api/recurring-transactions/{id}/backfill`

Writable workspace. Returns `{ "generated": <int> }` (count of new transaction rows, not linked existing ones).

Service: `backfill_recurring(session, user_id, workspace_id, recurring_id) -> int`.

1. Load the bill in this workspace. Missing → 404.
2. Inactive → 400 `"Recurring transaction is inactive"`.
3. Missing `account_id` → 400 `"Account is required"`.
4. Set `next_occurrence = start_date`.
5. Run the same materialize loop as `generate_pending` for **this row only**, cutoff `date.today()`. Ignore `auto_generate`. Honor weekend adjustment, `end_date`, synced-account pending vs posted, FX stamp, and occurrence matching.
6. Cap at 200 new or linked occurrences per call (same bound as `get_occurrences_in_range`). If the cap hits, commit progress and leave `next_occurrence` where it stopped so the user can click again.
7. Commit and return the new-row count.

Extract the per-row loop from `generate_pending` into a shared helper so backfill and the existing generator stay identical except for selection, rewind, auto-generate filter, and cutoff.

## UI

On **Add Recurring** / **Edit Recurring**: checkbox **Backfill until today**, shown when start date is today or earlier.

- Help text: create one transaction per due date from start date through today. Later dates wait for their due date.
- Create: checked by default when start date is before today.
- Edit: unchecked by default so a description/amount save does not surprise-backfill.
- After a successful create/update, if the box was checked, call `POST .../backfill` and toast the generated count (same copy as Generate Pending).

On each list row (write access): **Backfill** action next to edit/delete. Hidden or disabled when the bill is inactive or start date is in the future. Same endpoint and toast.

## Errors

| Case | Result |
|------|--------|
| Unknown id / other workspace | 404 |
| Inactive | 400 |
| No account | 400 |
| Viewer (no write) | existing writable-workspace 403 |
| Start date in the future | `{ "generated": 0 }`, `next_occurrence` stays `start_date` |
| Nothing left to create | `{ "generated": 0 }` |

Frontend: failed backfill after a successful save still shows the recurring as saved, plus an error toast for the backfill call.

## Tests

Service (freeze today where needed):

- Monthly start 1 Jan, today 15 Mar → 3 rows (Jan, Feb, Mar), `next_occurrence` 1 Apr.
- Does not create April when today is 15 Mar.
- `next_occurrence` already in the future, start date in the past → still fills the gap.
- `auto_generate=false` still creates history.
- Second backfill adds no extra rows; matching links an existing real charge.
- Other recurring bills are untouched.
- Inactive / missing account raise `ValueError` with the API messages above.

API: 200 with `generated`, 404 for unknown id, write-gated.

No new frontend unit tests (the Recurring page has none). Verify in the browser: checkbox for a past start date, create with it checked creates Jan–today rows, row Backfill on an existing item does the same.

## Docs

Update `docs/guide/08-recurring-and-investments.md`: Backfill until today is the way to fill history after a past start date; Generate Pending remains the catch-up for missed days.
