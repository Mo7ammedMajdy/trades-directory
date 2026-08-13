# Trades Directory — Database Project

A directory of tradesmen and contracting shops in Egypt, organised by trade
(بند): plumbing, carpentry, electrical, mechanical, metalwork, domestic
services, painting.

The database is **finished**. What's left is the backend and the web pages.

---

## What's in this repo

| File | What it is |
|---|---|
| `schema.sql` | The 5 tables. Creates the structure. |
| `seed.sql` | The sample data. 55 rows total. |
| `ENDPOINTS.md` | **The 5 pages you need to build.** Start here. |
| `app_starter.py` | A working FastAPI app with one page done. Copy the pattern. |
| `queries.sql` | Ready-made SQL for every page. Copy these, don't write your own. |
| `join-walkthrough.html` | Explains how the SQL joins work. Open it in a browser. |

**Do not edit `schema.sql` or `seed.sql`.** If you think something is missing
from the database, message Mohamed. Changing them breaks everyone else.

---

## Setup — do this first

### 1. Install PostgreSQL

**Windows:** download the installer from
<https://www.postgresql.org/download/windows/>, run it, and **write down the
password you set for the `postgres` user** — you will need it. Accept every
other default. When it offers "Stack Builder" at the end, skip it.

**Linux (Arch/CachyOS):**
```bash
sudo pacman -S postgresql
sudo -iu postgres initdb -D /var/lib/postgres/data -E UTF8 --locale=en_US.UTF-8
sudo systemctl enable --now postgresql
sudo -u postgres createuser --superuser $USER
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install postgresql
sudo -u postgres createuser --superuser $USER
```

### 2. Create the database and load it

Open a terminal in this folder (on Windows use **SQL Shell (psql)** or
PowerShell), then:

```bash
createdb trades_db
psql trades_db -f schema.sql
psql trades_db -f seed.sql
```

You should see 5 × `CREATE TABLE`, then
`INSERT 0 7`, `INSERT 0 8`, `INSERT 0 10`, `INSERT 0 13`, `INSERT 0 17`.

### 3. Check it worked

```bash
psql trades_db -c "SELECT count(*) FROM shop;"
```

Should print `8`.

**If something goes wrong**, the fix is almost always to start over:

```bash
dropdb trades_db && createdb trades_db && psql trades_db -f schema.sql && psql trades_db -f seed.sql
```

Close any open `psql` window first, or `dropdb` will refuse.

### 4. Install Python packages

```bash
pip install "fastapi[standard]" "psycopg[binary]" jinja2
```

### 5. Run the starter app

```bash
fastapi dev app_starter.py
```

Open <http://127.0.0.1:8000> — you should see the 7 trades listed.
Open <http://127.0.0.1:8000/docs> — auto-generated API documentation.

**If you get there, your setup is correct and you can start building.**

---

## What's in the database

Five tables, 55 rows.

```
trade ──┐
        ├── shop_trade ──── shop ──── branch ──── employee
        ┘                  (8)        (13)        (17)
       (7)      (10)
```

- **`trade`** — the 7 categories
- **`shop`** — the businesses. Name, commercial register, bank account,
  technical capacity
- **`branch`** — each shop's locations. Address and phone. One shop can have
  many branches
- **`employee`** — the people at each branch
- **`shop_trade`** — links shops to trades. A shop can do more than one trade
  (شركة الإتقان does three), which is why this table exists

Two things that will trip you up:

1. **Some columns are empty on purpose.** `commercial_register`,
   `bank_account`, `name_en`, `branch_name` and `national_id` are `NULL` for
   the informal one-man tradesmen. Your pages must handle a missing value
   without crashing — show a dash, not `None`.
2. **Names are in Arabic.** Put `dir="rtl"` on the HTML elements showing
   `name_ar` and `address`, or the text will render in the wrong order.

---

## Who does what

| Person | Job |
|---|---|
| Mohamed | Database — **done** |
| Wageh | Backend — the 5 endpoints in `ENDPOINTS.md` |
| Bola | Frontend — the HTML templates those endpoints render |

Work off `ENDPOINTS.md`. It lists every page, what it shows, and the exact SQL
to run. `queries.sql` has the same SQL ready to copy.

**Deadline: Sunday.** If you are stuck for more than 30 minutes on setup,
message the group — do not sit on it.
