# Trades Directory — how to run it

A directory of tradesmen and contracting shops in Egypt, organised by trade.
PostgreSQL database with a small web application on top.

**Everything below has to be done once. After that it is one double-click.**

---

## 1. Install PostgreSQL

<https://www.postgresql.org/download/windows/>

Run the installer and accept the defaults, with two exceptions:

- **Write down the password you set for the `postgres` user.** You will need it
  in step 3, and it cannot be recovered afterwards.
- At the end it offers **Stack Builder** — skip it, nothing here needs it.

Keep the default port, 5432.

## 2. Install Python

<https://www.python.org/downloads/windows/>

**On the first screen, tick "Add python.exe to PATH."** It is switched off by
default, and the rest of the setup fails without it.

## 3. Set up the project

Double-click **`setup-windows.bat`**.

It asks for the PostgreSQL password from step 1, then creates the database,
loads the tables and the sample data, and installs what the application needs.
It checks each step and stops with a plain explanation if something is wrong.

When it finishes it prints:

```
trades=7  shops=8  branches=13  employees=17
```

## 4. Run it

Double-click **`run-windows.bat`**.

Your browser opens at <http://127.0.0.1:8000>. Leave the black window open
while you use the site; closing it stops the server.

That is the only step you repeat.

---

## What you can do in it

- Browse the seven trades, and the shops registered under each
- Open a shop to see its details, its branches, and the staff at every branch
- Search by shop name, commercial register, or a branch phone number
- Add, edit and delete trades, shops, branches and employees
- Link a shop to more than one trade — a maintenance company that does
  plumbing, electrical and metalwork is one record, not three

---

## Looking at the database directly

Open **SQL Shell (psql)** from the Start menu. Press Enter at each prompt
except the last two: database `trades_db`, then the password.

```
\dt              list the tables
\d branch        one table in full, with all its constraints
\q               quit
```

**`PSQL-DEMO.md`** in this folder is a guided tour of the database — every
query with an explanation of what it shows.

If Arabic appears as `????`, run `chcp 65001` before starting psql, or use
Windows Terminal instead of the old Command Prompt.

---

## If something goes wrong

| Message | What to do |
|---|---|
| `Could not find psql` | PostgreSQL is not installed, or went somewhere unusual. Reinstall from step 1. |
| `Python is not on PATH` | Re-run the Python installer, choose **Modify**, tick "Add python.exe to PATH". |
| `Could not connect` | Wrong password. There is no recovery — reinstall PostgreSQL and set a new one. |
| `Could not recreate the database` | Close pgAdmin and any open psql window, then run setup again. |
| Port 8000 already in use | Something else is using it. Edit `run-windows.bat` and change `8000` to `8001`. |
| The page looks unstyled | Press **Ctrl+Shift+R** in the browser. |

**To start over completely**, run `setup-windows.bat` again — it rebuilds the
database from scratch and reloads the original sample data.

---

## What is in this folder

| File | What it is |
|---|---|
| `schema.sql` | The five tables and every rule the database enforces |
| `seed.sql` | The sample data — 55 rows |
| `trades_db_dump.sql` | The whole database in one file, structure and data together |
| `queries.sql` | Every query the application runs |
| `PSQL-DEMO.md` | A guided tour of the database from the terminal |
| `erd.png` | The entity-relationship diagram |
| `app_starter.py` | The web application |
| `templates/`, `static/` | Its pages and stylesheet |
| `ENDPOINTS.md` | What each page does and the SQL behind it |

Source: <https://github.com/Mo7ammedMajdy/trades-directory>
