"""
Trades Directory — internal admin application.

A back-office tool for maintaining a directory of tradesmen and contracting
shops. Full create/read/update/delete on all five tables.

Run it:
    pip install "fastapi[standard]" "psycopg[binary]" jinja2
    fastapi dev app_starter.py

Then open http://127.0.0.1:8000

Reference SQL lives in ENDPOINTS.md and queries.sql.
"""

import os
import re

import psycopg
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------
# On Linux this works as-is: it connects as your own OS user.
#
# If your Postgres needs a user, password or a non-default port, set the
# environment variable rather than editing this line — a password committed to
# the repository is a password everyone with the link now knows.
#
#   Linux/macOS:  export DATABASE_URL="dbname=trades_db user=postgres password=... host=127.0.0.1"
#   Windows:      set DATABASE_URL=dbname=trades_db user=postgres password=... host=127.0.0.1
#
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "dbname=trades_db client_encoding='UTF8'"
)

app = FastAPI(title="Trades Directory — Admin")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def query(sql, params=()):
    """Run a SELECT and return a list of dicts, one per row.

    Values always travel through `params` — never formatted into the SQL
    string. That is what makes SQL injection impossible.
    """
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            columns = [c.name for c in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def one(sql, params=()):
    """Return a single row, or None."""
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql, params=()):
    """Run an INSERT/UPDATE/DELETE. Returns the first row if the statement has
    a RETURNING clause, otherwise None."""
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone() if cur.description else None
            conn.commit()
            return row


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
PHONE_RE = re.compile(r"\+?[0-9]{7,15}")
NATIONAL_ID_RE = re.compile(r"[0-9]{14}")


def clean(value):
    """Empty form fields arrive as '' — store NULL instead, so 'no value' and
    'the empty string' don't become two different things in the data."""
    return value.strip() if value and value.strip() else None


def page(request, name, **context):
    return templates.TemplateResponse(request=request, name=name, context=context)


def fail(request, name, message, status=400, **context):
    return templates.TemplateResponse(
        request=request, name=name, context={"error": message, **context},
        status_code=status,
    )


def get_shop_or_404(shop_id):
    shop = one("SELECT * FROM shop WHERE id = %s;", (shop_id,))
    if not shop:
        raise HTTPException(status_code=404, detail="المحل غير موجود")
    return shop


def get_trade_or_404(trade_id):
    trade = one("SELECT * FROM trade WHERE id = %s;", (trade_id,))
    if not trade:
        raise HTTPException(status_code=404, detail="القسم غير موجود")
    return trade


def get_branch_or_404(branch_id):
    branch = one(
        """
        SELECT b.*, s.name_ar AS shop_name, s.id AS shop_id
        FROM branch b JOIN shop s ON s.id = b.shop_id
        WHERE b.id = %s;
        """,
        (branch_id,),
    )
    if not branch:
        raise HTTPException(status_code=404, detail="الفرع غير موجود")
    return branch


def get_employee_or_404(employee_id):
    emp = one(
        """
        SELECT e.*, b.branch_name, b.address AS branch_address,
               s.id AS shop_id, s.name_ar AS shop_name
        FROM employee e
        JOIN branch b ON b.id = e.branch_id
        JOIN shop s ON s.id = b.shop_id
        WHERE e.id = %s;
        """,
        (employee_id,),
    )
    if not emp:
        raise HTTPException(status_code=404, detail="العامل غير موجود")
    return emp


def all_trades():
    return query("SELECT id, name_ar, name_en FROM trade ORDER BY id;")


# ---------------------------------------------------------------------------
# Dashboard and search
# ---------------------------------------------------------------------------
@app.get("/")
def dashboard(request: Request, q: str = ""):
    q_clean = q.strip()

    counts = one(
        """
        SELECT (SELECT count(*) FROM trade)      AS trades,
               (SELECT count(*) FROM shop)       AS shops,
               (SELECT count(*) FROM branch)     AS branches,
               (SELECT count(*) FROM employee)   AS employees,
               (SELECT count(*) FROM shop_trade) AS links;
        """
    )

    results = None
    if q_clean:
        pattern = f"%{q_clean}%"
        # DISTINCT: a shop with three branches would otherwise appear three
        # times when the match came from a branch phone number.
        results = query(
            """
            SELECT DISTINCT s.id, s.name_ar, s.name_en, s.commercial_register
            FROM shop s
            LEFT JOIN branch b ON b.shop_id = s.id
            WHERE s.name_ar ILIKE %s
               OR s.name_en ILIKE %s
               OR s.commercial_register ILIKE %s
               OR b.phone_number LIKE %s
            ORDER BY s.name_ar;
            """,
            (pattern, pattern, pattern, pattern),
        )

    trades = query(
        """
        SELECT t.id, t.name_ar, t.name_en, count(st.shop_id) AS shop_count
        FROM trade t
        LEFT JOIN shop_trade st ON st.trade_id = t.id
        GROUP BY t.id, t.name_ar, t.name_en
        ORDER BY t.id;
        """
    )
    return page(request, "index.html", counts=counts, trades=trades,
                results=results, q=q_clean)


# ---------------------------------------------------------------------------
# Trades
# ---------------------------------------------------------------------------
@app.get("/trades")
def trades_list(request: Request):
    trades = query(
        """
        SELECT t.id, t.name_ar, t.name_en, count(st.shop_id) AS shop_count
        FROM trade t
        LEFT JOIN shop_trade st ON st.trade_id = t.id
        GROUP BY t.id, t.name_ar, t.name_en
        ORDER BY t.id;
        """
    )
    return page(request, "trades.html", trades=trades)


@app.get("/trades/new")
def trade_new(request: Request):
    return page(request, "trade_form.html", trade=None, form={})


@app.post("/trades/new")
def trade_create(request: Request,
                 name_ar: str = Form(...), name_en: str = Form(...)):
    form = {"name_ar": name_ar.strip(), "name_en": name_en.strip()}
    if not form["name_ar"] or not form["name_en"]:
        return fail(request, "trade_form.html",
                    "الاسم بالعربية والإنجليزية مطلوبان.", trade=None, form=form)
    try:
        row = execute(
            "INSERT INTO trade (name_ar, name_en) VALUES (%s, %s) RETURNING id;",
            (form["name_ar"], form["name_en"]),
        )
    except psycopg.errors.UniqueViolation:
        return fail(request, "trade_form.html",
                    "يوجد قسم بهذا الاسم بالفعل.", trade=None, form=form)
    return RedirectResponse(url=f"/trades/{row[0]}", status_code=303)


@app.get("/trades/{trade_id}/edit")
def trade_edit(request: Request, trade_id: int):
    trade = get_trade_or_404(trade_id)
    return page(request, "trade_form.html", trade=trade, form=trade)


@app.post("/trades/{trade_id}/edit")
def trade_update(request: Request, trade_id: int,
                 name_ar: str = Form(...), name_en: str = Form(...)):
    trade = get_trade_or_404(trade_id)
    form = {"name_ar": name_ar.strip(), "name_en": name_en.strip()}
    if not form["name_ar"] or not form["name_en"]:
        return fail(request, "trade_form.html",
                    "الاسم بالعربية والإنجليزية مطلوبان.", trade=trade, form=form)
    try:
        execute("UPDATE trade SET name_ar = %s, name_en = %s WHERE id = %s;",
                (form["name_ar"], form["name_en"], trade_id))
    except psycopg.errors.UniqueViolation:
        return fail(request, "trade_form.html",
                    "يوجد قسم آخر بهذا الاسم.", trade=trade, form=form)
    return RedirectResponse(url=f"/trades/{trade_id}", status_code=303)


@app.post("/trades/{trade_id}/delete")
def trade_delete(trade_id: int):
    get_trade_or_404(trade_id)
    # ON DELETE CASCADE on shop_trade removes the links; the shops themselves
    # are untouched, because a shop is not owned by a trade.
    execute("DELETE FROM trade WHERE id = %s;", (trade_id,))
    return RedirectResponse(url="/trades", status_code=303)


@app.get("/trades/{trade_id}")
def trade_detail(request: Request, trade_id: int):
    trade = get_trade_or_404(trade_id)
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
    return page(request, "trade.html", trade=trade, shops=shops)


# ---------------------------------------------------------------------------
# Shops
# ---------------------------------------------------------------------------
@app.get("/shops")
def shops_list(request: Request):
    shops = query(
        """
        SELECT s.id, s.name_ar, s.name_en, s.commercial_register,
               count(DISTINCT b.id)  AS branch_count,
               count(DISTINCT st.trade_id) AS trade_count
        FROM shop s
        LEFT JOIN branch b ON b.shop_id = s.id
        LEFT JOIN shop_trade st ON st.shop_id = s.id
        GROUP BY s.id, s.name_ar, s.name_en, s.commercial_register
        ORDER BY s.id;
        """
    )
    return page(request, "shops.html", shops=shops)


@app.get("/shops/new")
def shop_new(request: Request):
    return page(request, "shop_form.html", shop=None, form={},
                trades=all_trades(), selected=[])


@app.post("/shops/new")
def shop_create(request: Request,
                name_ar: str = Form(...),
                name_en: str = Form(""),
                commercial_register: str = Form(""),
                bank_account: str = Form(""),
                technical_capacity: str = Form(""),
                trade_ids: list[int] = Form(default=[])):
    form = {
        "name_ar": name_ar.strip(), "name_en": name_en.strip(),
        "commercial_register": commercial_register.strip(),
        "bank_account": bank_account.strip(),
        "technical_capacity": technical_capacity.strip(),
    }
    reject = lambda msg: fail(request, "shop_form.html", msg, shop=None,
                              form=form, trades=all_trades(), selected=trade_ids)

    if not form["name_ar"]:
        return reject("اسم المحل بالعربية مطلوب.")
    if not trade_ids:
        return reject("اختر قسماً واحداً على الأقل.")

    try:
        # The shop and its trade links are written in one transaction. A shop
        # that belonged to no trade would appear on no page — invisible the
        # moment it was created — so either all of it is written or none is.
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO shop (name_ar, name_en, commercial_register,
                                      bank_account, technical_capacity)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id;
                    """,
                    (form["name_ar"], clean(form["name_en"]),
                     clean(form["commercial_register"]),
                     clean(form["bank_account"]),
                     clean(form["technical_capacity"])),
                )
                new_id = cur.fetchone()[0]
                for tid in trade_ids:
                    cur.execute(
                        "INSERT INTO shop_trade (shop_id, trade_id) VALUES (%s, %s);",
                        (new_id, tid),
                    )
    except psycopg.errors.UniqueViolation:
        return reject("رقم السجل التجاري مسجل بالفعل لمحل آخر.")
    except psycopg.errors.ForeignKeyViolation:
        return reject("أحد الأقسام المختارة غير موجود.")
    return RedirectResponse(url=f"/shops/{new_id}", status_code=303)


@app.get("/shops/{shop_id}/edit")
def shop_edit(request: Request, shop_id: int):
    shop = get_shop_or_404(shop_id)
    selected = [r["trade_id"] for r in
                query("SELECT trade_id FROM shop_trade WHERE shop_id = %s;", (shop_id,))]
    return page(request, "shop_form.html", shop=shop, form=shop,
                trades=all_trades(), selected=selected)


@app.post("/shops/{shop_id}/edit")
def shop_update(request: Request, shop_id: int,
                name_ar: str = Form(...),
                name_en: str = Form(""),
                commercial_register: str = Form(""),
                bank_account: str = Form(""),
                technical_capacity: str = Form("")):
    shop = get_shop_or_404(shop_id)
    form = {
        "name_ar": name_ar.strip(), "name_en": name_en.strip(),
        "commercial_register": commercial_register.strip(),
        "bank_account": bank_account.strip(),
        "technical_capacity": technical_capacity.strip(),
    }
    selected = [r["trade_id"] for r in
                query("SELECT trade_id FROM shop_trade WHERE shop_id = %s;", (shop_id,))]
    if not form["name_ar"]:
        return fail(request, "shop_form.html", "اسم المحل بالعربية مطلوب.",
                    shop=shop, form=form, trades=all_trades(), selected=selected)
    try:
        execute(
            """
            UPDATE shop SET name_ar = %s, name_en = %s, commercial_register = %s,
                            bank_account = %s, technical_capacity = %s
            WHERE id = %s;
            """,
            (form["name_ar"], clean(form["name_en"]),
             clean(form["commercial_register"]), clean(form["bank_account"]),
             clean(form["technical_capacity"]), shop_id),
        )
    except psycopg.errors.UniqueViolation:
        return fail(request, "shop_form.html",
                    "رقم السجل التجاري مسجل بالفعل لمحل آخر.",
                    shop=shop, form=form, trades=all_trades(), selected=selected)
    return RedirectResponse(url=f"/shops/{shop_id}", status_code=303)


@app.post("/shops/{shop_id}/delete")
def shop_delete(shop_id: int):
    get_shop_or_404(shop_id)
    # ON DELETE CASCADE removes this shop's branches, their employees, and its
    # trade links, in one statement. That is the schema doing the work.
    execute("DELETE FROM shop WHERE id = %s;", (shop_id,))
    return RedirectResponse(url="/shops", status_code=303)


@app.post("/shops/{shop_id}/trades")
def shop_add_trade(shop_id: int, trade_id: int = Form(...)):
    get_shop_or_404(shop_id)
    try:
        execute("INSERT INTO shop_trade (shop_id, trade_id) VALUES (%s, %s);",
                (shop_id, trade_id))
    except (psycopg.errors.UniqueViolation, psycopg.errors.ForeignKeyViolation):
        # Already linked, or the trade was deleted between page load and submit.
        # Either way the end state the user wanted is already true.
        pass
    return RedirectResponse(url=f"/shops/{shop_id}", status_code=303)


@app.post("/shops/{shop_id}/trades/{trade_id}/delete")
def shop_remove_trade(shop_id: int, trade_id: int):
    get_shop_or_404(shop_id)
    execute("DELETE FROM shop_trade WHERE shop_id = %s AND trade_id = %s;",
            (shop_id, trade_id))
    return RedirectResponse(url=f"/shops/{shop_id}", status_code=303)


@app.get("/shops/{shop_id}")
def shop_detail(request: Request, shop_id: int):
    shop = get_shop_or_404(shop_id)
    trades = query(
        """
        SELECT t.id, t.name_ar FROM trade t
        JOIN shop_trade st ON st.trade_id = t.id
        WHERE st.shop_id = %s ORDER BY t.id;
        """,
        (shop_id,),
    )
    # LEFT JOIN so a branch with no employees still appears, with a count of 0.
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
    rows = query(
        """
        SELECT e.id, e.name_ar, e.name_en, e.national_id, e.phone_number, e.branch_id
        FROM employee e JOIN branch b ON b.id = e.branch_id
        WHERE b.shop_id = %s ORDER BY e.branch_id, e.id;
        """,
        (shop_id,),
    )
    employees_by_branch = {}
    for row in rows:
        employees_by_branch.setdefault(row["branch_id"], []).append(row)

    linked = {t["id"] for t in trades}
    available = [t for t in all_trades() if t["id"] not in linked]

    return page(request, "shop.html", shop=shop, trades=trades,
                branches=branches, employees_by_branch=employees_by_branch,
                available_trades=available)


# ---------------------------------------------------------------------------
# Branches
# ---------------------------------------------------------------------------
@app.get("/shops/{shop_id}/branches/new")
def branch_new(request: Request, shop_id: int):
    shop = get_shop_or_404(shop_id)
    return page(request, "branch_form.html", shop=shop, branch=None, form={})


@app.post("/shops/{shop_id}/branches/new")
def branch_create(request: Request, shop_id: int,
                  address: str = Form(...),
                  phone_number: str = Form(...),
                  branch_name: str = Form("")):
    shop = get_shop_or_404(shop_id)
    form = {"address": address.strip(), "phone_number": phone_number.strip(),
            "branch_name": branch_name.strip()}
    reject = lambda msg: fail(request, "branch_form.html", msg,
                              shop=shop, branch=None, form=form)

    # address and phone_number are NOT NULL, and phone_number has a CHECK
    # constraint. Validate here so the user gets a readable message; the
    # database checks again so no other code path can slip a bad value past.
    if not form["address"]:
        return reject("عنوان الفرع مطلوب.")
    if not PHONE_RE.fullmatch(form["phone_number"]):
        return reject("رقم الهاتف يجب أن يكون من 7 إلى 15 رقماً.")
    try:
        execute(
            """
            INSERT INTO branch (shop_id, branch_name, address, phone_number)
            VALUES (%s, %s, %s, %s);
            """,
            (shop_id, clean(form["branch_name"]), form["address"],
             form["phone_number"]),
        )
    except (psycopg.errors.CheckViolation, psycopg.errors.NotNullViolation,
            psycopg.errors.StringDataRightTruncation):
        return reject("بيانات الفرع غير صالحة.")
    return RedirectResponse(url=f"/shops/{shop_id}", status_code=303)


@app.get("/branches/{branch_id}/edit")
def branch_edit(request: Request, branch_id: int):
    branch = get_branch_or_404(branch_id)
    shop = get_shop_or_404(branch["shop_id"])
    return page(request, "branch_form.html", shop=shop, branch=branch, form=branch)


@app.post("/branches/{branch_id}/edit")
def branch_update(request: Request, branch_id: int,
                  address: str = Form(...),
                  phone_number: str = Form(...),
                  branch_name: str = Form("")):
    branch = get_branch_or_404(branch_id)
    shop = get_shop_or_404(branch["shop_id"])
    form = {"address": address.strip(), "phone_number": phone_number.strip(),
            "branch_name": branch_name.strip()}
    reject = lambda msg: fail(request, "branch_form.html", msg,
                              shop=shop, branch=branch, form=form)
    if not form["address"]:
        return reject("عنوان الفرع مطلوب.")
    if not PHONE_RE.fullmatch(form["phone_number"]):
        return reject("رقم الهاتف يجب أن يكون من 7 إلى 15 رقماً.")
    try:
        execute(
            """
            UPDATE branch SET branch_name = %s, address = %s, phone_number = %s
            WHERE id = %s;
            """,
            (clean(form["branch_name"]), form["address"],
             form["phone_number"], branch_id),
        )
    except (psycopg.errors.CheckViolation, psycopg.errors.NotNullViolation,
            psycopg.errors.StringDataRightTruncation):
        return reject("بيانات الفرع غير صالحة.")
    return RedirectResponse(url=f"/shops/{branch['shop_id']}", status_code=303)


@app.post("/branches/{branch_id}/delete")
def branch_delete(branch_id: int):
    branch = get_branch_or_404(branch_id)
    # Employees of this branch go with it, by ON DELETE CASCADE.
    execute("DELETE FROM branch WHERE id = %s;", (branch_id,))
    return RedirectResponse(url=f"/shops/{branch['shop_id']}", status_code=303)


# ---------------------------------------------------------------------------
# Employees
# ---------------------------------------------------------------------------
@app.get("/branches/{branch_id}/employees/new")
def employee_new(request: Request, branch_id: int):
    branch = get_branch_or_404(branch_id)
    return page(request, "employee_form.html", branch=branch,
                employee=None, form={})


@app.post("/branches/{branch_id}/employees/new")
def employee_create(request: Request, branch_id: int,
                    name_ar: str = Form(...),
                    phone_number: str = Form(...),
                    name_en: str = Form(""),
                    national_id: str = Form("")):
    branch = get_branch_or_404(branch_id)
    form = {"name_ar": name_ar.strip(), "phone_number": phone_number.strip(),
            "name_en": name_en.strip(), "national_id": national_id.strip()}
    reject = lambda msg: fail(request, "employee_form.html", msg,
                              branch=branch, employee=None, form=form)

    if not form["name_ar"]:
        return reject("اسم العامل بالعربية مطلوب.")
    if not PHONE_RE.fullmatch(form["phone_number"]):
        return reject("رقم الهاتف يجب أن يكون من 7 إلى 15 رقماً.")
    # The national ID is optional — informal workers often have no record on
    # file — but if given it must be exactly 14 digits, matching the CHECK.
    if form["national_id"] and not NATIONAL_ID_RE.fullmatch(form["national_id"]):
        return reject("الرقم القومي يجب أن يكون 14 رقماً.")
    try:
        execute(
            """
            INSERT INTO employee (branch_id, name_ar, name_en, national_id,
                                  phone_number)
            VALUES (%s, %s, %s, %s, %s);
            """,
            (branch_id, form["name_ar"], clean(form["name_en"]),
             clean(form["national_id"]), form["phone_number"]),
        )
    except psycopg.errors.UniqueViolation:
        return reject("هذا الرقم القومي مسجل لعامل آخر.")
    except (psycopg.errors.CheckViolation, psycopg.errors.NotNullViolation,
            psycopg.errors.StringDataRightTruncation):
        return reject("بيانات العامل غير صالحة.")
    return RedirectResponse(url=f"/shops/{branch['shop_id']}", status_code=303)


@app.get("/employees/{employee_id}/edit")
def employee_edit(request: Request, employee_id: int):
    emp = get_employee_or_404(employee_id)
    branch = get_branch_or_404(emp["branch_id"])
    return page(request, "employee_form.html", branch=branch,
                employee=emp, form=emp)


@app.post("/employees/{employee_id}/edit")
def employee_update(request: Request, employee_id: int,
                    name_ar: str = Form(...),
                    phone_number: str = Form(...),
                    name_en: str = Form(""),
                    national_id: str = Form("")):
    emp = get_employee_or_404(employee_id)
    branch = get_branch_or_404(emp["branch_id"])
    form = {"name_ar": name_ar.strip(), "phone_number": phone_number.strip(),
            "name_en": name_en.strip(), "national_id": national_id.strip()}
    reject = lambda msg: fail(request, "employee_form.html", msg,
                              branch=branch, employee=emp, form=form)
    if not form["name_ar"]:
        return reject("اسم العامل بالعربية مطلوب.")
    if not PHONE_RE.fullmatch(form["phone_number"]):
        return reject("رقم الهاتف يجب أن يكون من 7 إلى 15 رقماً.")
    if form["national_id"] and not NATIONAL_ID_RE.fullmatch(form["national_id"]):
        return reject("الرقم القومي يجب أن يكون 14 رقماً.")
    try:
        execute(
            """
            UPDATE employee SET name_ar = %s, name_en = %s, national_id = %s,
                                phone_number = %s
            WHERE id = %s;
            """,
            (form["name_ar"], clean(form["name_en"]),
             clean(form["national_id"]), form["phone_number"], employee_id),
        )
    except psycopg.errors.UniqueViolation:
        return reject("هذا الرقم القومي مسجل لعامل آخر.")
    except (psycopg.errors.CheckViolation, psycopg.errors.NotNullViolation,
            psycopg.errors.StringDataRightTruncation):
        return reject("بيانات العامل غير صالحة.")
    return RedirectResponse(url=f"/shops/{emp['shop_id']}", status_code=303)


@app.post("/employees/{employee_id}/delete")
def employee_delete(employee_id: int):
    emp = get_employee_or_404(employee_id)
    execute("DELETE FROM employee WHERE id = %s;", (employee_id,))
    return RedirectResponse(url=f"/shops/{emp['shop_id']}", status_code=303)
