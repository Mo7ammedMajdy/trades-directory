# psql demo script

Every command here has been run against the live `trades_db`. Expected output
is noted so you know immediately if something is off.

**Start with:**

```bash
psql trades_db
```

**Two settings worth typing first** — they make Arabic readable in a terminal:

```
\pset null '—'
\x auto
```

`\pset null` makes NULLs visible instead of blank, so "no commercial register"
doesn't look identical to an empty string. `\x auto` switches to one-field-per-
line when a row is too wide, which mixed Arabic and Latin text often is.

**`\q` quits. `\?` lists all backslash commands.** If a query scrolls off,
press `q` to exit the pager.

---

## Act 1 — What exists

### 1.1 List the tables

```
\dt
```

Five tables. Say: *this is the whole database — trade, shop, branch, employee,
and the junction table linking shops to trades.*

### 1.2 Sizes on disk

```
\dt+
```

Adds size and row estimates. Useful for saying *the whole directory is a few
kilobytes; it would behave the same at a million rows, with indexes doing the
work.*

### 1.3 Row counts, all five at once

```sql
SELECT (SELECT count(*) FROM trade)      AS "أقسام",
       (SELECT count(*) FROM shop)       AS "محلات",
       (SELECT count(*) FROM branch)     AS "فروع",
       (SELECT count(*) FROM employee)   AS "عاملون",
       (SELECT count(*) FROM shop_trade) AS "ارتباطات";
```

**Expect `7 | 8 | 13 | 17 | 10`.** A subquery in the SELECT list runs once and
returns a single value — five separate counts in one row.

---

## Act 2 — The structure, and where the rules live

### 2.1 One table in full

```
\d branch
```

**This is the single most informative command in the demo.** It shows, in one
screen:

- every column, its type, and whether it accepts NULL
- `Indexes:` the primary key
- `Check constraints:` the phone-number pattern `^\+?[0-9]{7,15}$`
- `Foreign-key constraints:` `shop_id` must point at a real shop, `ON DELETE CASCADE`
- `Referenced by:` employee rows depend on this table

Say: *the rules are not in the application. They are here, in the table
definition, enforced no matter which program connects.*

### 2.2 The junction table

```
\d shop_trade
```

Point at `PRIMARY KEY, btree (shop_id, trade_id)` — a **composite key**. Two
columns together identify the row. There is no `id` column because the pair
*is* the identity, and it makes recording the same shop-trade pair twice
impossible.

### 2.3 The nullable-but-unique column

```
\d shop
```

`commercial_register` is `UNIQUE` but not `NOT NULL`. Say: *an informal
one-man tradesman has no commercial register. Postgres allows many NULLs under
a UNIQUE constraint, because two unknowns are not necessarily equal — so every
real register is unique and unlimited shops can have none.*

### 2.4 Every constraint in the database, in one list

```sql
SELECT conrelid::regclass AS "الجدول", conname AS "القيد",
       CASE contype WHEN 'p' THEN 'PRIMARY KEY' WHEN 'f' THEN 'FOREIGN KEY'
                    WHEN 'u' THEN 'UNIQUE'      WHEN 'c' THEN 'CHECK'
                    WHEN 'n' THEN 'NOT NULL'    ELSE contype::text END AS "النوع"
FROM pg_constraint
WHERE connamespace = 'public'::regnamespace
ORDER BY conrelid::regclass::text, contype;
```

Reads the system catalogue. Useful line: *the database describes itself — this
list was not written by us, it was queried out of Postgres.*

---

## Act 3 — The data

### 3.1 The seven categories

```sql
SELECT * FROM trade ORDER BY id;
```

### 3.2 The shops, and the deliberate gaps

```sql
SELECT id, name_ar, commercial_register, bank_account FROM shop ORDER BY id;
```

Point at rows 6 and 7 — dashes where the register is missing. Say: *those gaps
are deliberate. عم سيد is a one-man tradesman with no commercial register and
no bank account, exactly the case the brief listed. If the column were NOT
NULL he could not be entered at all.*

### 3.3 Finding the missing ones

```sql
SELECT name_ar, commercial_register FROM shop WHERE commercial_register IS NULL;
```

**Expect 2 rows.**

### 3.4 The NULL trap — worth demonstrating

```sql
SELECT count(*) FROM shop WHERE commercial_register = NULL;
```

**Expect `0`.** Say: *this looks correct and is silently wrong. NULL means
unknown, and comparing anything to an unknown gives unknown — never true. It
matches nothing and raises no error, which is the worst combination. That is
why the previous query used `IS NULL`.*

---

## Act 4 — Relationships

### 4.1 One-to-many: a shop and its branches

```sql
SELECT s.name_ar AS "المحل", b.branch_name AS "الفرع", b.address AS "العنوان"
FROM shop s JOIN branch b ON b.shop_id = s.id
WHERE s.id = 8;
```

**Expect 3 rows.** The shop's name repeats down the column — it is stored once
and joined in, not stored three times.

### 4.2 Many-to-many: shops and trades

```sql
SELECT s.name_ar AS "المحل", t.name_ar AS "القسم"
FROM shop s
JOIN shop_trade st ON st.shop_id = s.id
JOIN trade t       ON t.id = st.trade_id
ORDER BY s.id, t.id;
```

**Expect 10 rows from 8 shops.** شركة الإتقان appears three times, once per
trade. Say: *8 shops become 10 rows because one shop works in three trades.
That is the junction table doing its job — a single `trade_id` column could
never express it.*

### 4.3 Which shops work in more than one trade

```sql
SELECT s.name_ar AS "المحل", count(*) AS "عدد الأقسام"
FROM shop s JOIN shop_trade st ON st.shop_id = s.id
GROUP BY s.id, s.name_ar
HAVING count(*) > 1;
```

**Expect 1 row: الإتقان, 3.** `HAVING` filters *after* grouping — `WHERE`
filters rows, `HAVING` filters groups.

### 4.4 All five tables in one query

```sql
SELECT t.name_ar AS "القسم", s.name_ar AS "المحل", b.address AS "العنوان",
       b.phone_number AS "الهاتف", e.name_ar AS "العامل"
FROM trade t
JOIN shop_trade st ON st.trade_id = t.id
JOIN shop s        ON s.id = st.shop_id
JOIN branch b      ON b.shop_id = s.id
JOIN employee e    ON e.branch_id = b.id
WHERE t.name_ar = 'السباكة'
ORDER BY s.id, b.id, e.id;
```

**Expect 7 rows.** *Every plumber in the directory, by name, with the address
and phone of the branch they work at.* Five tables, four joins, one answer —
and no table holds that answer on its own.

### 4.5 LEFT JOIN — why it matters

```sql
SELECT t.name_ar AS "القسم", count(st.shop_id) AS "عدد المحلات"
FROM trade t
LEFT JOIN shop_trade st ON st.trade_id = t.id
GROUP BY t.id, t.name_ar
ORDER BY count(st.shop_id) DESC, t.id;
```

**Expect all 7 categories.** Say: *`LEFT JOIN` keeps every trade even if no
shop is linked to it. A plain `JOIN` would silently drop empty categories, and
the report would look complete while hiding rows.*

---

## Act 5 — The database refusing bad data

**This is the strongest part of the demo.** Seven inserts, seven different
constraints, seven refusals. Type them one at a time and let each error land.

```sql
-- 1. UNIQUE — a category name that already exists
INSERT INTO trade (name_ar, name_en) VALUES ('السباكة', 'X');
```
> `ERROR: duplicate key value violates unique constraint "trade_name_ar_key"`

```sql
-- 2. UNIQUE — a commercial register belonging to another shop
INSERT INTO shop (name_ar, commercial_register) VALUES ('محل', '45219');
```
> `ERROR: duplicate key value violates unique constraint "shop_commercial_register_key"`

```sql
-- 3. NOT NULL — a shop with no Arabic name
INSERT INTO shop (name_en) VALUES ('No arabic name');
```
> `ERROR: null value in column "name_ar" of relation "shop" violates not-null constraint`

```sql
-- 4. CHECK — a phone number that is not a phone number
INSERT INTO branch (shop_id, address, phone_number) VALUES (1, 'ش', '12ab');
```
> `ERROR: new row for relation "branch" violates check constraint "branch_phone_number_check"`

```sql
-- 5. FOREIGN KEY — a branch of a shop that does not exist
INSERT INTO branch (shop_id, address, phone_number) VALUES (999, 'ش', '01000000000');
```
> `ERROR: insert or update on table "branch" violates foreign key constraint "branch_shop_id_fkey"`
> `DETAIL: Key (shop_id)=(999) is not present in table "shop".`

```sql
-- 6. CHECK — a national ID that is not 14 digits
INSERT INTO employee (branch_id, name_ar, national_id, phone_number)
VALUES (1, 'س', '123', '01000000000');
```
> `ERROR: new row for relation "employee" violates check constraint "employee_national_id_check"`

```sql
-- 7. COMPOSITE PRIMARY KEY — linking the same shop and trade twice
INSERT INTO shop_trade (shop_id, trade_id) VALUES (1, 1);
```
> `ERROR: duplicate key value violates unique constraint "shop_trade_pkey"`

**The line to say:** *none of that was checked by application code. Every one
of those refusals came from the database, and no program connecting to it —
ours, a script, or psql by hand — can get past them.*

---

## Act 6 — Cascade delete, safely

Deleting a shop should take its branches, their employees, and its trade links
with it. **Run it inside a transaction so nothing is actually lost.**

```sql
BEGIN;

SELECT (SELECT count(*) FROM shop) shops, (SELECT count(*) FROM branch) branches,
       (SELECT count(*) FROM employee) employees, (SELECT count(*) FROM shop_trade) links;
-- 8 | 13 | 17 | 10

DELETE FROM shop WHERE id = 8;

SELECT (SELECT count(*) FROM shop) shops, (SELECT count(*) FROM branch) branches,
       (SELECT count(*) FROM employee) employees, (SELECT count(*) FROM shop_trade) links;
-- 7 | 10 | 13 | 7      one shop, three branches, four employees, three links

ROLLBACK;

SELECT (SELECT count(*) FROM shop) shops, (SELECT count(*) FROM branch) branches,
       (SELECT count(*) FROM employee) employees, (SELECT count(*) FROM shop_trade) links;
-- 8 | 13 | 17 | 10     everything back
```

**Two things to say.** First: *one `DELETE` removed eleven rows across four
tables. The application does not loop and clean up — `ON DELETE CASCADE` is
declared in the schema and the database does it, correctly, every time.*
Second: *`ROLLBACK` undid all of it. Everything between `BEGIN` and `COMMIT`
either happens completely or not at all.*

**If you forget the `ROLLBACK`, run it before doing anything else.** To rebuild
from scratch at any point:

```bash
dropdb trades_db && createdb trades_db \
  && psql trades_db -f schema.sql && psql trades_db -f seed.sql
```

---

## Act 7 — Reports

### 7.1 Staff per branch

```sql
SELECT s.name_ar AS "المحل", b.branch_name AS "الفرع", count(e.id) AS "عاملون"
FROM shop s
JOIN branch b      ON b.shop_id = s.id
LEFT JOIN employee e ON e.branch_id = b.id
GROUP BY s.id, s.name_ar, b.id, b.branch_name
ORDER BY s.id, b.id;
```

**Expect 13 rows**, one per branch.

### 7.2 The biggest operators

```sql
SELECT s.name_ar AS "المحل",
       count(DISTINCT b.id) AS "فروع",
       count(e.id)          AS "عاملون"
FROM shop s
LEFT JOIN branch b   ON b.shop_id = s.id
LEFT JOIN employee e ON e.branch_id = b.id
GROUP BY s.id, s.name_ar
ORDER BY count(e.id) DESC, count(DISTINCT b.id) DESC;
```

**`count(DISTINCT b.id)` matters here.** Joining branches *and* employees
multiplies the rows — a branch with 2 employees appears twice — so a plain
`count(b.id)` would report 4 branches where there are 3. Say: *this is the
classic double-counting mistake in a multi-join aggregate, and `DISTINCT` is
the fix.*

### 7.3 Where the work is, by governorate

```sql
SELECT CASE
         WHEN b.address LIKE '%القاهرة%'    THEN 'القاهرة'
         WHEN b.address LIKE '%الجيزة%'     THEN 'الجيزة'
         WHEN b.address LIKE '%الإسكندرية%' THEN 'الإسكندرية'
         WHEN b.address LIKE '%أكتوبر%'     THEN '6 أكتوبر'
         ELSE 'غير محدد'
       END AS "المحافظة",
       count(*) AS "فروع"
FROM branch b
GROUP BY 1
ORDER BY count(*) DESC;
```

Shows `CASE` deriving a column that isn't stored, and `GROUP BY 1` grouping by
the first select expression.

---

## Act 8 — Two closing lines

### 8.1 The database describes itself

```sql
SELECT table_name AS "الجدول", count(*) AS "أعمدة"
FROM information_schema.columns
WHERE table_schema = 'public'
GROUP BY table_name ORDER BY table_name;
```

### 8.2 Show the whole schema as SQL

```bash
pg_dump --schema-only --no-owner trades_db | less
```

Run from the shell, not inside psql. Say: *Postgres can regenerate the exact
`CREATE TABLE` statements from the live database — the structure is data too.*

---

## Quick reference

| Command | Does |
|---|---|
| `\dt` | list tables |
| `\d name` | one table in full, with constraints |
| `\di` | list indexes |
| `\l` | list databases |
| `\x auto` | wrap wide rows one field per line |
| `\pset null '—'` | make NULLs visible |
| `\timing on` | show how long each query takes |
| `\e` | open the last query in an editor |
| `\i file.sql` | run a file |
| `\q` | quit |

**If a query goes wrong mid-transaction**, psql refuses everything after it
with `current transaction is aborted`. Type `ROLLBACK;` and carry on.
