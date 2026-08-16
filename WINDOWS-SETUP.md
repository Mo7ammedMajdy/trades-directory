# Running the demo on someone else's machine

Three ways, easiest first. **Pick option 1 unless you've been told otherwise.**

---

## Option 1 — Don't install anything. Serve from your laptop.

The app already listens on every network interface, so any device on the same
Wi-Fi can open it in a browser. Nothing is installed on the professor's laptop
and nothing can go wrong on his machine.

**On your laptop:**

```bash
cd ~/db-project
sudo ufw allow 8000/tcp          # once — lets other devices reach the port
.venv/bin/fastapi run app_starter.py --port 8000
```

**Find your address:**

```bash
ip -4 addr show scope global | grep -oP 'inet \K[\d.]+'
```

**On his laptop**, open:

```
http://YOUR_IP:8000
```

Right now that is **http://10.180.10.200:8000** — but the address changes with
the network, so check it again in the room.

**Before you leave, undo the firewall rule:**

```bash
sudo ufw delete allow 8000/tcp
```

### If there's no shared Wi-Fi

Turn on your phone's hotspot and connect both laptops to it. No internet is
needed — they only have to be on the same network. Your IP will change, so
check it again after connecting.

### If nothing else works

Plug your laptop into the projector and drive the demo yourself. That is the
normal way this is done, and it removes every remaining risk.

---

## Option 2 — Full install on his Windows laptop

Budget **20–30 minutes**, and you need administrator rights on his machine.
**Do this the day before if you possibly can, not in the room.**

### 1. PostgreSQL

Download the Windows installer: <https://www.postgresql.org/download/windows/>

During setup:

- **Write down the password you set for the `postgres` user.** You need it in
  step 4 and there is no way to recover it later.
- Keep the default port **5432**.
- Locale: leave as default.
- At the end it offers **Stack Builder** — skip it.

This installs `psql` and pgAdmin. A Start-menu entry called **SQL Shell (psql)**
appears; that is the terminal for the database demo.

### 2. Python

Download from <https://www.python.org/downloads/windows/>

**Tick "Add python.exe to PATH" on the first screen.** It is off by default and
everything afterwards fails without it.

### 3. The project

Either `git clone https://github.com/Mo7ammedMajdy/trades-directory.git`, or
download the ZIP from GitHub and extract it. **Bring a copy on a USB stick as
well** — assume there is no internet.

Open **Command Prompt** in that folder (type `cmd` in the address bar of File
Explorer and press Enter), then:

```cmd
pip install "fastapi[standard]" "psycopg[binary]" jinja2
```

### 4. Create and load the database

In the same Command Prompt, replace `YOUR_PASSWORD` with the one from step 1:

```cmd
set PGPASSWORD=YOUR_PASSWORD
set DATABASE_URL=dbname=trades_db user=postgres password=YOUR_PASSWORD host=127.0.0.1 client_encoding='UTF8'
"C:\Program Files\PostgreSQL\18\bin\createdb" -U postgres trades_db
"C:\Program Files\PostgreSQL\18\bin\psql" -U postgres -d trades_db -f schema.sql
"C:\Program Files\PostgreSQL\18\bin\psql" -U postgres -d trades_db -f seed.sql
```

Adjust `18` if a different version was installed.

**Expect:** five `CREATE TABLE`, then `INSERT 0 7`, `INSERT 0 8`, `INSERT 0 10`,
`INSERT 0 13`, `INSERT 0 17`.

### 5. Run it

```cmd
fastapi run app_starter.py --port 8000
```

Open <http://127.0.0.1:8000>.

**`set DATABASE_URL` only lasts for that Command Prompt window.** Open a new
one and you must set it again, or the app will try to connect as the Windows
user and fail.

### 6. Arabic in the Windows terminal

Before running any psql command in Command Prompt:

```cmd
chcp 65001
```

That switches the console to UTF-8. Without it Arabic comes out as `????` or
mojibake, which will wreck the psql part of the demo. **PowerShell and Windows
Terminal handle UTF-8 better than the old Command Prompt** — prefer them.

Inside psql, also run:

```
\pset null '—'
\x auto
```

### What goes wrong on Windows, and the fix

| Symptom | Cause and fix |
|---|---|
| `'psql' is not recognized` | Not on PATH. Use the full `"C:\Program Files\PostgreSQL\18\bin\psql"` path, or the **SQL Shell (psql)** Start-menu entry. |
| `'python'` / `'pip'` not recognized | "Add to PATH" was unticked. Re-run the Python installer, choose Modify, tick it. |
| `password authentication failed` | Wrong password, or `DATABASE_URL` not set in *this* window. |
| Arabic shows as `????` | `chcp 65001`, or use Windows Terminal. |
| `database "trades_db" does not exist` | Step 4's `createdb` didn't run. |
| Port 8000 already in use | `fastapi run app_starter.py --port 8001` |

---

## Option 3 — A copy he can keep, without running anything

If he only wants the work rather than a live demo, give him the repository link
plus a database dump:

```bash
pg_dump --no-owner --clean --if-exists trades_db > trades_db_dump.sql
```

One file that recreates the whole database — structure and data — on any
Postgres:

```
psql -U postgres -d trades_db -f trades_db_dump.sql
```

Include `schema.sql`, `seed.sql`, `PSQL-DEMO.md` and the ERD alongside it.

---

## What to bring on the day

- **Your own laptop, charged**, with the app already running and tested
- **A USB stick** with the whole `db-project` folder, including `trades_db_dump.sql`
- The GitHub link written down
- **Screen recordings** of the app and the psql demo, as the final fallback —
  if the machine, the network and the projector all fail, you can still show
  the work
