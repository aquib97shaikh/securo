# 6. Categories and rules

Categories turn a list of transactions into an answer. Rules mean you only have to categorise each kind of spending once, ever.

This is the highest-leverage chapter in the guide. An hour here saves you ten minutes every month forever, and it's the difference between a system you keep using and one you abandon in March.

---

## 6.1 What Securo starts you with

A new workspace comes with **6 category groups** and **16 categories**:

| Group | Categories inside it |
|-------|---------------------|
| `Housing` | `Housing` |
| `Food & Dining` | `Food & Dining`, `Groceries` |
| `Transport` | `Transport` |
| `Lifestyle` | `Health`, `Leisure`, `Education`, `Personal Care` |
| `Other` | `Subscriptions`, `Shopping`, `Donations`, `Taxes & Fees`, `Transfers`, `Investments`, `Other` |
| `Income` | `Salary & Income` |

Groups exist purely to organise the list — with forty categories, a flat dropdown becomes unusable.

Two of these defaults behave specially: `Transfers` and `Investments` are marked **treat as transfer**, which is explained in 6.4.

---

## 6.2 How many categories should you have?

The temptation is to make sixty. Resist it.

**Too few** and the answer is useless: a single `Food` category worth ₹20,000 tells you nothing you can act on.

**Too many** and you stop maintaining it. If you have to decide whether a Blinkit order was `Groceries`, `Snacks`, `Household Supplies` or `Convenience`, you'll eventually pick `Other` for everything.

**The right test:** would you actually behave differently based on knowing this category separately? If splitting `Groceries` from `Eating Out` would change a decision, split them. If splitting `Coffee` from `Eating Out` wouldn't, don't.

**Fifteen to twenty-five** categories suits most people. Start at the low end and split one only when a category gets big enough to be interesting.

---

## 6.3 A category set for Indian salaried life

Here's what Aarav ends up with. Adapt it — this is a starting point, not a prescription.

**Group `Housing`** — `Rent`, `Utilities` (electricity, water, gas), `Internet & Phone`, `Home Help` (cook, cleaner, driver), `Home Maintenance`

**Group `Food & Dining`** — `Groceries` (BigBasket, Blinkit, the local kirana), `Eating Out` (restaurants and cafés), `Food Delivery` (Swiggy, Zomato — split from `Eating Out` deliberately, because for most people it's the bigger and more surprising number)

**Group `Transport`** — `Fuel`, `Cabs & Auto` (Uber, Ola, Rapido), `Public Transport` (metro, bus), `Vehicle Maintenance` (servicing, insurance, FASTag)

**Group `Lifestyle`** — `Health` (doctors, medicines, hospitals), `Fitness` (gym, sports), `Shopping` (clothes, electronics, general), `Entertainment` (movies, events, games), `Subscriptions` (Netflix, Spotify, iCloud, YouTube Premium), `Personal Care` (salon, grooming), `Travel` (holidays, flights, hotels)

**Group `Family & Obligations`** *(a new group worth adding)* — `Family Support` (money to parents), `Gifts & Festivals` (Diwali, weddings, birthdays), `Donations`

**Group `Financial`** *(new)* — `Insurance Premiums`, `Taxes & Fees` (advance tax, bank charges), `Investments` *(treat as transfer)*, `Transfers` *(treat as transfer)*

**Group `Income`** — `Salary`, `Bonus`, `Interest & Dividends`, `Reimbursements`, `Other Income`

`Gifts & Festivals` deserves its own line rather than being buried in `Shopping`. In India it is a genuine recurring expense — Diwali, weddings, birthdays — and seeing the annual total is often the moment people start a sinking fund for it ([chapter 1](01-money-basics.md)).

### Creating them

**`Add Group`** asks for `Name`, `Position` (sort order), `Color` and `Icon`.

**`Add Category`** asks for `Name`, `Group`, `Color`, `Icon`, and two checkboxes covered below.

**Cleaning up the defaults:** you can't delete the built-in categories, but you can hide them. The eye icon on each gives you **`Hide default category`**. Hidden categories disappear from pickers and stop being assigned by rules, but transactions already using them keep working — so your history and old reports don't break. The page explains this at the top.

---

## 6.4 The two checkboxes that confuse everyone

**`Treat as transfer`** — *"Transactions in this category won't count as income or expense in reports. Use this for movements between your own accounts (investments, savings deposits, loan repayments)."*

This is the important one. When you put ₹45,000 into a mutual fund, you haven't spent it — you still own it, it just changed form. If that counted as an expense, your savings rate would read 0% no matter how much you saved.

Use it for: SIP contributions, PPF deposits, FD creation, moving money to your brokerage, credit card bill payments.

Transactions in these categories show a **`Transfer`** badge in the list.

**`Ignore this transfer`** — *"Ignored transactions won't show on income or expense reports."*

A stronger version, removing the transaction from reports entirely. Most people never need it. Reach for it only when something is genuinely double-counted.

Categories marked this way show an **`Ignore`** badge.

> Nothing here changes your **account balances** — money that left your account has left it either way. These flags only affect how reports classify the movement.

---

## 6.5 Rules: the part that saves your time

A rule watches for a pattern in incoming transactions and acts on it. `Description contains "SWIGGY"` → `Set category` to `Food Delivery`. Once written, every Swiggy order for the rest of your life categorises itself.

Go to **`Rules`** and click **`Add`**.

### Conditions

You get eight fields to match on:

| Field | Notes |
|-------|-------|
| `Description` | What you'll use 90% of the time |
| `Imported payee` | The raw payee text from the import, before any cleanup |
| `Notes` | |
| `Amount` | |
| `Type` | `Expense (debit)` or `Income (credit)` |
| `Account` | |
| `Payee` | |
| `Date` | |

Text fields offer `contains`, `does not contain`, `equals`, `not equal to`, `starts with`, `ends with` and `regex`. Numbers and dates offer `=`, `>`, `>=`, `<`, `<=`. Account and payee offer `is` and `is not`.

Use **`contains`** for almost everything. Bank narrations are messy — a Swiggy order might arrive as `UPI-SWIGGY-SWIGGY@YBL-HDFC0000123-4567-PAYMENT`. `contains "SWIGGY"` catches it; `equals` never will.

Combine conditions with **`AND`** / **`OR`**, and nest them in groups for complicated cases.

### Actions

| Action | What it does |
|--------|--------------|
| `Set category` | The main one |
| `Set description` | Rewrite that narration into something human |
| `Set payee` | Assign a payee automatically |
| `Append tags/notes` | Add a `#tag` |
| `Ignore transaction` | Drop it from reports |

`Set description` is underrated. A rule that turns `UPI-SWIGGY-SWIGGY@YBL-HDFC0000123-4567` into `Swiggy` makes your entire transaction list readable, and takes one extra field.

### The rest of the form

**`Name`** — describe what it does, like `Swiggy → Food Delivery`.

**`Priority`** — a number. When several rules match the same transaction, priority decides who wins. Leave it at `0` unless you need a specific order; then give the specific rules higher priority than the general ones. Rules show a `p:5` badge in the list.

**`Active rule`** — untick to disable without deleting.

### Preview before saving

Turn on **`Preview`** and Securo shows how many existing transactions match — `23 matches · 23 would change` — and lists them. This catches over-broad rules before they do damage. A rule matching `contains "PAY"` will hit far more than you intended, and the preview shows you that immediately.

### Applying to what you already have

A new rule has **`Apply matching actions to existing transactions`** ticked by default, so it cleans up your history as well as future imports.

Underneath is **`Also replace existing categories`**, off by default. Leave it off unless you're deliberately re-categorising — with it on, the rule overwrites categories you set by hand.

---

## 6.6 A starter rule set

Securo ships **`Rule Packs`** for Brazil, the United States, Europe and the United Kingdom. **There is no India pack**, so you'll write your own. Here's Aarav's, which covers most Indian salaried spending.

All of these use `Description` `contains`, and all set a category:

| Match | Category |
|-------|----------|
| `SWIGGY`, `ZOMATO`, `EATCLUB` | `Food Delivery` |
| `BLINKIT`, `ZEPTO`, `BIGBASKET`, `DUNZO`, `INSTAMART` | `Groceries` |
| `UBER`, `OLA`, `RAPIDO` | `Cabs & Auto` |
| `IRCTC`, `BMTC`, `METRO` | `Public Transport` |
| `INDIAN OIL`, `HP PETROL`, `BHARAT PETRO`, `FASTAG` | `Fuel` |
| `AMAZON`, `FLIPKART`, `MYNTRA`, `AJIO`, `NYKAA` | `Shopping` |
| `NETFLIX`, `SPOTIFY`, `PRIME`, `HOTSTAR`, `APPLE.COM/BILL`, `GOOGLE` | `Subscriptions` |
| `AIRTEL`, `JIO`, `VODAFONE`, `ACT FIBERNET`, `BSNL` | `Internet & Phone` |
| `BESCOM`, `ELECTRICITY`, `GAS`, `WATER BOARD` | `Utilities` |
| `APOLLO`, `PHARMEASY`, `1MG`, `NETMEDS`, `PRACTO` | `Health` |
| `CULT.FIT`, `CULTFIT`, `GYM` | `Fitness` |
| `ZERODHA`, `GROWW`, `KUVERA`, `SIP`, `MUTUAL FUND` | `Investments` *(transfer)* |
| `LIC`, `HDFC LIFE`, `STAR HEALTH`, `POLICYBAZAAR` | `Insurance Premiums` |
| `MAKEMYTRIP`, `GOIBIBO`, `INDIGO`, `AIR INDIA`, `OYO`, `AIRBNB` | `Travel` |
| `BOOKMYSHOW`, `PVR`, `INOX` | `Entertainment` |

Plus two for income, matching on `Description` `contains` your employer's name with `Type` `is` `Income (credit)` → `Salary`, and `contains "INT.PD"` or `"INTEREST"` → `Interest & Dividends`.

Don't write all thirty at once. Import a month of statements, filter to `Uncategorized`, sort by description, and write a rule for whatever appears most. Ten rules will cover 80% of your transactions. Add more as new merchants show up.

**Building a rule from a transaction you're looking at:** open it and click **`Create Rule`** — the conditions are pre-filled from that transaction. This is usually faster than starting from a blank rule.

---

## 6.7 Maintaining rules

**`Reset and reapply`** clears rule-assigned categories across your transactions and runs every active rule again. Use it after a significant rewrite of your rule set. It asks for confirmation, because it will overwrite manual categorisations that a rule also matches.

**`Export`** downloads your rules as `securo-categorization-rules.json`. Worth doing once you've built a set you like — it's a small file and it represents real work. **`Import`** loads one back, but note it *replaces* your current rules rather than merging, and warns you accordingly.

**Rules only run on import and when you tell them to.** A transaction you type in manually and categorise by hand won't be touched.

---

## 6.8 The monthly cleanup

After each import:

1. Go to **`Transactions`**, filter `Category` = `Uncategorized`
2. Sort by description so similar items group together
3. For anything appearing more than twice, write a rule — you'll never see it again
4. For genuine one-offs, tick them and use the bulk category picker
5. Aim to finish at zero

The dashboard tracks this for you with `12 transactions need categorizing` and a `Categorize now →` link. Watching that hit zero is oddly satisfying, and it's the single best indicator that your setup is healthy.

---

**Next:** [Chapter 7 — Budgets and goals](07-budgets-and-goals.md)
