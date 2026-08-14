"""
Trades Directory — the web app.

Public pages: the trade list, the shops in a trade, one shop in full, and the
add-shop form. Admin pages (under /admin) add branches to a shop.

Reference SQL lives in ENDPOINTS.md and queries.sql.

Run it:
    pip install "fastapi[standard]" "psycopg[binary]" jinja2
    fastapi dev app_starter.py

Then open http://127.0.0.1:8000
"""

import os
import re

import psycopg
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
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
# Public pages
# ---------------------------------------------------------------------------
@app.get("/")
def home(request: Request):
    trades = query("SELECT id, name_ar, name_en FROM trade ORDER BY id;")
    return templates.TemplateResponse(
        request=request, name="index.html", context={"trades": trades}
    )


@app.get("/trades/{trade_id}")
def trade_detail(request: Request, trade_id: int):
    shops = query(
        """
        SELECT s.id, s.name_ar, s.name_en, s.commercial_register,
               count(b.id) AS branch_count
        FROM shop s
        JOIN shop_trade st ON st.shop_id = s.id
        LEFT JOIN branch b ON b.shop_id = s.id
        WHERE st.trade_id = %s
        GROUP BY s.id, s.name_ar, s.name_en, s.commercial_register
        ORDER BY s.name_ar;
        """,
        (trade_id,),
    )
    trade = query("SELECT id, name_ar FROM trade WHERE id = %s", (trade_id,))
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return templates.TemplateResponse(
        request=request,
        name="trade.html",
        context={"trade": trade[0], "shops": shops},
    )

# NOTE: always call TemplateResponse with these three keyword arguments.
# Older tutorials show TemplateResponse("page.html", {"request": request, ...}).
# That form is removed in current versions and raises:
#     TypeError: cannot use 'tuple' as a dict key
# If you see that error, this is why.


@app.get("/shops/new")
def new_shop(request: Request):
    trades = query("SELECT id, name_ar, name_en FROM trade ORDER BY id;")
    return templates.TemplateResponse(
        request=request,
        name="shop_new.html",
        context={"trades": trades},
    )

@app.get("/shops/{shop_id}")
def shop_detail(request: Request, shop_id: int):
    shops = query(
        """
        SELECT id, name_ar, name_en, commercial_register, bank_account,
               technical_capacity
        FROM shop
        WHERE id = %s;
        """,
        (shop_id,),
    )
    if not shops:
        raise HTTPException(status_code=404, detail="Shop not found")

    branches = query(
        """
        SELECT b.id, b.branch_name, b.address, b.phone_number,
               count(e.id) AS staff_count
        FROM branch b
        LEFT JOIN employee e ON e.branch_id = b.id
        WHERE b.shop_id = %s
        GROUP BY b.id, b.branch_name, b.address, b.phone_number
        ORDER BY b.id;
        """,
        (shop_id,),
    )
    trades = query(
        """
        SELECT t.name_ar
        FROM trade t
        JOIN shop_trade st ON st.trade_id = t.id
        WHERE st.shop_id = %s
        ORDER BY t.id;
        """,
        (shop_id,),
    )
    return templates.TemplateResponse(
        request=request,
        name="shop.html",
        context={"shop": shops[0], "branches": branches, "trades": trades},
    )


# TODO: Protect these admin routes with authentication and authorization before
# exposing them beyond direct local prototype testing.
@app.get("/admin/shops/{shop_id}/branches/new")
def new_branch(request: Request, shop_id: int):
    shops = query("SELECT id, name_ar FROM shop WHERE id = %s", (shop_id,))
    if not shops:
        raise HTTPException(status_code=404, detail="Shop not found")

    return templates.TemplateResponse(
        request=request,
        name="branch_new.html",
        context={"shop": shops[0]},
    )


@app.post("/admin/shops/{shop_id}/branches")
def create_branch(
    request: Request,
    shop_id: int,
    address: str = Form(...),
    phone_number: str = Form(...),
    branch_name: str | None = Form(None),
):
    shops = query("SELECT id, name_ar FROM shop WHERE id = %s", (shop_id,))
    if not shops:
        raise HTTPException(status_code=404, detail="Shop not found")
    shop = shops[0]

    address = address.strip()
    phone_number = phone_number.strip()
    branch_name = branch_name.strip() if branch_name and branch_name.strip() else None
    form_values = {
        "branch_name": branch_name or "",
        "address": address,
        "phone_number": phone_number,
    }

    if not address:
        return templates.TemplateResponse(
            request=request,
            name="branch_new.html",
            context={
                "shop": shop,
                "error": "يرجى إدخال عنوان الفرع.",
                "form": form_values,
            },
            status_code=400,
        )

    if len(phone_number) > 15 or not re.fullmatch(r"\+?[0-9]{7,15}", phone_number):
        return templates.TemplateResponse(
            request=request,
            name="branch_new.html",
            context={
                "shop": shop,
                "error": "يرجى إدخال رقم هاتف صحيح من 7 إلى 15 رقماً.",
                "form": form_values,
            },
            status_code=400,
        )

    # Branches are deliberately allowed to share a phone number: a shop often
    # runs one central line across all of its branches. `branch.phone_number`
    # has NOT NULL and a CHECK in schema.sql, but no UNIQUE — so there is
    # nothing to enforce here and no UniqueViolation to catch.
    try:
        execute(
            """
            INSERT INTO branch(shop_id, branch_name, address, phone_number)
            VALUES (%s, %s, %s, %s);
            """,
            (shop_id, branch_name, address, phone_number),
        )
    except (psycopg.errors.CheckViolation, psycopg.errors.StringDataRightTruncation):
        return templates.TemplateResponse(
            request=request,
            name="branch_new.html",
            context={
                "shop": shop,
                "error": "بيانات الفرع غير صالحة.",
                "form": form_values,
            },
            status_code=400,
        )
    except psycopg.errors.ForeignKeyViolation:
        raise HTTPException(status_code=404, detail="Shop not found")

    return RedirectResponse(url=f"/shops/{shop_id}", status_code=303)


@app.post("/shops")
def create_shop(
    request: Request,
    name_ar: str = Form(...),
    trade_id: int = Form(...),
    name_en: str | None = Form(None),
    commercial_register: str | None = Form(None),
    bank_account: str | None = Form(None),
    technical_capacity: str | None = Form(None),
):
    trades = query("SELECT id, name_ar, name_en FROM trade ORDER BY id;")
    name_ar = name_ar.strip()
    if not name_ar:
        return templates.TemplateResponse(
            request=request,
            name="shop_new.html",
            context={
                "error": "يرجى إدخال اسم المحل بالعربية.",
                "trades": trades,
            },
            status_code=400,
        )

    if not any(trade["id"] == trade_id for trade in trades):
        return templates.TemplateResponse(
            request=request,
            name="shop_new.html",
            context={"error": "الحرفة المختارة غير موجودة.", "trades": trades},
            status_code=400,
        )

    def blank_to_none(value: str | None):
        return value if value and value.strip() else None

    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO shop(
                        name_ar, name_en, commercial_register, bank_account,
                        technical_capacity
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (
                        name_ar,
                        blank_to_none(name_en),
                        blank_to_none(commercial_register),
                        blank_to_none(bank_account),
                        blank_to_none(technical_capacity),
                    ),
                )
                new_id = cur.fetchone()[0]
                cur.execute(
                    """
                    INSERT INTO shop_trade(shop_id, trade_id)
                    VALUES (%s, %s);
                    """,
                    (new_id, trade_id),
                )
    except psycopg.errors.UniqueViolation:
        return templates.TemplateResponse(
            request=request,
            name="shop_new.html",
            context={
                "error": "رقم السجل التجاري مستخدم بالفعل.",
                "trades": trades,
            },
            status_code=400,
        )
    except psycopg.errors.ForeignKeyViolation:
        return templates.TemplateResponse(
            request=request,
            name="shop_new.html",
            context={"error": "الحرفة المختارة غير موجودة.", "trades": trades},
            status_code=400,
        )

    return RedirectResponse(url=f"/shops/{new_id}", status_code=303)
