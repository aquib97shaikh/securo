# 3. Setting up your accounts

An **account** in Securo is any place money sits: a bank account, a credit card, the cash in your wallet, the balance in a payment app. Getting these right takes fifteen minutes and everything else depends on it.

Go to **`Accounts`** in the sidebar.

---

## 3.1 What counts as an account

Before clicking anything, list the places your money actually lives. For Aarav:

| Real thing | Securo account type |
|------------|---------------------|
| HDFC salary account | `Savings` |
| ICICI account he opened years ago and forgot | `Savings` |
| HDFC Regalia credit card | `Credit Card` |
| Cash in his wallet | `Wallet` |
| Paytm / PhonePe balance | `Wallet` |
| Zerodha demat holdings | **Not an account** — see below |
| EPF and PPF | **Not an account** — see below |

The five available types are `Checking`, `Savings`, `Credit Card`, `Investment` and `Wallet`.

`Checking` is the American term for what Indian banks call a current account. Most salaried people don't have one — use `Savings` for your bank accounts.

### What does *not* belong here

**Your investments.** Mutual funds, stocks, EPF, PPF, fixed deposits, gold and property are tracked on the **`Assets`** page, not here. They behave differently: their value changes on its own, without a transaction. [Chapter 8](08-recurring-and-investments.md) covers them.

The `Investment` account type is for the *cash* lying idle in a broker account waiting to be invested — the money you transferred to Zerodha but haven't bought anything with. If you keep no idle cash there, skip it entirely.

**Loans.** There is no loan account type. Track an EMI as a recurring payment from your bank account ([chapter 8](08-recurring-and-investments.md)). The outstanding principal won't be reflected in your net worth, which is a real limitation worth knowing about.

---

## 3.2 Adding a normal bank account

Click **`Add Account`**. The form is short:

| Field | What to enter |
|-------|---------------|
| `Account name` | Something you'll recognise: `HDFC Salary`, not `Account 1` |
| `Type` | `Savings` |
| `Currency` | `INR` |
| `Balance` | Your balance right now — check your banking app |
| `Balance date` | Today's date, unless you're starting from an older statement |

Click **`Save`**.

### The balance and date, explained

This pair is the most misunderstood part of setting up. Securo creates an invisible starting transaction (you'll see it tagged `opening balance` in the account's transaction list) that establishes your balance on that date. Everything after that date is calculated from the transactions you add.

So the rule is: **the balance and the date must agree with each other.**

- Entering today's balance with today's date is correct and simplest. Recommended.
- Entering today's balance with a date of 1st April is wrong — you'd be claiming you had today's money four months ago, and then adding four months of transactions on top of it.
- Entering your 1st April balance with a date of 1st April is correct, but then you must import every transaction since April or your balance won't match reality.

**Do the simple thing:** today's balance, today's date. You lose historical data you were unlikely to enter anyway, and your numbers will be right from day one.

---

## 3.3 Adding a credit card

Credit cards get their own treatment because the numbers run backwards: a positive balance means you owe money.

Click **`Add Account`**, set `Type` to `Credit Card`, and the form changes:

| Field | What to enter |
|-------|---------------|
| `Account name` | `HDFC Regalia` |
| `Type` | `Credit Card` |
| `Currency` | `INR` |
| `Amount owed` | Your current outstanding, **as a positive number**. Owe ₹18,400? Enter `18400`. Owe nothing? Enter `0` |
| `Balance date` | Today |
| `Credit limit` | Optional but useful — your sanctioned limit, e.g. `500000` |
| `Statement close day` | Optional. The day your bill is generated, e.g. `18` |
| `Payment due day` | Optional. The day payment is due, e.g. `8` |

Securo spells the first one out for you: *"Enter how much you currently owe on this card as a positive number. Leave at 0 if you have no debt."*

### Fill in the two day fields

They're marked optional, and skipping them is a mistake. Your card statement shows both — the statement date and the payment due date. With them filled in, you unlock:

- A **bill view** on the account page that groups spending by billing cycle rather than by calendar month, which is how the card actually works
- A **`Due date`** panel that shows `Due in 6 days`, `Due today` or `Overdue`
- A **`Utilization`** bar showing how much of your limit you're using

Without them, the account page shows a `Set up cycle` badge nagging you until you do.

**Why the billing cycle matters more than you'd think.** If your statement closes on the 18th, then something you buy on the 20th of August isn't due until early October. Calendar months don't line up with card cycles, and that gap is exactly where people miscalculate what they owe.

Aarav's card: statement closes on the 18th, payment due on the 8th of the next month. A purchase on the 19th of August lands on the September statement, due 8th October — 50 days of free credit. A purchase on the 17th of August lands on the August statement, due 8th September — 22 days. Same card, same month, very different.

---

## 3.4 Cash and UPI wallets

**Cash.** Add a `Wallet` account named `Cash`, with whatever is physically in your wallet right now as the balance.

Should you bother? Honest answer: only if cash is a meaningful part of your spending. If you withdraw ₹2,000 a month for autos and chai and everything else is digital, tracking it precisely is more effort than it's worth. Just record the ATM withdrawal as an expense in a `Cash` category and let it go.

If cash is ₹15,000+ a month for you, track it properly, because that is a large enough hole to make your reports wrong.

**Paytm, PhonePe, Amazon Pay balances.** A `Wallet` account each, if you keep meaningful money in them. If you only use UPI to pay *from your bank account* — which is how most people use it — there's no wallet balance to track. Those UPI payments are just bank transactions and appear in your bank statement.

This is a common confusion worth stating plainly: **UPI is not a wallet.** It is a way of instructing your bank to pay someone. A UPI payment from your HDFC account is an HDFC transaction.

---

## 3.5 What the Accounts page shows you

Once you have a few accounts:

- **`Manual Accounts`** — everything you added by hand. All of your accounts, in India
- **`Closed Accounts`** — accounts you've retired, hidden from totals
- A **`Connect Bank`** button, which offers Pluggy (Brazil), Enable Banking (Europe) and SimpleFIN (US). None cover Indian banks. Ignore it

Each account row has actions: **`Edit`**, **`Close account`** and **`Delete`**.

**Close vs delete.** `Close account` hides the account from your totals but keeps all its transactions, so your history and past reports stay intact. It warns you: *"Close this account? It will be hidden from totals."* Closed accounts move to the `Closed Accounts` section with a **`Reopen account`** button.

`Delete` destroys the account and everything in it. Use it only for accounts created by mistake. When you actually close a bank account in real life, use `Close account` — you want the history.

---

## 3.6 The account detail page

Click any account name to open it. This is one long page, not tabs.

For a normal bank account, a row of figures across the top:

| Figure | Meaning |
|--------|---------|
| `Current balance` | What's in the account now |
| `Projected Balance` | What it will be at the end of the period, after known upcoming recurring transactions |
| `Income` | Money in, during the selected date range |
| `Expenses` | Money out |

Below that, a **`Balance Flow`** chart, and then the account's transactions with a running `Balance` column — useful for finding the exact point where your Securo balance stopped matching your bank's.

`From` and `To` date pickers at the top control the range.

### For a credit card

The page rearranges itself around billing cycles:

- A **cycle stepper** (`Previous cycle` / `Next cycle`) instead of date pickers
- A **timeline** of the last several bills as clickable bars
- **`Bill total`**, **`Available credit`** and **`Due date`** across the top
- A **`Utilization`** bar against your `Credit limit`
- A **`Cycle spending`** chart

A badge near the title tells you where you stand: `Due in 6 days`, `Due today`, or `Overdue`.

---

## 3.7 Getting your balances to match reality

The first time you check, your Securo balance will differ from your bank's. This is normal and always has one of a few causes:

1. **Missing transactions.** The usual one. Cash spends, or the last few days you haven't imported.
2. **A transaction entered twice.** Common after importing a statement that overlaps one you already imported. [Chapter 5](05-import-statements.md) covers duplicate handling.
3. **Wrong opening balance or wrong opening date.** See 3.2.
4. **A transfer recorded as two separate transactions.** Moving ₹50,000 from HDFC to ICICI recorded as an expense in one and income in the other looks right on balances but wrecks your income and expense figures. [Chapter 4](04-transactions.md) shows the correct way.

To find the discrepancy, open the account and read down the running `Balance` column against your bank statement until they diverge. The problem is at the first line where they differ.

**How often to check:** once a month, when you import your statement. Chasing a ₹12 mismatch daily is not a good use of your life; a ₹12,000 mismatch is worth twenty minutes.

---

## 3.8 Aarav's setup, done

| Account | Type | Balance |
|---------|------|---------|
| HDFC Salary | `Savings` | ₹5,84,300 |
| ICICI Savings | `Savings` | ₹42,100 |
| HDFC Regalia | `Credit Card` | ₹18,400 owed, limit ₹5,00,000, closes 18th, due 8th |
| Cash | `Wallet` | ₹3,500 |

Sidebar total: **₹6,11,500**. The credit card is subtracted, because he owes it.

That ₹5.84 lakh sitting in his savings account is close to his ₹5.4 lakh emergency fund target — a fact he didn't know before this exercise. In [chapter 7](07-budgets-and-goals.md) he'll formalise it as a goal, and then move the surplus somewhere more productive.

---

**Next:** [Chapter 4 — Recording transactions](04-transactions.md)
