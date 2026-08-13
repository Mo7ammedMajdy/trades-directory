# The 5 pages to build

Build them in this order. Each one is roughly 10 lines of Python plus a
template. The SQL is written for you — copy it, don't invent your own.

`%s` is a placeholder. **Never** paste a value into the SQL string yourself;
pass it as the second argument to `execute()`. See `app_starter.py`.

---

## 1. `GET /` — the 7 trade categories

The home page. A list of the 7 trades; each links to `/trades/{id}`.

```sql
SELECT id, name_ar, name_en
FROM trade
ORDER BY id;
```

Returns 7 rows. **Already built in `app_starter.py`** — use it as your model
for the other four.

---

## 2. `GET /trades/{trade_id}` — shops in one trade

Every shop that works in this trade, with how many branches each has.

```sql
SELECT s.id, s.name_ar, s.name_en, s.commercial_register,
       count(b.id) AS branch_count
FROM shop s
JOIN shop_trade st ON st.shop_id = s.id
LEFT JOIN branch b ON b.shop_id = s.id
WHERE st.trade_id = %s
GROUP BY s.id, s.name_ar, s.name_en, s.commercial_register
ORDER BY s.name_ar;
```

Check it: `/trades/1` (plumbing) gives **2 shops**, `/trades/2` gives **1**.

`commercial_register` can be `NULL` — show a dash, not the word `None`.

---

## 3. `GET /shops/{shop_id}` — one shop in full

Three queries on one page: the shop, its branches, its trades.

**The shop:**
```sql
SELECT id, name_ar, name_en, commercial_register, bank_account, technical_capacity
FROM shop
WHERE id = %s;
```

**Its branches, with staff counts:**
```sql
SELECT b.id, b.branch_name, b.address, b.phone_number,
       count(e.id) AS staff_count
FROM branch b
LEFT JOIN employee e ON e.branch_id = b.id
WHERE b.shop_id = %s
GROUP BY b.id, b.branch_name, b.address, b.phone_number
ORDER BY b.id;
```

**Its trades:**
```sql
SELECT t.name_ar
FROM trade t
JOIN shop_trade st ON st.trade_id = t.id
WHERE st.shop_id = %s
ORDER BY t.id;
```

Check it: `/shops/8` (شركة الإتقان) gives **3 branches** and **3 trades**.
`/shops/6` gives 1 branch and several `NULL` fields — use it to test that your
page doesn't crash on missing data.

If the first query returns nothing, the shop id doesn't exist. Return a 404:

```python
from fastapi import HTTPException
if row is None:
    raise HTTPException(status_code=404, detail="Shop not found")
```

---

## 4. `GET /shops/new` — the add-shop form

No SQL. Just an HTML form with five fields, posting to `/shops`:

| Field name | Required |
|---|---|
| `name_ar` | yes |
| `name_en` | no |
| `commercial_register` | no |
| `bank_account` | no |
| `technical_capacity` | no |

Only `name_ar` gets `required` in the HTML. The other four are allowed to be
empty — that's deliberate, informal tradesmen don't have a commercial register.

---

## 5. `POST /shops` — save it

```sql
INSERT INTO shop(name_ar, name_en, commercial_register, bank_account, technical_capacity)
VALUES (%s, %s, %s, %s, %s)
RETURNING id;
```

`RETURNING id` hands back the new shop's id so you can redirect to its page.

**Turn empty strings into `NULL` before inserting**, or you'll store `''`
instead of "no value":

```python
def blank_to_none(v):
    return v if v and v.strip() else None
```

**Two errors you will hit, and what they mean:**

- `null value in column "name_ar" violates not-null constraint` — the form
  sent an empty name. Validate before inserting.
- `duplicate key value violates unique constraint "shop_commercial_register_key"`
  — that register number is already in the database. Show the user a message;
  don't let the page 500.

After a successful insert, redirect:

```python
from fastapi.responses import RedirectResponse
return RedirectResponse(f"/shops/{new_id}", status_code=303)
```

---

## Optional, if there's time

`GET /search?q=...` — search by shop name or phone number.

```sql
SELECT DISTINCT s.id, s.name_ar, s.name_en
FROM shop s
LEFT JOIN branch b ON b.shop_id = s.id
WHERE s.name_ar ILIKE %s OR s.name_en ILIKE %s OR b.phone_number LIKE %s
ORDER BY s.name_ar;
```

Pass the same value three times, wrapped in `%`:
`("%" + q + "%", "%" + q + "%", "%" + q + "%")`

`ILIKE` is case-insensitive `LIKE`. `%` inside the value means "anything here".

---

## Rules

1. **Never build SQL with f-strings or `+`.** Always `%s` and a tuple. Anything
   else is an SQL injection hole and the professor may well ask about it.
2. **Every text field can be `NULL`** except `name_ar`, `address`, and the phone
   numbers. Handle it in the template, not with a try/except.
3. **Arabic needs `dir="rtl"`** on the element, or it renders backwards.
4. **Don't touch `schema.sql` or `seed.sql`.** Message Mohamed instead.
