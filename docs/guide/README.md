# Securo for Beginners

A guide for people who have never used a personal finance app, and are not sure they understand personal finance either.

If you earn a salary, have a bank account and a credit card, and have a vague guilty feeling that you should be "managing your money" — this guide is for you. It teaches two things at once:

1. **What to actually do with your money**, in plain language, with no products to sell you.
2. **How to do it in Securo**, click by click.

You do not need an accounting background. You do not need to know what a balance sheet is. Every term is explained the first time it appears.

---

## Who this guide assumes you are

The examples follow one person so the numbers stay concrete instead of abstract:

> **Aarav, 27**, software engineer in Bengaluru. Takes home **₹2,20,000 per month** after tax and PF (roughly a ₹36.6 lakh CTC). Lives with his parents, so he pays no rent. One credit card. No loans. He has about ₹6 lakh sitting in his savings account doing nothing, and no idea where the rest went.

Your salary is almost certainly different from Aarav's. That is fine — every rule in this guide is expressed as a percentage or a method, and Aarav's rupee figures are just there to show the method working. If you earn ₹40,000 a month, the same steps apply to smaller numbers.

The guide is written for India: rupees, EPF, PPF, UPI, TDS, and the fact that **no Indian bank connects to Securo automatically** (more on that below). If you are elsewhere, most of it still applies; skip the tax-specific parts.

---

## The one thing to know before you start

Securo has a feature called **bank sync** that pulls transactions in automatically. It supports three providers, covering Brazil, Europe, and the United States. **None of them support Indian banks.**

That is not a defect you can configure around, and it changes how you will use the app. Your workflow will be:

- **Import** your bank and credit card statements once a month (a two-minute job once you've done it twice), and
- **Add** cash and UPI spends manually as they happen, or reconstruct them at month end.

This sounds like more work than it is. After you set up **Rules** (chapter 6), the imported transactions categorise themselves, and the monthly job becomes: download two statements, upload two files, glance at the ones the rules missed. Ten minutes.

---

## Two ways to read this

**The one-hour path.** If you want a working setup today and will learn the rest later, read these four in order:

1. [Your first hour in Securo](02-first-hour.md) — get oriented
2. [Setting up your accounts](03-accounts.md) — tell Securo what you own and owe
3. [Recording transactions](04-transactions.md) — the daily habit
4. [Importing bank statements](05-import-statements.md) — the monthly habit

That gets your money visible. Come back for the rest when you want it to be *managed* rather than just visible.

**The full course.** Read all twelve chapters in order over a couple of evenings. Chapter 1 has no software in it at all — it is the money part, and it is the part that actually changes your finances. The app is just bookkeeping; the decisions in chapter 1 are what matter.

---

## The chapters

| # | Chapter | What you get out of it |
|---|---------|------------------------|
| 1 | [Money basics for a salaried person](01-money-basics.md) | Read your payslip properly, understand where your salary really goes, build an emergency fund, pick a savings rate that fits your life |
| 2 | [Your first hour in Securo](02-first-hour.md) | Create your login, set rupees as your currency, learn what every page in the app is for |
| 3 | [Setting up your accounts](03-accounts.md) | Get your bank balance, credit card, cash and UPI wallets into the app correctly |
| 4 | [Recording transactions](04-transactions.md) | Add spends, move money between accounts, handle EMIs, split a dinner bill, attach receipts |
| 5 | [Importing bank statements](05-import-statements.md) | Turn a bank CSV into clean transactions without creating duplicates |
| 6 | [Categories and rules](06-categories-and-rules.md) | Set up categories that match Indian life, then automate them so you never categorise Swiggy again |
| 7 | [Budgets and goals](07-budgets-and-goals.md) | Build your first budget from your own spending history, and set targets you'll actually hit |
| 8 | [Recurring bills and investments](08-recurring-and-investments.md) | Track salary, rent, SIPs and EMIs on autopilot; record EPF, PPF, FDs, stocks and mutual funds |
| 9 | [Reading your reports](09-reports.md) | Understand net worth, cash flow and the money map without an accounting degree |
| 10 | [Sharing and staying safe](10-sharing-and-safety.md) | Split expenses with family or flatmates, share a workspace, back up your data, lock your account down |
| 11 | [Your first 90 days](11-first-90-days.md) | A week-by-week checklist that turns all of the above into a habit |
| 12 | [FAQ and glossary](12-faq-and-glossary.md) | Answers to the things that confuse everyone, and plain-English definitions |

---

## Things Securo does not do

Better to know now than to discover in month three. As of this version:

- **No Indian bank sync.** Covered above. Import statements manually.
- **No restore from backup inside the app.** You can download a backup, and you should. But if you lose your database, putting the backup back requires manual work outside Securo. See [chapter 10](10-sharing-and-safety.md) for what this means for you in practice.
- **No email or push notifications.** Nothing will remind you that a bill is due or that you have blown your budget. You have to open the app. Chapter 11 suggests a schedule.
- **No budget rollover.** Money you don't spend this month does not increase next month's budget. Chapter 7 explains how to work around this.
- **No Invoices yet.** The page exists in business workspaces but is a placeholder.
- **Two-factor authentication has no recovery codes.** If you enable 2FA and lose your phone, you are locked out. Read [chapter 10](10-sharing-and-safety.md) before turning it on.

---

## A note on honesty with yourself

The most common way people fail at this is not picking the wrong app or the wrong mutual fund. It is entering only the spending they feel good about. A month of records with the ₹4,000 bar tab missing is worse than no records, because it produces a confident wrong answer.

Everything you type goes into a database on a machine you control. Nobody is reading it. Enter the embarrassing transactions.

---

Start with [chapter 1: money basics](01-money-basics.md), or jump straight to [chapter 2](02-first-hour.md) if you'd rather get the app running first.
