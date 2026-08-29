# 4. Recording transactions

A **transaction** is one movement of money: a ₹340 Swiggy order, your ₹2,20,000 salary, a ₹50,000 transfer to your brokerage. Everything else in Securo — budgets, reports, net worth — is calculated from these.

Go to **`Transactions`** in the sidebar.

---

## 4.1 Adding your first one

Click **`Add Transaction`** (on a phone, **`+ Add`**). Working through the form:

| Field | What it means |
|-------|---------------|
| `Description` | What it was. `Swiggy - dinner`, not `food` |
| `Amount` | Always a **positive number**. Whether it's money in or out is set by `Type`, not by a minus sign |
| `Currency` | `INR` |
| `Date` | When it happened |
| `Status` | `Posted` (money has actually moved) or `Pending` (authorised but not settled). Use `Posted` for almost everything |
| `Type` | `Expense` or `Income` |
| `Category` | Which bucket it belongs to. See [chapter 6](06-categories-and-rules.md) |
| `Payee` | Who you paid, or who paid you. Optional |
| `Account` | Which account it came from or went into |
| `Notes` | Free text. Anything starting with `#` becomes a searchable tag |

Then **`Save`**.

The `Save` button has a dropdown with **`Save & New`** and **`Save & Duplicate`**. `Save & New` keeps the dialog open for the next one — the right choice when you're entering a week of receipts in one sitting.

### Two conventions worth internalising

**Amounts are never negative.** The sign is implied by `Type`. Typing `-340` will confuse things.

**`Expense` and `Income` are the only two types.** You may see the words *debit* and *credit* in exported files or technical documentation. `debit` means `Expense`, `credit` means `Income`. It's the same thing in accountant's language.

---

## 4.2 Transfers: the mistake everyone makes first

You move ₹50,000 from your HDFC account to your ICICI account.

**The wrong way** — and the instinctive one — is to record an `Expense` of ₹50,000 in HDFC and an `Income` of ₹50,000 in ICICI. Your balances come out right, so it looks like it worked. But your reports now show ₹50,000 of income you never earned and ₹50,000 of spending that never happened. Do this a few times and your savings rate becomes fiction.

**The right way:** use the transfer feature. Click **`Transfer`** in the page header (it's also on each account's detail page).

The **`Transfer Between Accounts`** dialog asks for:

- `From account`
- `To account`
- `Amount` and `Date`
- `Description` — required. Something like `To ICICI for FD`
- `Notes` — optional

Save, and you get a toast reading `Transfer created`. Both sides appear in your transaction list with a **`Transfer`** badge, and the tooltip explains the point: *"Transfers are excluded from report and dashboard totals."*

### What counts as a transfer

Money moving between things you own. It's not income and it's not spending — your net worth doesn't change.

- Bank to bank ✅
- Bank to brokerage or mutual fund ✅
- **Paying your credit card bill** ✅ — this one surprises people, but the spending already happened when you swiped the card. Paying the bill just moves money from your bank to the card
- Bank to a fixed deposit ✅
- Cash withdrawal from an ATM ✅ (bank → `Cash` wallet)
- Buying something ❌ — that's an expense
- Salary arriving ❌ — that's income

**If you already have currencies to bridge:** when the two accounts use different currencies, the dialog says *"Currencies differ — enter the destination amount or leave it blank to convert automatically"* and shows a second amount field. Leave it blank to use the exchange rate, or type the exact amount that landed if you know it.

**If you imported both sides separately** and only realised afterwards, you don't have to delete and redo. Select the two rows in the transaction list and use the bulk action **`Link as transfer`**.

---

## 4.3 EMIs and installments

You buy a ₹90,000 laptop on a 6-month no-cost EMI.

Recording it as a single ₹90,000 expense in August makes August look catastrophic and the next five months look artificially good — while ₹15,000 a month quietly leaves your account.

Instead, when adding the transaction, tick **`Repeat as installments`**:

- `Frequency` — `Monthly` (also available: `Weekly`, `Quarterly`, `Yearly`)
- `Number of installments` — `6`

Enter the **per-installment amount** (₹15,000), not the total. Securo creates six linked transactions across six months. Each shows a badge like `2/6`, and hovering it says *"Installment plan — 6 charges totaling ₹90,000."*

Now August shows ₹15,000, and you can see the ₹75,000 of future commitment sitting in the months ahead — which is exactly the information you need before agreeing to the next EMI.

When you edit or delete one, Securo asks **`Apply to which installments?`** with three options: `This one`, `This and future`, `All installments`. Useful when you prepay the balance, or when the amount changes.

The same mechanism works for a home loan or a car loan, though for those a **recurring transaction** is usually better — see [chapter 8](08-recurring-and-investments.md). Use installments for a fixed, finite number of payments; use recurring for something ongoing.

---

## 4.4 Splitting a bill

You pay ₹4,800 for dinner with three friends. You spent ₹1,200; the rest is owed to you.

First you need a **group** — a set of people you regularly split with. In the transaction form, tick **`Split this transaction`** and either pick an existing `Group` or click **`+ Add group`** to make one on the spot (`Name`, `Type`, `Default currency`, `Notes`).

Then choose **`Split by`**:

| Option | When to use it |
|--------|----------------|
| `Equal` | Divide evenly among the people you tick. The common case |
| `Exact amounts` | Everyone pays for what they ordered. You type each amount |
| `Percentages` | Uneven but proportional — three flatmates splitting rent 40/30/30 |

Tick the members involved. Your own row is marked `(you)`.

Securo now knows that ₹3,600 of that ₹4,800 is owed back to you, and tracks the running balance in the group. [Chapter 10](10-sharing-and-safety.md) covers settling up.

**Bulk splitting:** select several transactions in the list and use **`Add to group`** to apply one split rule across all of them — handy for a trip where you paid for everything. Only `Equal` and `Percentages` work in bulk; exact amounts have to be per-transaction.

---

## 4.5 Attaching receipts

Open any saved transaction and find the **`Attachments`** section. Drag a file in, or click where it says `Drop files here or click to upload`.

- **Formats:** jpg, jpeg, png, webp, gif, heic, pdf
- **Size:** up to 10 MB each
- **Count:** up to 10 per transaction

Worth doing for things with a warranty, anything you'll claim as a reimbursement, medical bills for insurance claims, and large purchases. Not worth doing for your morning coffee.

---

## 4.6 Finding things later

**Search.** The box at the top searches descriptions. Typing `#work` turns into a tag filter chip.

**`Filters`** gives you:

| Filter | Options |
|--------|---------|
| `Account` | One or several accounts |
| `Category` | Any category, or `Uncategorized` |
| `Payee` | |
| `Group` | |
| `Type` | `All`, `Income`, `Expense` |
| `Status` | `All`, `Pending`, `Posted` |
| `Hide ignored` | A toggle |
| `Date` | `Today`, `Last 7 days`, `Last 30 days`, `This month`, `Last 90 days`, `This year`, or `Custom range…` |
| `Amount` | `Min` and `Max` |

**`Clear filters`** resets everything.

Three filters do most of the real work: `Category` = `Uncategorized` (your monthly cleanup list), `Amount` with a `Min` of ₹5,000 (find the big items), and `Date` = `Last 30 days`.

**Views.** Switch between **`List`** and **`Calendar`**. The calendar lays transactions out by day, which makes spending patterns obvious — a lot of people discover their weekends cost three times their weekdays.

**`Columns`** lets you show or hide columns in the list view.

---

## 4.7 Doing things to many transactions at once

Tick the checkboxes on several rows and a bar appears at the bottom showing the count and their net total. From there:

| Action | Use |
|--------|-----|
| Category picker | Categorise all of them at once |
| `Add to group` | Split them all with the same people |
| Tag box | Add or remove a `#tag` in bulk |
| `Link as transfer` | Join two rows into a transfer pair (exactly two rows) |
| `Create Rule` | Build an automatic rule from a transaction (one row) |
| `Delete` | Permanent, and it warns you |

The bulk categoriser is how you'll clean up after each import. Filter to `Uncategorized`, sort by description, tick all the Swiggy rows, categorise in one click. Then build a rule so it never comes back — [chapter 6](06-categories-and-rules.md).

---

## 4.8 Ignoring a transaction

Open a transaction and click **`Ignore`**. It stays in your account balance but drops out of income and expense reports.

Use it sparingly, for genuine noise: a duplicate you can't delete because it came from an import, a refund that would otherwise double-count, a test transaction from setup day.

Do not use it to hide spending you regret. `Restore` puts it back.

---

## 4.9 Payees

A **payee** is who you paid: Swiggy, your landlord, your employer. Filling this in is optional but it unlocks the **`Payees`** page, which shows per-payee `Total Spent`, `Total Received`, transaction count, `Last Transaction` and `Top Category`.

This answers questions budgets can't. Your `Food & Dining` category might be ₹12,000 a month, and look fine. The payee page tells you ₹8,400 of it is one delivery app across 31 orders — a different problem with a different solution.

Practical notes: mark the ones you use constantly as favourites with the star. If imports have created `SWIGGY`, `Swiggy Ltd` and `SWIGGY BANGALORE` as three payees, select them and use **`Merge`** — pick a target with `Merge into` and every transaction is reassigned.

---

## 4.10 Making the habit stick

You have three options, in descending order of realism:

**Weekly, batched (recommended).** Fifteen minutes on Sunday. Import the week's bank statement, add the cash spends you remember, categorise what the rules missed. Least effort, and you catch problems while you still remember the transaction.

**Monthly, batched.** Same job, once a month, taking about half an hour. Works, but you'll misremember cash spending and you're a month late spotting a fraudulent charge.

**Daily, as it happens.** Most accurate. Almost nobody sustains it past three weeks. Don't set this as your standard and then feel like a failure.

Start weekly. If you find yourself skipping, drop to monthly rather than stopping entirely. The failure mode isn't imprecision, it's abandonment.

> **One thing you won't find here:** upcoming recurring bills don't appear on the Transactions page. They show on the **dashboard** and on individual account pages with a violet **`Projected`** badge. If you're looking for next month's rent and can't find it in the list, that's why.

---

**Next:** [Chapter 5 — Importing bank statements](05-import-statements.md)
