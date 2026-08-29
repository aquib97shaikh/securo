# 2. Your first hour in Securo

This chapter gets you logged in and oriented. By the end you will know what every page is for, which means you will stop clicking around wondering where things are.

**Before you start:** Securo needs to be running. If you see a login page in your browser, you're ready. If not, whoever set up the server needs to start it first — the project [README](../../README.md) has the installation commands.

---

## 2.1 Creating your login

The very first person to use a fresh Securo installation sees a special screen at `/setup` that creates the admin account. If someone else already set it up, you'll see the normal `Login` page instead and they'll need to create an account for you.

The setup screen says **`Welcome to Securo`** and asks for these, in order:

| Field | What to enter |
|-------|---------------|
| `Language` | Pick from 11 options. `English` is the default. Portuguese, Spanish, French, German, Italian, Polish, Russian, Ukrainian and Dutch are also available. There is no Hindi or other Indian language option yet |
| Theme | Two small icons, `Light` and `Dark`. Cosmetic, changeable any time |
| `Your name` | How the app greets you |
| `Email` | Your login username. It does not need to be a real inbox — nothing is emailed to you |
| `Password` | Minimum 8 characters. Use a password manager |
| `Confirm password` | Same again |
| `Currency` | **Choose `INR`.** See the warning below |

Then click **`Create Admin Account`**. You are logged in and taken to the dashboard.

> ### ⚠️ Get the currency right the first time
>
> The `Currency` you pick here becomes your display currency — the unit every total in the app is shown in. **There is currently no screen where a normal user can change it afterwards.** Scroll the dropdown down to `🇮🇳 INR` before you submit.
>
> If you have already set up with the wrong currency, ask your administrator; it can be changed in the database, but not from the interface.

Individual accounts and transactions can still be in other currencies — useful if you hold a foreign brokerage account or get paid in dollars. Those are converted to your display currency for totals. Conversion needs an exchange-rate API key configured on the server; without one, Securo assumes a 1:1 rate and warns you. If everything you own is in rupees, this never affects you.

---

## 2.2 The guided tour

On first login a six-step walkthrough appears. It is genuinely brief:

1. **`Sidebar Navigation`** — "Use the sidebar to navigate between sections of the app."
2. **`Dashboard`** — "Your financial overview at a glance — balances, trends, and spending."
3. **`Accounts`** — "Manage your accounts or connect your bank."
4. **`Transactions`** — "View, search, and categorize your transactions."
5. **`Import`** — "Import bank statements in OFX, CSV, QIF, or CAMT format."
6. **`Categories`** — "Organize your spending with custom categories."

Click **`Next`** through it, or **`Skip tour`**. The last step's button is **`Get Started`**. It only appears once.

Note that step 3 mentions connecting your bank. As covered in the [introduction](README.md), that only works for Brazilian, European and US banks. Indian users import statements instead — [chapter 5](05-import-statements.md).

---

## 2.3 A map of the app

The sidebar runs down the left (on a phone, tap the menu icon at the top left). Here is what every item is actually for. Do not visit them all now — this is a reference to come back to.

### The dashboard

**There is no "Dashboard" item in the sidebar.** Click the **Securo** logo at the top to get there. This trips up everyone.

### Section: `Accounts`

| Item | What it's for | Chapter |
|------|---------------|---------|
| `Transactions` | Every rupee in and out, searchable and filterable. Where you'll spend most of your time | [4](04-transactions.md) |
| `Invoices` | A placeholder. Only appears in business workspaces, and currently shows a "coming next" message. Ignore it | — |
| `Accounts` | Your bank accounts, credit cards, cash and wallets, with their balances | [3](03-accounts.md) |
| `Import` | Upload bank statements and investment order files | [5](05-import-statements.md) |

### Section: `Analysis`

| Item | What it's for | Chapter |
|------|---------------|---------|
| `Reports` | Four views: net worth over time, income vs expenses, cash flow forecast, and a money-flow diagram | [9](09-reports.md) |
| `Assets` | Investments and things you own: mutual funds, stocks, EPF, PPF, FDs, gold, property | [8](08-recurring-and-investments.md) |

### Section: `Setup`

| Item | What it's for | Chapter |
|------|---------------|---------|
| `Budgets` | Monthly spending limits per category | [7](07-budgets-and-goals.md) |
| `Goals` | Savings targets with progress tracking | [7](07-budgets-and-goals.md) |
| `Recurring` | Bills and income that repeat — salary, rent, SIPs, EMIs | [8](08-recurring-and-investments.md) |
| `Categories` | The labels you sort spending into | [6](06-categories-and-rules.md) |
| `Payees` | Who you pay and who pays you, with per-payee spending totals | [4](04-transactions.md) |
| `Groups` | Splitting shared expenses with flatmates, family or colleagues | [10](10-sharing-and-safety.md) |
| `Rules` | Automatic categorisation. The feature that makes this app worth using | [6](06-categories-and-rules.md) |

Below the navigation is a collapsible **`Accounts`** list showing each account and its balance, with your total at the top.

### Two pages that aren't in the sidebar

**Collections** — named bundles of accounts you can filter the whole app by. Reach it from the `Collections` button on the Accounts page, or `Manage collections` in the filter bar. Covered in [chapter 10](10-sharing-and-safety.md).

**Administration** — server-wide settings, only for the admin account. It's in the account menu at the bottom of the sidebar. Covered in [chapter 10](10-sharing-and-safety.md).

---

## 2.4 Four controls worth knowing on day one

**Privacy mode.** The eye icon in the sidebar header. Tooltip reads `Hide values` when off and `Show values` when on. Turning it on replaces every amount in the app with `•••••`. Use it when someone is looking over your shoulder on a train or in an office. The setting is remembered in your browser.

**Command palette.** Press **Ctrl+K** (**⌘K** on a Mac). A search box opens with the placeholder `What are you looking for?`. It searches your transactions, accounts, payees, categories, goals and assets, and offers quick actions like `New transaction`, `Import CSV / OFX / QIF`, `New budget`, `New goal` and `Open reports`. Once you have a few hundred transactions this becomes the fastest way to find anything.

**Theme toggle.** Sun/moon icon beside the privacy toggle.

**Collection filter.** A bar across the top of the content area reading `Viewing` followed by `All accounts`. Once you create collections, this scopes the dashboard, transactions, reports and assets to a subset of your accounts. Leave it alone until [chapter 10](10-sharing-and-safety.md).

---

## 2.5 The account menu

At the very bottom of the sidebar is a row showing your workspace name and email. Click it. This menu holds everything that isn't a page:

| Item | What it does |
|------|--------------|
| `Workspace settings` | Rename the workspace, set its default currency and tax jurisdiction, manage who has access |
| `New workspace` | Create a separate financial container with its own accounts and categories |
| `Administration` | Server settings. Admin accounts only |
| `Change password` | |
| `Two-Factor Auth` | Adds an authenticator-app code at login. **Read [chapter 10](10-sharing-and-safety.md) before enabling — there are no recovery codes** |
| `Passkeys` | Sign in with Windows Hello, Touch ID or a hardware key |
| `Backup` | Downloads a zip of your data. Do this monthly |
| `Check for updates` | Checks whether a newer Securo release exists |
| `Language` | Switch the interface language |
| `Logout` | |

The Securo version number sits at the very bottom of the sidebar.

---

## 2.6 What the empty dashboard is telling you

Click the logo to reach the dashboard. Right now it is empty, which is correct. Here is what will fill in as you add data, so the layout makes sense later:

- **`Savings Rate`** — the percentage of this month's income you didn't spend. The headline number from [chapter 1](01-money-basics.md)
- **`Total Balance`** — everything in your accounts plus your investments
- **`Monthly Income`** and **`Monthly Expenses`** — for the selected month
- **`Spending by Category`** — where the money went, with budget progress bars once budgets exist
- **`Balance Flow`** — a chart of your balance day by day, this month against last
- **`Goals Progress`** — appears once you have goals
- **`Period Transactions`** — the month's transactions, as a list or a calendar

At the top is a month selector (`‹ August 2026 ›`). Almost every card respects it, so you can step back through previous months. Two things don't: goals, and the count of uncategorised transactions, which are always all-time.

You will also see a prompt like **`12 transactions need categorizing`** with a **`Categorize now →`** link once you start importing. Keeping that at zero is the core monthly habit.

---

## 2.7 Set your language, if you want

Account menu → **`Language`**. Eleven languages, shown in their own names. This changes the interface text only — it does not affect your currency or how dates are formatted.

---

## You're oriented

You now know where everything lives. The next chapter is the first one where you enter real data: telling Securo what you own and what you owe.

One piece of advice before you start: **don't try to enter three years of history.** Start from the first day of the current month, or the last statement date. Historical completeness is seductive and it is where most people burn out in week one. You need three months of clean data to build a budget, and the fastest way to get it is to start today and be consistent.

---

**Next:** [Chapter 3 — Setting up your accounts](03-accounts.md)
