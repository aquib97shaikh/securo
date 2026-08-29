# 11. Your first 90 days

Everything in this guide, sequenced. The order matters — each week depends on the one before, and doing them out of order is how people end up with budgets built on guesses.

Roughly two hours in week one, then twenty minutes a week.

---

## Week 1 — Get your money visible

**Time: about 90 minutes.**

- [ ] Log in and pick **`INR`** as your currency at setup. You can't change it later without database access ([ch. 2](02-first-hour.md))
- [ ] Click through the six-step tour
- [ ] Learn the two shortcuts that matter: **Ctrl+K** for search, and the **logo** for the dashboard
- [ ] List every place your money sits — bank accounts, credit cards, cash, payment app balances
- [ ] Add each one under **`Accounts`**, using **today's balance and today's date** ([ch. 3](03-accounts.md))
- [ ] For your credit card: enter what you owe as a **positive** number, and fill in `Credit limit`, `Statement close day` and `Payment due day`
- [ ] Download last month's statement for each account and import it ([ch. 5](05-import-statements.md)) — remember `DD/MM/YYYY` and `Split inflow/outflow columns`
- [ ] Check each account's balance in Securo against your banking app

**Done when:** your `Total Balance` on the dashboard matches reality.

**Don't do yet:** budgets, goals, investments. You don't have enough data.

---

## Week 2 — Make it self-maintaining

**Time: about 60 minutes.** This is the week that determines whether you're still using Securo in six months.

- [ ] Read [chapter 6](06-categories-and-rules.md) properly
- [ ] Set up your categories — 15 to 25, using the Indian set in 6.3 as a starting point
- [ ] Hide the default categories you won't use
- [ ] Mark `Investments` and `Transfers` as **treat as transfer**
- [ ] Filter transactions to `Uncategorized` and sort by description
- [ ] Write a rule for every merchant appearing more than twice. Aim for 10–15 rules
- [ ] Use **`Preview`** on each rule before saving to check it isn't too broad
- [ ] Bulk-categorise whatever's left
- [ ] Fix any transfers recorded as income/expense pairs — select both rows and use **`Link as transfer`** ([ch. 4](04-transactions.md))

**Done when:** the uncategorised count on your dashboard is zero.

---

## Week 3 — Automate what repeats

**Time: about 45 minutes.**

- [ ] Add every recurring item under **`Recurring`** ([ch. 8](08-recurring-and-investments.md)): salary, rent, SIPs, insurance, subscriptions, EMIs, phone, internet
- [ ] Leave `Generate transactions automatically` **on**
- [ ] Include yearly items like insurance premiums
- [ ] Check the dashboard — `Projected Balance` should now be meaningful
- [ ] Look at **Reports → `Cash Flow`** with `Include estimate` on

**Done when:** your recurring list accounts for most of your fixed monthly spending, and the cash flow forecast looks plausible.

---

## Week 4 — Count what you own

**Time: about 60 minutes.** Gathering the numbers takes longer than entering them.

- [ ] Find your EPFO passbook balance
- [ ] Find your PPF, NPS and FD balances
- [ ] Get your mutual fund total from your CAS or broker app
- [ ] Create wallets under **`Assets`**: `Retirement`, `Equity`, `Fixed Income`, `Gold`
- [ ] Add each holding, using the mapping table in [chapter 8](08-recurring-and-investments.md) — mostly `Manual`, `Growth Rule` for FDs
- [ ] Add a negative manual asset for any loan you have, since loans aren't otherwise tracked
- [ ] Look at **Reports → `Net Worth`**

**Done when:** you know your net worth. For many people this is the first time, and the number is usually higher than expected — EPF adds up quietly.

---

## Month 2 — Watch, don't act

You now have a working system with one month of clean data. One month is not a pattern, so resist the urge to set budgets yet.

**Weekly, 15 minutes:**

- [ ] Import the week's transactions, or add cash spends
- [ ] Clear the uncategorised list
- [ ] Add a rule for anything new

**End of month, 30 minutes:**

- [ ] Import full statements, verify balances match
- [ ] Update your manual asset values
- [ ] Download a **`Backup`** ([ch. 10](10-sharing-and-safety.md))
- [ ] Look at `Savings Rate`, `Spending by Category` and `Money Map` — but just look

**What you're likely to notice:** at least one category is two or three times what you'd have guessed. For most people it's food delivery, ride-hailing, or subscriptions they forgot they had. Note it. Don't fix it yet.

---

## Month 3 — Set your targets

Now you have two to three months of real data, which is enough to plan against.

**Week 9 — budgets:**

- [ ] Look at each category's average over the past months ([ch. 7](07-budgets-and-goals.md))
- [ ] Set budgets on the 5–8 categories where your behaviour actually varies
- [ ] Set them at roughly your actual average, not an aspirational number
- [ ] Tick `Repeat every month`
- [ ] Skip budgets on fixed costs and income

**Week 10 — goals:**

- [ ] Work out your emergency fund target: six months of total spending, using your real figure
- [ ] Open a separate savings account for it if you haven't, and link a `Linked Account` goal to it
- [ ] Add a goal for anything you're saving towards, with a `Target Date` so you get the `/mo` figure
- [ ] Set up sinking funds as goals — travel, festivals, phone replacement

**Week 11 — the honest review:**

- [ ] Calculate your savings rate from the dashboard
- [ ] Compare it against the framework in [chapter 1](01-money-basics.md)
- [ ] Pick **one** category to reduce. One. Not five
- [ ] Check the order of operations in 1.5 — insurance in place? Emergency fund funded? Credit cards clear?
- [ ] If your emergency fund isn't done, redirect money towards it before increasing investments

**Week 12 — lock it in:**

- [ ] Export your rules JSON
- [ ] Download a backup
- [ ] Confirm the database itself is being backed up
- [ ] Put a recurring calendar reminder for your monthly review — nothing in Securo will remind you
- [ ] Consider passkeys for faster login

---

## After 90 days

**Weekly (15 min):** import, categorise, glance at the dashboard.

**Monthly (30 min):** full statement import, balance check, update asset values, review savings rate and budgets, download a backup.

**Quarterly (45 min):** net worth trend, income vs expenses over 6 months, category trends, money map, rebalance budgets against reality.

**Annually (2 hours):** compare year over year, recalculate the emergency fund against current spending, review insurance cover, rebuild budgets from actuals rather than from last year's budgets, check your investment allocation still matches your plan.

---

## What "working" looks like

You'll know the system has taken hold when:

- You can answer "how much did I spend on X last year?" in under a minute
- Your uncategorised count is usually zero
- You know your net worth to the nearest ₹50,000 without looking
- A large purchase prompts you to check `Cash Flow` before deciding
- Your savings rate has moved in the right direction

None of that requires discipline in any heroic sense. It requires fifteen minutes a week and a system that does the boring parts for you.

---

## If you fall off

You will, at some point. A busy month, travel, something happening at work, and suddenly it's been eight weeks.

**Don't try to reconstruct the missing period transaction by transaction.** That's the abandonment trap — the backlog feels like homework, so you keep postponing it, and eventually you stop opening the app at all.

Instead:

1. Import the statements for the missing period all at once. Your rules will categorise most of it
2. Bulk-categorise the rest without agonising — `Other` is a perfectly acceptable answer for a two-month-old ₹400 transaction
3. Correct each account's balance to today's actual figure
4. Carry on from today

Two hours of effort, and you're current. The data for those weeks will be slightly rough. It does not matter. A system you return to after lapsing beats a perfect system you abandoned.

---

**Next:** [Chapter 12 — FAQ and glossary](12-faq-and-glossary.md)
