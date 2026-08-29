# 10. Sharing and staying safe

Splitting expenses with other people, sharing your data with a partner, and — importantly — not losing everything.

If you read only one section of this chapter, make it 10.5 on backups.

---

## 10.1 Splitting expenses

You pay for a group dinner, or you and two flatmates share the electricity bill. **Groups** track who owes whom.

Go to **`Groups`** and click **`+ Add group`**:

| Field | What to enter |
|-------|---------------|
| `Name` | `Flat 402`, `Goa Trip`, `Family` |
| `Type` | `Social`, `Cost center`, `Project`, `Client` or `Other`. For personal use, `Social`. **This can't be changed later** |
| `Default currency` | `INR` |
| `Notes` | Optional |

### Adding people

Open the group and click **`Add member`** in the `Members` section.

The key field is **`Linked Securo user`**. If the person has their own Securo login on the same server, pick them and they'll see the group too. Otherwise leave it on `— Not linked (non-user) —` and just enter a `Name`.

Most of the time you'll add unlinked members. Your flatmates almost certainly don't have accounts on your self-hosted Securo, and they don't need to — you're tracking the balance for your own benefit.

You'll appear as a member marked `(you)`.

### Recording a shared expense

Add or edit the transaction, tick **`Split this transaction`**, choose the `Group`, pick a **`Split by`** method (`Equal`, `Exact amounts`, `Percentages`) and tick who was involved. [Chapter 4](04-transactions.md) covers the details.

### Seeing who owes what

The group detail page shows `Total moved`, `Owed to you`, `You owe`, plus spending charts.

The **`Balances`** section reads in plain language — `Priya owes you ₹2,400`, `You owe Rahul ₹800`, or `All settled.` when everything nets out.

### Settling up

When someone pays you back, click **`Settle up`** (or **`Record settlement`**). The dialog asks for `From`, `To`, `Amount`, `Currency`, `Date` and `Notes`, plus one choice that matters:

| Option | When to use it |
|--------|----------------|
| `Don't record a transaction` | They handed you cash and you're not tracking it |
| `Create a new transaction` | Creates a matching entry in an account you pick |
| `Link an existing transaction` | The UPI transfer already came in on your imported statement — link to it |

If you import bank statements, **`Link an existing transaction`** is usually right. The money already appeared in your account; this connects it to the debt.

### A realistic use

For the shared flat: one group called `Flat 402` with three members. Every shared bill — rent, electricity, internet, the cleaner — gets split `Equal`. Groceries get split `Equal` when shared and left unsplit when personal. At month end you look at `Balances`, one person transfers the difference, and you record it as a settlement.

Ten minutes a month, and no arguments in November about who paid the August electricity bill.

---

## 10.2 Collections

A **collection** is a named bundle of accounts and wallets used to filter the app. Reach it from the `Collections` button on the Accounts page, or `Manage collections` in the filter bar.

**`New collection`** takes a `Name`, a `Color`, and checkboxes for which `Accounts` and `Wallets` belong to it.

Once created, the filter bar at the top (`Viewing` `All accounts`) lets you scope the dashboard, transactions, reports and assets to just that collection.

Worth setting up if you have genuinely separate financial lives — freelance income alongside a salary, or a joint household account alongside personal ones. If all your accounts are one pot, skip this.

---

## 10.3 Workspaces

A **workspace** is a completely separate container: its own accounts, categories, budgets, goals and transactions. Switch between them from the account menu at the bottom of the sidebar.

**`New workspace`** asks for a `Name` and a `Type` — `Personal` or `Business`. The only practical difference today is that `Business` shows an `Invoices` nav item, which is currently a placeholder. Type can't be changed later.

**Do you need more than one?** Probably not. One personal workspace covers most people, and collections handle the "keep these accounts separate" use case without splitting your data.

Create a second workspace when the finances genuinely don't belong together — a freelance business you need clean records for, or a family trust you administer. Not for "personal vs household," where you'd lose the combined view.

### Sharing a workspace with your partner

**`Workspace settings`** → **`Members`** → **`Add member`**. You enter their `Email` and a `Role`, and — if they don't have an account yet — a password that creates one.

| Role | What they can do |
|------|------------------|
| `Owner` | Full access, including managing members and settings |
| `Editor` | Read and write all financial data, but can't manage members |
| `Viewer` | Read-only |

For a spouse managing money jointly, `Owner` or `Editor`. For a parent or advisor you want to show things to, `Viewer`.

Removing someone doesn't delete their user account, just their access to that workspace.

### Workspace details

The `Details` section holds `Name`, `Icon`, `Color`, `Default currency`, `Language` and `Tax jurisdiction`. Set `Tax jurisdiction` to India if you want GSTIN and PAN as available tax ID fields on payees — mostly relevant for business use.

Note this `Default currency` is the workspace's, which is separate from the display currency you chose at setup ([chapter 2](02-first-hour.md)).

The `Danger zone` has **`Archive workspace`**, which hides it while preserving the data.

---

## 10.4 Locking down your account

All under the account menu at the bottom of the sidebar.

**`Change password`** — `Current password`, `New password`, `Confirm password`. Minimum 8 characters.

**`Passkeys`** — sign in with Windows Hello, Touch ID, or a hardware key instead of typing a password. Give each one a name like `Work laptop`. Register **at least two** if you rely on them, because there's no recovery mechanism if you lose your only one.

**`Two-Factor Auth`** — adds a code from an authenticator app at login.

> ### ⚠️ 2FA has no recovery codes
>
> Most services give you a list of one-time backup codes when you enable two-factor authentication. **Securo does not.** There is no "lost my phone" flow.
>
> If you enable 2FA and lose access to your authenticator app, you are locked out, and the only way back in is direct database access on the server.
>
> If you enable it anyway — and on a server exposed to the internet you probably should — **save the TOTP secret shown during setup** (the text string under the QR code) somewhere safe, like a password manager. That string is what lets you re-add the account on a new phone.
>
> On a Securo instance that only runs on your home network, 2FA adds little and risks a lot. Weigh it accordingly.

---

## 10.5 Backups — read this section

Your entire financial history lives in a database on one machine. Disks fail.

### Taking a backup

Account menu → **`Backup`**. The dialog is titled `Download backup`.

You can set a `Password (optional)`. With one, you get an AES-256 encrypted zip that any standard archiver can open. Without one, a plain zip. The dialog is clear about the consequence: *"Securo does not store this password and cannot recover the file without it."*

You get `securo-backup-2026-08-31.zip`.

### What's actually in it

| Included | Not included |
|----------|--------------|
| `accounts.json` | **Goals** |
| `transactions.json` | **Payees** |
| `categories.json`, `category_groups.json` | **Groups**, members, splits and settlements |
| `rules.json` | **Collections** |
| `recurring_transactions.json` | Workspace settings |
| `budgets.json` | Attachments |
| `assets.json`, `asset_values.json` | |
| `import_logs.json`, `metadata.json` | |

**The backup is not complete.** Your transactions, accounts, categories, rules, budgets and assets are safe. Your goals, payees, split groups and collections are not in the file.

For the two that represent real work — your **rules** and your **categories** — the rules page has its own **`Export`** producing `securo-categorization-rules.json`. Do that too, and keep it somewhere separate.

### ⚠️ There is no restore

> **Securo has no way to import a backup zip.** No screen, no API, no command.
>
> The backup is a set of readable JSON files, so your data isn't lost in any absolute sense — but recovering from one means someone writing a script against the API, or loading the JSON into the database by hand. It is not a click.

The practical conclusion: **the zip is not your primary protection.** What actually protects you is a backup of the PostgreSQL database itself, which whoever runs your server should be doing on a schedule with `pg_dump` or volume snapshots. A database backup restores in one command.

Think of the Securo zip as a portable, readable copy of your data — good for migrating, good for reading your own records in twenty years, good for peace of mind. Not a disaster recovery plan.

### What to actually do

1. **Monthly:** download a backup zip after your import. Thirty seconds
2. **Once:** export your rules JSON, and again whenever you change them significantly
3. **Make sure the database is backed up.** If that's you, set up `pg_dump` on a cron. If it's someone else, ask them
4. **Keep a copy off the machine.** A backup sitting on the same disk as the database protects you from nothing

### Automatic backups to Google Drive

If your administrator has configured Google credentials on the server, the admin settings page has a **`Google Drive backup`** section: connect a Google account, pick a `Schedule` of `Daily` or `Weekly`, optionally set a password. It uploads every workspace, keeping a latest file plus the last three dated copies.

This is **instance-wide and admin-only** — one Google account for the whole installation. On a single-user home server, that's you, and it's worth ten minutes to set up. Same caveats apply: same contents, still no restore.

---

## 10.6 Admin settings worth knowing about

The account menu shows **`Administration`** if you're the admin. Most of that page won't concern you, but four settings might.

**`Accounting`** — how credit card purchases are counted:

- `Cash basis` (default) — a purchase counts on the day you make it
- `Accrual basis` — it counts on the bill's due date

Cash basis answers "when did I spend?" Accrual answers "when does money leave my bank?" Cash basis is more intuitive for personal budgeting; stick with it unless you have a reason.

**`Number format`** — `Automatic`, `1,000.00`, `1.000,00` or `1 000,00`. There is no Indian lakh/crore grouping option (`1,00,000`), so ₹5 lakh displays as `500,000.00` rather than `5,00,000.00`. Nothing to be done about it today.

**`Date format`** — `Automatic`, `Day / Month / Year`, `Month / Day / Year` or `Year / Month / Day`. Set it to **`Day / Month / Year`** to match Indian convention.

**`Registration`** — `Allow user registration`. On a server reachable from the internet, turn this **off** unless you specifically want strangers creating accounts. Create accounts for family members yourself from the admin page.

---

**Next:** [Chapter 11 — Your first 90 days](11-first-90-days.md)
