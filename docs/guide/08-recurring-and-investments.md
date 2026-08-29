# 8. Recurring bills and investments

Two features that together let Securo answer "what will my balance be at the end of the month?" and "what am I actually worth?"

---

# Part 1: Recurring transactions

Your salary, rent, SIPs, insurance premiums and EMIs all happen on a schedule. Tell Securo the schedule once and it handles the rest — including showing you money that hasn't moved yet.

Go to **`Recurring`** in the sidebar.

## 8.1 Setting one up

Click **`Add Recurring`**:

| Field | What to enter |
|-------|---------------|
| `Description` | `Monthly SIP - Nifty Index Fund` |
| `Amount` / `Currency` / `Type` | Amount, `INR`, and `Expense` or `Income` |
| `Frequency` | `Monthly`, `Quarterly`, `Weekly` or `Yearly` |
| `Day of month` | Appears for monthly and quarterly. The date it hits |
| `Weekend adjustment` | See below |
| `Start date` / `End date (optional)` | Leave the end date blank for something ongoing |
| `Category` / `Account` | |
| `Generate transactions automatically` | See 8.2 |

Note there is **no fortnightly option**. If you're paid every two weeks, use `Weekly` and halve the amount, or add the transactions manually.

**`Weekend adjustment`** handles the fact that bank debits don't happen on Sundays. Options are `No adjustment`, `Friday before the weekend` and `Monday after the weekend`. For an auto-debited SIP or EMI, `Monday after the weekend` matches what banks actually do.

## 8.2 Auto-generate: on or off?

The **`Generate transactions automatically`** checkbox controls whether Securo creates a real transaction when the date arrives, or just shows it as upcoming. Its help text: *"Create a transaction each time this bill is due. Turn off to wait for the real charge (e.g. from bank sync) and only show it as upcoming until then."*

**For Indian users importing statements, leave it ON.**

The reasoning: with it off, you'd see the bill as a projection and then wait for the imported statement to fill it in — which works nicely with automatic bank sync, but you don't have that. Your import might be three weeks late.

With it on, Securo creates the transaction on the due date. When you later import the statement containing the real charge, Securo **matches them and upgrades the placeholder in place** rather than creating a duplicate. It matches on account, amount, currency, type, a date window, and description similarity.

That matching isn't perfect. If your rent is ₹25,000 on the 5th and it actually went out as ₹25,000 on the 7th, it'll match. If the amount changed to ₹26,500, it may not, and you'll have both a placeholder and a real transaction. Delete the placeholder when you spot it — the monthly reconciliation in [chapter 5](05-import-statements.md) is where you'll notice.

**`Generate Pending`** in the page header creates any transactions that were due but haven't been generated yet. Useful after you've been away.

**`Backfill until today`** fills history from the start date through today for one recurring item. Use it when you add a bill that started in the past, or after you change the start date earlier. It runs once up to today; later dates wait for their due date. You can check the box when saving, or use the backfill action on the row.

## 8.3 What "projected" means

Transactions that haven't happened yet appear with a violet **`Projected`** badge, and they're what makes the dashboard's **`Projected Balance`** meaningful: *this is what you'll have at month end after everything you already know about.*

You'll see projections on:

- The **dashboard**, in `Period Transactions` (list or calendar view)
- **Account detail pages**, as faded rows

You will **not** see them on the Transactions page. That page is history only.

Once a real transaction gets linked to a recurring item, it shows a **`Recurring`** badge with the tooltip *"Linked to a recurring bill."* If a link is wrong, open the transaction and click **`Unlink`** — you'll get `Transaction unlinked from the recurring bill`.

## 8.4 Aarav's recurring list

| Description | Amount | Frequency | Day | Type | Category |
|-------------|--------|-----------|-----|------|----------|
| Salary | ₹2,20,000 | Monthly | 1 | Income | `Salary` |
| Contribution to parents | ₹25,000 | Monthly | 2 | Expense | `Family Support` |
| SIP - Nifty index fund | ₹45,000 | Monthly | 5 | Expense | `Investments` *(transfer)* |
| PPF contribution | ₹12,500 | Monthly | 5 | Expense | `Investments` *(transfer)* |
| NPS contribution | ₹10,000 | Monthly | 5 | Expense | `Investments` *(transfer)* |
| Term insurance | ₹1,500 | Monthly | 10 | Expense | `Insurance Premiums` |
| Health insurance | ₹30,000 | Yearly | — | Expense | `Insurance Premiums` |
| Airtel postpaid | ₹1,500 | Monthly | 15 | Expense | `Internet & Phone` |
| Netflix, Spotify, iCloud | ₹1,400 | Monthly | various | Expense | `Subscriptions` |

The investment lines all sit in categories marked **treat as transfer** ([chapter 6](06-categories-and-rules.md)), so ₹67,500 a month of investing doesn't get counted as spending and destroy his savings rate.

The yearly health insurance premium is worth entering even though it's once a year. It shows up in `Cash Flow` forecasts, so the month it lands doesn't surprise you.

---

# Part 2: Assets and investments

An **asset** is something you own whose value changes on its own: mutual funds, stocks, EPF, PPF, fixed deposits, gold, property. This is distinct from an account, where money only moves when there's a transaction.

Go to **`Assets`**.

## 8.5 Wallets and holdings

Securo calls the container a **wallet** (not "asset group", despite what the underlying data model calls it). A wallet is a bucket you organise holdings into.

Sensible wallets for an Indian salaried person: `Retirement` (EPF, NPS, PPF), `Equity` (mutual funds, stocks), `Fixed Income` (FDs, debt funds), `Gold`, `Property`.

Click **`New Wallet`**, give it a name and colour.

## 8.6 The three valuation methods — the important decision

When you add an asset, **`Valuation Method`** determines how Securo works out what it's worth. **You cannot change it after saving**, so choose deliberately.

### `Manual`

You type the value in and update it periodically. Expanding the asset row gives you **`Add Value`** (`Amount` and `Date`), a **`Value History`** list, and a **`Value Trend`** chart.

More work, works for everything. **For Indian investors this will be your default**, for reasons that become clear below.

### `Growth Rule`

Value grows automatically at a rate you specify. Fields:

- `Growth Type` — `Percentage` or `Absolute`
- `Growth Rate` — the number
- `Growth Frequency` — `Daily`, `Weekly`, `Monthly` or `Yearly`
- `Growth Start Date`
- `Purchase Price` and `Purchase Date` — the starting value

Securo compounds forward from the purchase price at your chosen rate and fills in the value history automatically.

**Perfect for a fixed deposit.** A ₹2,00,000 FD at 7.1% for five years: `Purchase Price` ₹2,00,000, `Growth Type` `Percentage`, `Growth Rate` `7.1`, `Growth Frequency` `Yearly`. Done — it tracks itself for five years.

The limitation: it grows a single starting amount. It **cannot model ongoing contributions**. So it doesn't fit EPF or a PPF you're still paying into.

### `Market Price`

Fetches live prices by ticker. And here's the thing you need to know before relying on it:

> ### ⚠️ Market prices come from Yahoo Finance
>
> The example tickers Securo offers are `AAPL`, `BTC-USD`, `PETR4.SA` — American, crypto, Brazilian.
>
> **Indian stocks** often work using Yahoo's suffixes: `RELIANCE.NS` and `INFY.NS` for NSE, `.BO` for BSE. **Test it before committing** — type the ticker into the search box on the asset form and see whether a quote comes back. If it does, you're fine.
>
> **Indian mutual funds do not work.** There is no support for AMFI scheme codes, and Yahoo doesn't carry Indian MF NAVs in a form this can use. Since mutual funds are how most Indian salaried people invest, this matters: **track your mutual funds as `Manual` assets.**

For assets where it does work, you get `Ticker`, `Quantity` and `Unit price`, a live quote card, and a **`Refresh price`** button. Prices also refresh on a daily schedule. If you refresh too aggressively you'll hit *"Market data provider is currently rate-limiting. Try again in a minute."*

## 8.7 Setting up Indian investments

Here's the practical mapping. `Type` options available are `Stock`, `ETF`, `Crypto`, `Gold`, `Silver`, `Fund`, `Real Estate`, `Vehicle`, `Valuable`, `Investment` and `Other`.

| What you own | Type | Valuation | How to maintain it |
|--------------|------|-----------|--------------------|
| **EPF** | `Investment` | `Manual` | Update quarterly from the EPFO passbook. Your balance grows by ~₹28,800/month plus interest |
| **PPF** | `Investment` | `Manual` | Update quarterly from your bank |
| **NPS** | `Investment` | `Manual` | Update quarterly from the CRA statement |
| **Equity mutual funds** | `Fund` | `Manual` | Update monthly from your CAS or app. See below |
| **Indian stocks** | `Stock` | `Market Price` if the ticker resolves, else `Manual` | Try `RELIANCE.NS` first |
| **Fixed deposit** | `Investment` | `Growth Rule` | Set it once, forget it |
| **Physical gold** | `Gold` | `Market Price` | Quantity is **grams**. Pick your currency (INR, USD, …). Securo quotes `GOLD` from GoldPriceZ per gram in that currency. Gain/loss updates daily, or tap `Refresh price` anytime |
| **Physical silver** | `Silver` | `Market Price` | Same as gold, with ticker `SILVER` |
| **SGB** | `Valuable` | `Manual` | Sovereign Gold Bonds aren't a Yahoo metal ticker — update from the statement |
| **Property** | `Real Estate` | `Manual` | Update annually. Don't kid yourself upward |
| **Crypto** | `Crypto` | `Market Price` | `BTC-USD` style tickers work |

### The monthly mutual fund update

Since market pricing doesn't work for Indian MFs, here's the routine — five minutes a month:

1. Open your CAMS/KFintech consolidated statement, or your broker app
2. Note the current value of each fund
3. In Securo, expand the asset row and click **`Add Value`**
4. Enter the `Amount` and `Date`

Do it on the same day you import your statements. Consistency matters more than precision — updating on the 1st of every month gives you a clean trend line, even if the value is a day stale.

One simplification worth considering if you have eight funds: create **one `Manual` asset per wallet** rather than per fund. "Equity Mutual Funds" as a single line, updated with the total. Your net worth is just as accurate and the monthly job takes one minute instead of eight. You lose per-fund tracking in Securo — but your broker app already does that better.

## 8.8 The buy/sell ledger

For assets you buy in tranches, Securo tracks each order. The **`Transactions`** tab (or expanding a holding) gives you **`Add transaction`**:

`Holding`, `Type` (`Buy` / `Sell`), `Quantity`, `Unit price`, `Fee`, `Date`, and a computed `Total`.

Securo replays the ledger to compute your `Avg price` and units, using average cost. Selling reduces the cost basis and records a realised gain. Short positions aren't supported — try to sell more than you hold and it tells you so.

The holdings table then shows `Asset`, `Qty`, `Avg price`, `Current`, `Return`, `Total` and `% port.`

This is worth the effort for individual stocks, where knowing your average buy price matters. For a SIP into an index fund it is not — you'd be entering 12 orders a year to compute a number your broker already shows you. Use a single `Manual` asset instead.

## 8.9 The portfolio view

The **`Portfolio Value`** chart plots your holdings over time, with toggles for `By Wallet` / `By Asset` and `Stacked` / `Lines`.

`By Wallet` + `Stacked` is the useful default: it shows your total growing and the mix between retirement, equity and fixed income shifting. Watching the equity band grow relative to the others over two years is the most motivating chart in the app.

## 8.10 What this doesn't cover

**Loans and liabilities.** There is no loan account type and no way to record an outstanding principal. If you have a ₹40 lakh home loan, your net worth in Securo will be overstated by roughly that amount, because the house is an asset and the loan is invisible.

If this applies to you, the workaround is a `Manual` asset with a **negative value** named `Home Loan Outstanding`, updated when you check your loan statement. It's a hack, and it works.

**Your EPF is bigger than you think.** Enter it. At ₹28,800 a month, Aarav's EPF passes ₹3.4 lakh a year without him lifting a finger, and leaving it out of net worth makes the whole picture wrong.

---

**Next:** [Chapter 9 — Reading your reports](09-reports.md)
