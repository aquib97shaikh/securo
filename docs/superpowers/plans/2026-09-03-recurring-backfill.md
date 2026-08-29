# Recurring Backfill Until Today Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a per-item Backfill until today action that rewinds a recurring bill to its start date and materializes due transactions through today, once.

**Architecture:** Extract `generate_pending`'s per-row loop into `_materialize_due`. Add `backfill_recurring` that loads one workspace bill, rejects inactive/no-account, sets `next_occurrence = start_date`, then materializes through `date.today()` (tests pass `up_to`). New `POST /api/recurring-transactions/{id}/backfill`. UI: form checkbox + row action.

**Tech Stack:** FastAPI, SQLAlchemy async, pytest-asyncio, React Query, i18next.

## Global Constraints

- Cutoff is today only (API never passes a future `up_to`).
- Do not persist a backfill flag on the row.
- Do not change Generate Pending selection (`auto_generate`, all user bills, current `next_occurrence`).
- Cap backfill at 200 occurrences per call; leave `next_occurrence` where it stopped.
- Matching, weekend adjustment, end_date, synced pending vs posted, FX stamp stay identical to `generate_pending`.
- User rule: do not commit unless asked.

---

### Task 1: Service `backfill_recurring`

**Files:**
- Modify: `backend/app/services/recurring_transaction_service.py`
- Test: `backend/tests/test_recurring_transaction_service.py`

**Interfaces:**
- Produces: `async def backfill_recurring(session, user_id, workspace_id, recurring_id, up_to: Optional[date] = None) -> int`
- Produces: `async def _materialize_due(session, user_id, recurring, cutoff, max_occurrences: Optional[int] = None) -> int` (no commit)
- Raises: `LookupError` if missing; `ValueError("Recurring transaction is inactive")`; `ValueError("Account is required")`

- [ ] **Step 1: Write the failing tests** in `test_recurring_transaction_service.py`
- [ ] **Step 2: Run tests, confirm fail** (`backfill_recurring` import error)
- [ ] **Step 3: Extract `_materialize_due`, implement `backfill_recurring`, switch `generate_pending` to the helper**
- [ ] **Step 4: Run tests, confirm pass**

### Task 2: API endpoint

**Files:**
- Modify: `backend/app/api/recurring_transactions.py`
- Test: `backend/tests/test_recurring_api.py`

**Interfaces:**
- Consumes: `backfill_recurring`
- Produces: `POST /api/recurring-transactions/{recurring_id}/backfill` → `{ "generated": int }`
- 404 on `LookupError`, 400 on `ValueError`, writable workspace

- [ ] **Step 1: Write failing API tests**
- [ ] **Step 2: Run, confirm 404/missing route**
- [ ] **Step 3: Add the route**
- [ ] **Step 4: Run API + service tests, confirm pass**

### Task 3: Frontend + copy + guide

**Files:**
- Modify: `frontend/src/lib/api.ts`, `frontend/src/pages/recurring.tsx`
- Modify: `frontend/src/locales/{en,de,es,fr,it,nl,pl,pt-BR,pt-PT,ru,uk}.json`
- Modify: `docs/guide/08-recurring-and-investments.md`

- [ ] **Step 1: Add `recurring.backfill(id)`**
- [ ] **Step 2: Checkbox + row Backfill action**
- [ ] **Step 3: Locales and guide**
- [ ] **Step 4: Browser-verify Recurring page**

## Service tests to add

```python
async def test_backfill_creates_through_today_only(...):
    rec = await create_recurring_transaction(..., start_date=date(2025, 1, 1), ...)
    rec.next_occurrence = date(2025, 9, 1)
    await session.commit()
    count = await backfill_recurring(..., up_to=date(2025, 3, 15))
    assert count == 3
    await session.refresh(rec)
    assert rec.next_occurrence == date(2025, 4, 1)

async def test_backfill_ignores_auto_generate_off(...)
async def test_backfill_second_call_creates_nothing(...)
async def test_backfill_links_existing_real_tx(...)
async def test_backfill_leaves_other_bills_untouched(...)
async def test_backfill_inactive_raises(...)
async def test_backfill_missing_account_raises(...)
async def test_backfill_unknown_id_raises_lookup(...)
```

## API tests to add

```python
async def test_backfill_endpoint_generates(client, auth_headers, test_account)
async def test_backfill_endpoint_404(client, auth_headers)
```

## UI behavior

- Checkbox `recurring.backfillUntilToday` when `startDate <= today`.
- Create: default checked iff `startDate < today`; keep in sync when start date changes on create only.
- Edit: default unchecked.
- After save, if checked: `POST .../backfill`; toast `recurring.generated`. Save success stands even if backfill fails (error toast).
- Row History button: disabled when inactive or `start_date > today`.
