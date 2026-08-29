# 12. FAQ and glossary

---

## Frequently confusing things

### Where is the Dashboard link? I can't find it in the sidebar

There isn't one. Click the **Securo** logo at the top of the sidebar. Everyone hits this.

### My balance in Securo doesn't match my bank

Almost always one of four things ([chapter 3](03-accounts.md), section 3.7): missing transactions (usually cash or the last few days), a transaction imported twice, a wrong opening balance or opening date, or a transfer recorded as a separate expense and income.

Open the account and read down the running `Balance` column against your bank statement. The problem is at the first row where they diverge.

### My savings rate says 0%, or something negative

Your investments are being counted as spending. Go to `Categories`, find `Investments` and `Transfers`, and make sure **`Treat as transfer`** is ticked ([chapter 6](06-categories-and-rules.md), section 6.4). Then check that money you moved between your own accounts was recorded as a transfer, not as an expense-and-income pair.

### I chose the wrong currency at setup

There's no user-facing way to change it. Ask whoever administers the server — it's a database field. This is why [chapter 2](02-first-hour.md) makes such a point of it.

### Can I connect my Indian bank account?

No. The three sync providers cover Brazil, Europe and the United States. Import statements instead ([chapter 5](05-import-statements.md)).

### My bank only gives PDF statements

Look harder in net banking — most Indian banks bury a CSV or Excel export somewhere. If it truly doesn't exist, enter the significant transactions manually and accept some imprecision on the small ones. PDF converters produce output that usually takes longer to clean than typing.

### Why does ₹5 lakh show as 500,000.00 instead of 5,00,000.00?

Securo's number formats are `1,000.00`, `1.000,00` and `1 000,00`. The Indian lakh/crore grouping isn't among them. The amounts are correct, just grouped Western-style.

### Do I really need to track cash?

Only if it's material. Under ₹5,000 a month, record the ATM withdrawal as an expense and move on. Over ₹15,000 a month, track it properly — it's a big enough hole to make your reports wrong.

### How do I record paying my credit card bill?

As a **transfer** from your bank account to the credit card account ([chapter 4](04-transactions.md), section 4.2). Not as an expense. The spending already happened when you used the card.

### How do I record my salary?

As a recurring `Income` transaction into your salary account, for your **in-hand** amount ([chapter 8](08-recurring-and-investments.md)). Not gross, not CTC. Your EPF is tracked separately as an asset.

### What's the difference between an account and an asset?

An **account** only changes when there's a transaction. An **asset** changes value on its own.

Your savings account is an account. Your mutual funds are an asset — their value moves whether or not you do anything.

### Why won't my mutual fund price update automatically?

Market prices come from Yahoo Finance, which doesn't carry Indian mutual fund NAVs in a usable form, and there's no AMFI integration. Track Indian mutual funds as `Manual` assets and update the value monthly ([chapter 8](08-recurring-and-investments.md), section 8.7).

Indian *stocks* often do work — try `RELIANCE.NS` or `.BO` for BSE, and test the ticker in the search box before committing.

### Can I restore from a backup?

**No, not inside the app.** The zip contains readable JSON, so the data isn't gone, but putting it back requires scripting against the API or loading it into the database by hand.

What actually protects you is a PostgreSQL backup of the server. Read [chapter 10](10-sharing-and-safety.md), section 10.5.

### I forgot my password

If email is configured on the server, use the forgot-password link. If not, the admin can reset it from the admin page. If you *are* the admin on a server with no email — that's a database operation.

### I enabled 2FA and lost my phone

There are no recovery codes. You need database access to disable it. [Chapter 10](10-sharing-and-safety.md) warns about this before you turn it on.

### Can my spouse and I use this together?

Yes. Two ways: share one workspace (`Workspace settings` → `Members`, giving them `Owner` or `Editor`), or keep separate workspaces and use a **group** to split shared expenses. [Chapter 10](10-sharing-and-safety.md).

### Does unspent budget carry over to next month?

No. There's no rollover. For expenses you save up for, use a **goal** instead ([chapter 7](07-budgets-and-goals.md)).

### Will Securo tell me when a bill is due or I'm over budget?

No. There are no emails, no push notifications, no alerts of any kind. You have to open the app. Put a recurring reminder in your calendar.

### What's the difference between "treat as transfer" and "ignore"?

**Treat as transfer** means the money moved between things you own — it's not income or spending. Use it for SIPs, FDs, credit card payments.

**Ignore** removes a transaction from reports entirely. Use it rarely, for genuine duplicates or noise.

Neither affects your account balance.

### Should I delete or close an old account?

**Close** it. That keeps the transaction history so your past reports stay correct. Delete only for accounts created by mistake.

### I imported the same statement twice

Undo the import: `Import` page → `Import History` → trash icon → `Delete all`. It removes only that batch. Then re-import with `Skip duplicate transactions` ticked.

### Does it work on my phone?

Yes, the interface adapts. There's no native app — open the URL in your phone's browser. If your server is only on your home network, it works at home; exposing it to the internet is a decision with security implications you should think through.

### Is my data actually private?

The data sits in a database on whichever machine runs Securo. If that's your own hardware, nobody else has it. The exceptions: market price lookups go to Yahoo Finance (ticker symbols only), currency conversion contacts a rate API if configured, and Google Drive backup uploads your data to Google if you enable it. All optional.

---

## Glossary

### Money terms

**Asset** — Something you own that has value. Investments, property, gold.

**Basic salary** — The core component of your pay. PF, gratuity and HRA exemptions are calculated from it, so a higher basic means more forced saving and less take-home.

**Compounding** — Returns earning returns. The reason a 27-year-old investing ₹10,000 a month ends up far ahead of a 37-year-old investing ₹20,000.

**CTC (Cost to Company)** — What your employer spends on you annually, including things you never receive as cash. The biggest number on your offer letter and the least useful.

**Emergency fund** — Six months of spending, kept somewhere you can reach in a day. Insurance, not an investment.

**EPF (Employees' Provident Fund)** — Retirement savings. You contribute 12% of basic, your employer matches it. Both are yours.

**Equity** — Ownership in companies. Stocks, or mutual funds that hold stocks. Volatile short-term, historically the best long-term returns.

**Gross salary** — Your pay before deductions.

**HRA (House Rent Allowance)** — A salary component that's tax-exempt if you actually pay rent, and fully taxable if you don't.

**In-hand salary** — What reaches your bank account. The only figure to budget with.

**Index fund** — A fund that tracks a market index like the Nifty 50, with low fees and no fund manager trying to beat the market.

**Liability** — Something you owe. Loans, credit card balances.

**Liquidity** — How fast you can turn something into spendable cash without losing value. A savings account is liquid; property is not.

**Net worth** — Everything you own minus everything you owe.

**NPS (National Pension System)** — A government retirement scheme with additional tax deductions and long lock-in.

**PPF (Public Provident Fund)** — A 15-year government savings scheme with tax-free returns and a ₹1.5 lakh annual limit.

**Savings rate** — The share of take-home pay you don't spend. The number that matters most.

**Sinking fund** — Money set aside monthly for a known irregular expense: festivals, insurance renewals, a new phone.

**SIP (Systematic Investment Plan)** — Investing a fixed amount monthly, automatically.

**TDS (Tax Deducted at Source)** — Income tax your employer deducts and pays on your behalf each month.

**Term insurance** — Pure life cover. Pays out if you die during the term, nothing otherwise. Cheap, and the only kind of life insurance most people should buy.

### Securo terms

**Account** — A place money sits: bank account, credit card, cash, wallet. Changes only via transactions.

**Asset** *(in Securo)* — An investment or possession whose value changes independently of transactions. Tracked on the `Assets` page.

**Budget** — A monthly spending limit on one category.

**Category** — The label you sort a transaction into.

**Category group** — A folder that organises categories.

**Collection** — A named bundle of accounts and wallets used to filter the app.

**Goal** — A savings target with progress tracking.

**Group** — A set of people you split expenses with.

**Installments** — A purchase split across several future transactions. For EMIs.

**Payee** — Who you paid or who paid you.

**Posted / Pending** — Whether the money has actually moved, or is only authorised.

**Privacy mode** — Masks every amount as `•••••`.

**Projected** — A transaction that hasn't happened yet, generated from a recurring rule. Shown on the dashboard, not the transactions page.

**Recurring transaction** — A bill or income that repeats on a schedule.

**Rule** — An automatic action on transactions matching a pattern. The feature that makes the app maintainable.

**Split** — Dividing one transaction among group members.

**Transfer** — Money moving between accounts you own. Excluded from income and expense reports.

**Treat as transfer** — A category flag marking its transactions as movements between your own accounts rather than spending.

**Wallet** — A container that groups assets. Also the name of a Securo account type for cash and payment app balances — the two meanings are unrelated, which is unfortunate.

**Workspace** — A separate container with its own accounts, categories, budgets and goals.

---

## Where to go next

You've finished the guide. Some suggestions:

- **Use it for three months before changing anything.** Consistency teaches you more than optimisation.
- **The official documentation** at [docs.usesecuro.com](https://docs.usesecuro.com/) covers features this guide skipped: bank sync for supported countries, OIDC single sign-on, and the optional AI agents.
- **On the money side**, the highest-value next step is understanding index funds and asset allocation. Ignore anything promising to beat the market.

The system only works if you keep using it. Fifteen minutes a week.

---

[← Back to the index](README.md)
