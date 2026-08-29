# 9. Reading your reports

Charts are only useful if you know what question they answer. This chapter goes through each one, what it means, and what to actually do with it.

---

## 9.1 The dashboard

Click the **Securo** logo to get here. It answers: *how is this month going?*

The month selector at the top (`‹ August 2026 ›`) scopes almost everything, so you can step back through previous months. Two exceptions: goals aren't month-scoped, and the uncategorised count is always all-time.

### `Savings Rate`

**(Income − Expenses) ÷ Income**, for the selected month.

The most important number in the app. From [chapter 1](01-money-basics.md): this is the lever you control, and moving it up a few points a year matters more than any investment choice you'll make.

It only works if your transfers are set up correctly. If your SIP is recorded as an expense rather than a transfer, this reads far too low. If it shows something implausible, that's the first thing to check ([chapter 6](06-categories-and-rules.md)).

### `Total Balance`

Every open account balance plus your invested assets, converted to rupees. Credit card debt is subtracted.

Beneath it, when they differ, you'll see:

- **`Projected Balance`** — what you'll have at month end once known recurring transactions have run. If this is much lower than your current balance, you have bills coming
- **`Invested assets`** — how much of the total is investments rather than cash. Not an addition to the total; a breakdown of it

### `Monthly Income` and `Monthly Expenses`

Posted transactions for the month, excluding transfers, ignored transactions and opening balances. Both are clickable — they drill through to the underlying transactions, which is the fastest way to answer "why was August so expensive?"

If a projection exists, `Projected Income` and `Projected Expenses` appear underneath.

### The spending pace line

In the current month you'll see something like *"At this pace, you'll spend ₹96,400 by month end."* It's simple arithmetic — spending so far divided by days elapsed, times days in the month — which makes it unreliable in the first week and quite accurate by the middle of the month.

### `{{count}} transactions need categorizing`

Your to-do list, with a `Categorize now →` link. Keep it at zero. When it isn't zero, every other number on this page is slightly wrong.

### `Spending by Category`

Bars per category, sorted by size, with budget progress if you've set budgets ([chapter 7](07-budgets-and-goals.md)) and an `↑`/`↓` badge comparing to last month.

Read the **top three bars**. That's where your money goes, and it's where any meaningful change has to come from. Cutting a ₹400 category by half saves ₹200; cutting a ₹15,000 category by 20% saves ₹3,000.

### `Balance Flow`

Your account balance day by day, this month against last month, with a `Period change` figure.

The shape tells a story. A cliff on the 5th is your SIPs and bills going out. A steady decline through the month is normal. A line that flattens near zero before payday means you're living paycheck to paycheck regardless of what your savings rate says — which happens when your savings are all locked in and you have no buffer.

### `Goals Progress` and `Period Transactions`

Goals with their bars and on-track status. Then the month's transactions as a `List view` or `Calendar view`.

The calendar view is worth a look occasionally. Spending clusters visually — most people find their weekends cost multiples of their weekdays, which is obvious in hindsight and invisible in a list.

---

## 9.2 Reports

Four tabs under **`Reports`**. The dashboard is about this month; these are about trends.

Most tabs share range buttons (`6M`, `YTD`, `1Y`, `2Y`) and interval buttons (`D`, `W`, `M`, `Y`). For anything over three months, use `M` — daily intervals over a year are noise.

---

## 9.3 `Net Worth`

**The question: am I getting wealthier?**

The single best measure of financial progress, because it captures everything at once. You can have a great month for income and a worse net worth if you spent it all.

**`Net Worth · Over Time`** plots the total. **`Composition`** breaks it into `Net Worth`, `Assets & Accounts` and `Liabilities`. **`Evolution`** shows stacked bars of `Accounts`, `Assets` and `Liabilities` with net worth as a dashed line over them.

### How Securo calculates it

| Counted as an asset | Counted as a liability |
|---------------------|------------------------|
| Open accounts with a positive balance (excluding credit cards) | Credit card balances, always |
| All your assets — investments, gold, property | Any account with a negative balance |

**Net worth = positive accounts + assets − liabilities.**

Two caveats from [chapter 8](08-recurring-and-investments.md) worth repeating: **loans aren't tracked**, so if you have a home loan your net worth is overstated unless you've added a negative manual asset. And your net worth is only as current as your last asset update — if you haven't touched your mutual fund values in six months, the line is flat for reasons that have nothing to do with the market.

### What to look for

Direction over a year, not month to month. A dip because markets fell is not a problem. A dip because you spent more than you earned is.

The **`Evolution`** view is the interesting one over a couple of years: watch the `Assets` band grow relative to the `Accounts` band. That's the transition from *saving money* to *having investments*, and it's what compounding looks like early on.

---

## 9.4 `Income vs Expenses`

**The question: am I earning more than I spend, consistently?**

Bars for `Income` and `Expenses` per period, lighter bars for projections, and a dashed **`Net Income`** line. Below it, a composition breakdown with `Net` / `By Income` / `By Expenses` toggles, and **`Category Trends`** showing a sparkline per category.

### What to look for

**Is the net line consistently above zero?** If not, nothing else matters — fix that first.

**Is the gap widening?** As your salary rises, expenses should rise more slowly. If the two bars grow together, you have lifestyle inflation, which is the mechanism by which people earn twice as much and save the same amount.

**`Category Trends` is the most under-used view in the app.** A single month of high `Food Delivery` is noise. Six months of steady increase is a habit forming, and you can see it here while it's still small enough to change easily.

---

## 9.5 `Cash Flow`

**The question: will I have enough money next month?**

Forward-looking, unlike the others. Ranges are `3M`, `6M`, `12M` into the future.

An area chart of your balance: solid where it's history, dashed where it's **`Forecast`**. A `Today` marker separates them. The tooltip shows `Balance`, `Inflow` and `Outflow`. There's also an `Inflow vs Outflow` stacked bar chart.

The forecast is built from your recurring transactions ([chapter 8](08-recurring-and-investments.md)), so its quality depends entirely on how completely you've entered them. With three recurring items it's useless; with twenty it's genuinely predictive.

### `Include estimate`

A toggle that adds an estimate of your *non-recurring* spending, based on your historical average of up to 12 months, instead of relying only on recurring rules.

**Turn it on.** Without it, the forecast assumes you'll spend nothing outside your scheduled bills, which is wildly optimistic. With it, you get something closer to reality.

### What to use it for

Two concrete questions. *Can I afford a ₹1.5 lakh trip in December?* — look at the projected balance for December and see whether it stays comfortably above your emergency fund floor. And *when will my balance dip lowest?* — the trough is when a large unexpected expense would actually hurt.

---

## 9.6 `Money Map`

**The question: where did my money actually go?**

A Sankey diagram. Income sources flow in from the left, through a central `Cash Flow` hub, and out to the right.

| Element | Meaning |
|---------|---------|
| Left nodes | Income categories — salary, interest, reimbursements |
| Centre | The `Cash Flow` hub, where everything pools |
| Right, red | Expense categories |
| Right, teal | `Investments` — categories marked *treat as transfer* |
| Right, green | `Surplus` — income minus expenses minus investments |
| Amber, left | `Deficit` — appears only if you spent and invested more than you earned |

The widths are proportional, so this is the one report where the picture does the work. A thick red band to `Food Delivery` next to a thin teal band to investments communicates something no table does.

Ranges are `30D`, `3M`, `6M`, `YTD`, `1Y`. Use `1Y` — a single month is too noisy for this to be interesting.

Show this one to yourself once a quarter. It's the report most likely to change behaviour, because it makes proportion visible in a way that percentages don't.

---

## 9.7 Filtering by collection

A **collection** is a named bundle of accounts and wallets. The bar at the top of the content area reads `Viewing` `All accounts`; pick a collection and the dashboard, transactions, reports and assets all scope to it.

Useful when you want to separate concerns — freelance income from salary, or joint household accounts from personal ones.

Two behaviours worth knowing: a collection containing only wallets and no accounts will only load the `Net Worth` tab, since the other three need account transactions. And group-split adjustments are turned off while a collection filter is active, so you see the raw numbers for those accounts.

[Chapter 10](10-sharing-and-safety.md) covers creating them.

---

## 9.8 A review routine that takes ten minutes

**Monthly**, right after your import:

1. Dashboard — is the uncategorised count zero?
2. `Savings Rate` — how does it compare to last month?
3. `Spending by Category` — anything red, anything surprising in the top three?
4. Any goal marked `Behind`?

**Quarterly**, add twenty minutes:

1. `Net Worth`, range `1Y` — is the trend up?
2. `Income vs Expenses`, range `6M` — is the gap widening?
3. `Category Trends` — any category creeping upward?
4. `Money Map`, range `1Y` — does the shape match what you intend?
5. Update your manual asset values before doing any of this, or the net worth chart lies to you

**Annually:** compare this year's total income and spending to last year's, revisit your savings rate target, check your emergency fund still covers six months of your *current* spending, and rewrite your budgets from actuals rather than from last year's budgets.

---

**Next:** [Chapter 10 — Sharing and staying safe](10-sharing-and-safety.md)
