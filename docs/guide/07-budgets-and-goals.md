# 7. Budgets and goals

A **budget** is a monthly ceiling on a category. A **goal** is a target amount you're working towards. Budgets control the present; goals describe the future.

Do not do either of these in your first month. You need real data first, and setting limits by guessing produces numbers you'll ignore by week two.

---

## 7.1 Wait for three months of data

The single most common way to fail at budgeting is to invent limits, blow through them immediately, and conclude that budgeting doesn't work for you.

Your first budget should be **a description of what you already spend**, not a wish. Once it's accurate, you can lower one number at a time and actually hit it.

So: import three months of statements, categorise them, and only then come back here. If you're impatient, one month is enough to start — just expect the first version to be wrong.

**Where to find your own numbers:**

- **Dashboard → `Spending by Category`**, stepping back through months with the `‹` `›` selector
- **Reports → `Income vs Expenses`** with the range set to `6M`, which shows how each category moves month to month

Look at three months of each category and take something close to the average, rounded up slightly. Aarav's `Food Delivery` came in at ₹9,200 / ₹14,800 / ₹11,400 — he sets ₹12,000, not ₹9,000, because ₹9,000 is a fantasy and would fail in month one.

---

## 7.2 Creating budgets

Go to **`Budgets`**. The page title is the month you're looking at, like `August 2026`, and you move between months with `‹` and `›`.

Click **`Add Budget`**:

| Field | What to enter |
|-------|---------------|
| `Category` | Which category to cap |
| `Repeat every month` | Tick this. See below |
| `Limit` | The monthly ceiling |

**`Repeat every month`** makes the budget a template: it applies to the selected month and every month after it, until you change or delete it. Without it, you'd be re-entering twenty budgets every month.

You can still override a single month — set a different budget for just December and it takes precedence for December only, while the recurring one resumes in January. That's how you handle Diwali.

When editing an existing budget, only `Limit` is shown; category and repeat can't be changed.

### Budget the things you can control

Don't budget all 25 categories. Budget the ones where your behaviour actually varies.

Aarav budgets seven: `Food Delivery` ₹12,000, `Eating Out` ₹6,000, `Shopping` ₹12,000, `Cabs & Auto` ₹4,000, `Entertainment` ₹3,000, `Groceries` ₹6,000, `Subscriptions` ₹4,000.

He doesn't budget `Rent` (fixed), `Insurance Premiums` (fixed), `Family Support` (fixed by agreement), or `Salary` (income, not spending). Capping something you can't change generates noise, not insight.

---

## 7.3 Two limitations to know about

**Budgets are per category, not per group.** You can't set ₹20,000 across all of `Food & Dining` and let it distribute. Set individual limits.

**There is no rollover.** Spend ₹8,000 of a ₹12,000 budget and next month is still ₹12,000, not ₹16,000. If you're used to envelope-style apps, this will feel wrong.

The workaround for genuinely lumpy expenses — the ones where saving up matters — is to use a **goal** instead of a budget. Aarav's ₹10,000/month travel money isn't a budget line; it's a goal he adds to monthly and draws down when he books a trip. Section 7.6 covers this.

---

## 7.4 Where you see budget progress

Not on the Budgets page, which just lists your limits. Progress lives on the **dashboard**, in the **`Spending by Category`** card. Each category shows a bar with `of ₹12,000` underneath, colour-coded:

| Colour | Meaning |
|--------|---------|
| Green | Under 80% |
| Amber | 80–100% — slow down |
| Red | Over 100% |

There's also a small `↑`/`↓` badge comparing the category to last month.

Two things to understand about that percentage:

**It includes projections.** The figure is *actual spending plus expected recurring transactions for the rest of the month*. So on the 5th, a category with a ₹6,000 recurring bill due on the 25th already shows that ₹6,000. This is deliberate and more useful than pure actuals — it tells you what the month will look like, not just what's happened.

**Nothing will alert you.** Securo sends no emails, no push notifications, nothing. If you don't open the dashboard, you won't know you're at 140%. Check it weekly.

---

## 7.5 The month you blow the budget

You will. Here's what to do about it, in order of how likely each is to be the right answer:

**1. Was the budget wrong?** If you set `Groceries` at ₹4,000 and you've spent ₹6,000 three months running, the budget is wrong, not you. Raise it and cut elsewhere.

**2. Was it a one-off?** A medical emergency or a wedding gift isn't a pattern. Note it and move on. This is exactly what the unallocated slack from [chapter 1](01-money-basics.md) exists for.

**3. Is it a genuine trend?** `Food Delivery` creeping from ₹9,000 to ₹12,000 to ₹15,000 over three months is a habit forming. This is the case where the budget did its job — it caught something you wouldn't have noticed. Now you get to decide whether you care.

**What not to do:** delete the budget so the red bar goes away, or give up on the whole system because one category failed. Overspending one category in one month is not failure. It's the system working.

---

## 7.6 Goals

Go to **`Goals`** and click **`Add Goal`**:

| Field | What to enter |
|-------|---------------|
| `Name` | `Emergency Fund` |
| `Target Amount` | `540000` |
| `Currency` | `INR` |
| `Target Date` | When you want it done |
| `Tracking Type` | How progress is measured — see below |
| `Icon` | Click `Choose icon & color` |

### The five tracking types

This choice determines whether you update progress manually or Securo works it out.

| Type | How `current` is calculated | Best for |
|------|------------------------------|----------|
| `Manual` | A number you type in and update yourself | Anything that doesn't map to a single account or asset |
| `Linked Account` | The live balance of one account | An emergency fund kept in a dedicated savings account |
| `Linked Asset` | The current value of one asset | "Get my PPF to ₹10 lakh" |
| `Wallet` | Combined value of every asset in one wallet | "Reach ₹25 lakh invested across my equity portfolio" |
| `Net Worth` | All open account balances plus all asset values | "Reach my first ₹1 crore" |

**Prefer the automatic ones.** A `Manual` goal is only as current as the last time you remembered to update it, and people stop remembering by month three. If you can attach a goal to an account, an asset or a wallet, do.

The practical implication: if you're serious about an emergency fund goal, **open a separate savings account for it** and link the goal to that account. It updates itself, and the money stops blending into your spending balance. That psychological separation does more work than the tracking does.

### What the goal shows you

Progress as `₹5,84,300 / ₹5,40,000` with a percentage bar, and — if you set a target date — a **`/mo`** figure telling you how much you need to put aside each month to make it. That number is the useful one. It converts "I'd like ₹10 lakh someday" into "₹28,000 a month, and I currently save ₹18,000," which is a decision rather than a wish.

Goals also carry an on-track badge: `Ahead`, `On Track`, `Behind`, `Overdue` or `Achieved`.

### Updating a manual goal

There's no "add contribution" button. Open the goal with the pencil icon, change **`Current Amount`**, and **`Save`**. Do it monthly, at the same time as your import.

### Goal states

Filter pills across the top: `Active`, `Completed`, `Paused`, `Archived`, `All`.

`Mark Complete` when you get there. `Pause` when life happens and you want to stop the "behind schedule" nag without deleting anything — this is a genuinely good feature and using it is not admitting defeat. `Archive` for things that no longer apply.

---

## 7.7 Aarav's goals

| Goal | Target | Tracking | Notes |
|------|--------|----------|-------|
| Emergency Fund | ₹5,40,000 | `Linked Account` → a dedicated savings account | Six months of spending |
| Travel Fund | ₹1,20,000 | `Manual` | Adds ₹10,000/month, draws down when he books |
| First ₹50 lakh invested | ₹50,00,000 | `Wallet` → his equity wallet | The long-term one |
| New laptop | ₹1,50,000 | `Manual` | Target date next June, so the `/mo` figure tells him if he's on pace |

The travel fund is the sinking fund from [chapter 1](01-money-basics.md) in practice. Because there's no budget rollover, a goal is the right container for money that accumulates and then gets spent in one go.

---

## 7.8 Budget or goal?

| Situation | Use |
|-----------|-----|
| Spending you want to cap each month | **Budget** — `Food Delivery` at ₹12,000 |
| Money accumulating for a future purchase | **Goal** — ₹1.2 lakh for a holiday |
| A fixed bill you can't change | **Neither** — make it a recurring transaction ([chapter 8](08-recurring-and-investments.md)) |
| Building an emergency fund | **Goal**, linked to a real account |
| An irregular annual expense | **Goal** if you save up for it, **budget** in the month it lands if you can absorb it |

---

**Next:** [Chapter 8 — Recurring bills and investments](08-recurring-and-investments.md)
