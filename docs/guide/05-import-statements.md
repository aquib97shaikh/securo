# 5. Importing bank statements

This is the chapter that makes Securo practical for Indian users. Since no Indian bank connects automatically, importing statements is how your data gets in. It takes about two minutes per account once you've done it twice.

Go to **`Import`** in the sidebar. The page is headed **`Bank statement`** and has two tabs: **`Transactions`** and **`Investments`**. Stay on `Transactions` for now.

---

## 5.1 Getting a file out of your bank

Securo accepts **OFX, CSV, QIF and CAMT** files (extensions `.ofx`, `.qfx`, `.csv`, `.qif`, `.xml`, `.camt`).

What Indian banks actually give you varies:

| Bank | Where to look | What you get |
|------|---------------|--------------|
| HDFC | Net banking → Accounts → Enquire → Statement → *Download in Excel/Delimited* | `.xls` or delimited text |
| ICICI | Net banking → Bank Accounts → Statements → Excel | `.xls` |
| SBI | Net banking → Account Statement → CSV or XLS | `.csv` or `.xls` |
| Axis | Net banking → Accounts → Download statement | `.xls` or `.csv` |
| Most credit cards | Card statement section, or the monthly email | Usually PDF, sometimes CSV |

**If you get a `.xls` or `.xlsx`:** open it in Excel, LibreOffice or Google Sheets and save as CSV. Securo can't read Excel files directly.

**If you only get a PDF:** this is the annoying case. Options, in order of preference — look harder in net banking for a CSV or Excel option (most banks have one, often buried); check whether your credit card issuer's app offers a statement export; or fall back to entering the larger transactions manually and letting the small ones go. PDF-to-CSV converters exist but produce messy output that often takes longer to fix than manual entry.

### Clean the file before uploading

Bank exports usually need thirty seconds of tidying:

1. **Delete the header block.** Indian statements typically open with several rows of account holder name, address, account number, statement period. Delete everything above the row containing the actual column names (`Date`, `Narration`, `Withdrawal Amt.` and so on).
2. **Delete the footer.** Closing balance summaries, disclaimers, "This is a computer generated statement."
3. **Check the columns survived.** You want one row of column names, then one row per transaction, and nothing else.
4. **Save as CSV.**

If you're unsure what shape the file should be, click **`Download CSV template`** on the import page to see Securo's expected format.

---

## 5.2 Uploading

Drag your file onto the box reading **`Drag a file or click to select`**, or click it and browse.

Securo parses the file and shows the filename with something like `147 transactions · format CSV`. If that count looks wrong — 3 when you expected 150 — your header rows are probably still in the file. Click **`Remove file`**, fix it, try again.

### Choose the destination account

Next to **`Import to:`**, pick the account this statement belongs to. **One statement, one account.** If you're importing HDFC and ICICI, that's two separate imports.

Getting this wrong puts a hundred transactions in the wrong account. There's an undo (section 5.6), but it's easier to check now.

---

## 5.3 CSV options

For CSV files, a **`CSV Options`** section appears. If Securo couldn't work out your columns automatically it tells you so: *"We couldn't recognize your CSV columns automatically. Map them to Securo fields below to continue."*

### `Date format`

Options are `Auto (detect)`, `DD/MM/YYYY`, `MM/DD/YYYY` and `YYYY-MM-DD`.

**Set this explicitly to `DD/MM/YYYY` for Indian bank statements.** Don't rely on auto-detect. Here's why: `05/03/2026` is 5th March in India and 3rd May in America. Auto-detection guesses from the whole file, and it usually guesses right — but if your statement happens to contain only dates where both readings are valid (nothing above the 12th of a month), it can silently pick wrong and shift every transaction by months.

Two seconds of explicitness avoids an hour of confusion.

### `Split inflow/outflow columns`

**Most Indian bank statements need this.** They don't have a single signed amount column — they have two, typically named `Withdrawal Amt.` and `Deposit Amt.`, where each row fills in one and leaves the other blank.

Tick **`Split inflow/outflow columns`** and two dropdowns appear:

- **`Inflow column`** → your deposit/credit column (money coming in)
- **`Outflow column`** → your withdrawal/debit column (money going out)

If your statement has a single `Amount` column with negatives for spending, leave this unticked.

### `Negate amounts (swap income/expense)`

Only needed if your file's signs are backwards from Securo's expectation — some credit card exports show purchases as positive and payments as negative. Import a few rows, look at the preview, and tick it if income and expenses are the wrong way round.

### `Skip duplicate transactions`

**Leave this ticked.** It's on by default. Section 5.5 explains what it does.

---

## 5.4 Column mapping

Under **`Column mapping`**, tell Securo which of your CSV columns is which. Each dropdown defaults to `Auto-detect`, which is often right — but check them.

| Securo field | What to point it at |
|--------------|---------------------|
| `Date column` | Transaction date. Indian statements often also have a "Value Date" — use the transaction date |
| `Description column` | Usually `Narration`, `Particulars`, `Description` or `Remarks` |
| `Amount column` | Hidden when split inflow/outflow is on |
| `Type column` | Only if your file has an explicit debit/credit column |
| `Category column` | Rare in Indian statements |
| `Currency column` | Skip for rupee accounts |
| `FX rate column` | Skip |
| `Payee column` | Rare |
| `Transaction ID column` | **Map this if you have it.** Usually `Chq./Ref.No.` or `Reference Number`. It makes duplicate detection exact |
| `Notes column` | Anything else worth keeping |

Mapping the reference number column is the single highest-value thing on this screen — it turns duplicate detection from a heuristic into an exact match.

---

## 5.5 Duplicates

The overlap problem is unavoidable: you import 1st–31st August, then in September you download 1st August to 15th September because you forgot where you left off. Two weeks of transactions would land twice.

With **`Skip duplicate transactions`** on, Securo checks each incoming row against what's already in that account:

- **If you mapped a transaction ID:** it matches on that ID plus the date. Exact and reliable.
- **Otherwise:** it matches on date + amount + type + description. Also reliable, with one edge case — if you genuinely bought two identical ₹200 coffees at the same shop on the same day, the second gets treated as a duplicate and skipped.

For non-CSV formats (OFX, QIF, CAMT) duplicate detection is always on and can't be turned off. Those formats carry their own transaction IDs.

**Practical advice:** always download a slightly overlapping range rather than trying to be precise about where the last import ended. Skipped duplicates are harmless; missing transactions are not.

---

## 5.6 Reviewing before you commit

Nothing is saved until you press the final button. The **`Preview`** section shows what's about to happen.

A summary bar reports `147 transactions found`, `147 will be imported`, and `Balance impact:` with the net effect on your account balance. That last figure is a good sanity check — if your salary went in and you spent normally, it should look roughly like your month.

The review table lets you:

- **Untick any row** to exclude it. Its badge changes from `Included` to `Excluded`
- **Set a category** per row from the dropdown
- **Search and filter** the rows, including by `All` / `Included` / `Excluded`

You **cannot** edit dates, descriptions or amounts here. Those you fix after importing, on the Transactions page.

**How much reviewing is enough?** Scan the amounts for anything that looks impossible, verify the dates are in the range you expected, and check that income and expenses aren't reversed. Don't categorise row by row at this stage — do it in bulk afterwards, or better, set up rules so it happens automatically ([chapter 6](06-categories-and-rules.md)).

When you're satisfied, click **`Import 147 transactions`**. You'll get a confirmation like `142 imported, 5 duplicates skipped`.

---

## 5.7 Import history and undo

At the bottom of the import page, **`Import History`** lists every import: `Date`, `File`, `Format`, `Account`, `Qty`, `Credit`, `Debit`.

Each row has a trash icon. Clicking it asks **`Undo import?`** — *"This will delete N imported transactions from filename.csv. This action cannot be undone."* Confirm with **`Delete all`** and the whole batch disappears.

This is your safety net for the two mistakes everyone makes: importing into the wrong account, and importing with the wrong date format. Undo, fix, re-import. It only removes transactions that came from that import, so anything you added manually is untouched.

---

## 5.8 Your monthly routine

Once your rules are set up, this is the whole job:

1. Download last month's statement for each account
2. Save as CSV if needed, delete the header rows
3. Import each one — `Import to:` the right account, `DD/MM/YYYY`, split inflow/outflow, skip duplicates
4. Check the balance now matches your bank
5. Filter transactions to `Uncategorized` and clean up whatever the rules missed
6. Glance at the dashboard

**About ten minutes** for two accounts and a credit card. Do it on the first weekend of every month. Put it in your calendar — nothing in Securo will remind you, since there are no notifications of any kind.

---

## 5.9 Importing investments

The **`Investments`** tab imports buy and sell orders from a broker, rather than bank transactions. Its CSV template is:

```csv
ticker*,date*,quantity*,price*,fee,kind,currency,notes
```

The starred columns are required. A negative quantity means a sale. You choose which wallet the holdings go into, and confirm with `Import N orders`.

Whether this works for you depends on whether the price provider recognises your tickers — see [chapter 8](08-recurring-and-investments.md), which discusses the significant caveats for Indian stocks and mutual funds before you invest time here.

---

**Next:** [Chapter 6 — Categories and rules](06-categories-and-rules.md)
