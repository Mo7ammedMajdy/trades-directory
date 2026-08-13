"""
Trades Directory — starter app.

Page 1 of 5 is finished. Copy its pattern for the other four.
Every query you need is in ENDPOINTS.md and queries.sql.

Run it:
    pip install "fastapi[standard]" "psycopg[binary]" jinja2
    fastapi dev app_starter.py

Then open http://127.0.0.1:8000
"""

import os

import psycopg
from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates

# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------
# On Linux this works as-is: it connects as your own OS user.
#
# On Windows you must supply the postgres user and the password you set during
# installation. Either edit the fallback string below, or set the environment
# variable before running:
#
#     set DATABASE_URL=dbname=trades_db user=postgres password=YOUR_PASSWORD host=localhost
#
DATABASE_URL = os.environ.get("DATABASE_URL", "dbname=trades_db")

app = FastAPI(title="Trades Directory")
templates = Jinja2Templates(directory="templates")


def query(sql, params=()):
    """Run a SELECT and return a list of dicts, one per row.

    Always pass values through `params` — never build the SQL string with
    f-strings or +. That is how SQL injection happens.

        query("SELECT * FROM shop WHERE id = %s", (shop_id,))
    """
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            columns = [c.name for c in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def execute(sql, params=()):
    """Run an INSERT/UPDATE/DELETE. Returns the first row if the SQL has
    RETURNING, otherwise None."""
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone() if cur.description else None
            conn.commit()
            return row


# ---------------------------------------------------------------------------
# PAGE 1 of 5 — DONE. This is your template for the rest.
# ---------------------------------------------------------------------------
@app.get("/")
def home(request: Request):
    trades = query("SELECT id, name_ar, name_en FROM trade ORDER BY id;")
    return templates.TemplateResponse(
        request=request, name="index.html", context={"trades": trades}
    )


# ---------------------------------------------------------------------------
# PAGE 2 of 5 — TODO (Wageh)
#
# Uncomment, then create templates/trade.html.
# The SQL is in ENDPOINTS.md section 2.
# ---------------------------------------------------------------------------
# @app.get("/trades/{trade_id}")
# def trade_detail(request: Request, trade_id: int):
#     shops = query(
#         """
#         SELECT s.id, s.name_ar, s.name_en, s.commercial_register,
#                count(b.id) AS branch_count
#         FROM shop s
#         JOIN shop_trade st ON st.shop_id = s.id
#         LEFT JOIN branch b ON b.shop_id = s.id
#         WHERE st.trade_id = %s
#         GROUP BY s.id, s.name_ar, s.name_en, s.commercial_register
#         ORDER BY s.name_ar;
#         """,
#         (trade_id,),
#     )
#     trade = query("SELECT id, name_ar FROM trade WHERE id = %s", (trade_id,))
#     if not trade:
#         raise HTTPException(status_code=404, detail="Trade not found")
#     return templates.TemplateResponse(
#         request=request,
#         name="trade.html",
#         context={"trade": trade[0], "shops": shops},
#     )
#
# NOTE: always call TemplateResponse with these three keyword arguments.
# Older tutorials show TemplateResponse("page.html", {"request": request, ...}).
# That form is removed in current versions and raises:
#     TypeError: cannot use 'tuple' as a dict key
# If you see that error, this is why.


# ---------------------------------------------------------------------------
# PAGE 3 of 5 — TODO   GET  /shops/{shop_id}     (ENDPOINTS.md section 3)
# PAGE 4 of 5 — TODO   GET  /shops/new           (ENDPOINTS.md section 4)
# PAGE 5 of 5 — TODO   POST /shops               (ENDPOINTS.md section 5)
# ---------------------------------------------------------------------------
