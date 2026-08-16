import os
import re
import psycopg
from fastapi import FastAPI, HTTPException, Request, Form
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

app = FastAPI(title="Trades Directory")

# ربط مجلد الملفات الثابتة
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

def query(sql, params=()):
    """Run a SELECT and return a list of dicts, one per row."""
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            columns = [c[0] for c in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]

def execute(sql, params=()):
    """Run an INSERT/UPDATE/DELETE."""
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()

# 🔍 الرئيسية والبحث
@app.get("/")
def home(request: Request, q: str = None):
    q_clean = q.strip() if q and q.strip() else None
    
    if q_clean:
        search_param = f"%{q_clean}%"
        # البحث في الأقسام
        trades = query(
            "SELECT * FROM trade WHERE name_ar ILIKE %s OR name_en ILIKE %s ORDER BY name_ar;", 
            (search_param, search_param)
        )
        # البحث في المحلات بالاسم العربي أو الإنجليزي
        shops = query(
            "SELECT * FROM shop WHERE name_ar ILIKE %s OR name_en ILIKE %s ORDER BY name_ar;",
            (search_param, search_param)
        )
    else:
        trades = query("SELECT * FROM trade ORDER BY name_ar;")
        shops = []

    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"trades": trades, "shops": shops, "q": q_clean or ""}
    )

@app.get("/trades/{trade_id}")
def trade_details(request: Request, trade_id: int):
    trade_data = query("SELECT * FROM trade WHERE id = %s;", (trade_id,))
    if not trade_data:
        raise HTTPException(status_code=404, detail="القسم غير موجود")
    trade = trade_data[0]

    shops = query("""
        SELECT s.* FROM shop s
        JOIN shop_trade st ON s.id = st.shop_id
        WHERE st.trade_id = %s;
    """, (trade_id,))

    return templates.TemplateResponse(
        request=request,
        name="trade.html",
        context={"trade": trade, "shops": shops}
    )

@app.get("/shops/{shop_id}")
def shop_details(request: Request, shop_id: int):
    shop_data = query("SELECT * FROM shop WHERE id = %s;", (shop_id,))
    if not shop_data:
        raise HTTPException(status_code=404, detail="المحل غير موجود")
    shop = shop_data[0]

    trades = query("SELECT t.* FROM trade t JOIN shop_trade st ON t.id = st.trade_id WHERE st.shop_id = %s;", (shop_id,))

    # LEFT JOIN, not JOIN: a branch with no employees recorded must still appear,
    # with a count of 0. An inner join would silently hide it.
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

    # Every employee across this shop's branches, keyed by branch id so the
    # template can list them under the right one.
    employee_rows = query(
        """
        SELECT e.id, e.name_ar, e.name_en, e.national_id, e.phone_number,
               e.branch_id
        FROM employee e
        JOIN branch b ON b.id = e.branch_id
        WHERE b.shop_id = %s
        ORDER BY e.branch_id, e.id;
        """,
        (shop_id,),
    )
    employees_by_branch = {}
    for row in employee_rows:
        employees_by_branch.setdefault(row["branch_id"], []).append(row)

    return templates.TemplateResponse(
        request=request,
        name="shop.html",
        context={
            "shop": shop,
            "trades": trades,
            "branches": branches,
            "employees_by_branch": employees_by_branch,
        },
    )

@app.get("/add-shop")
def add_shop_page(request: Request):
    trades = query("SELECT * FROM trade ORDER BY name_ar;")
    return templates.TemplateResponse(request=request, name="add_shop.html", context={"trades": trades})

# 🛠️ دالة إضافة محل مع التقاط خطأ التكرار بشكل أنيق
@app.post("/add-shop")
def add_shop_action(
    request: Request,
    name_ar: str = Form(...),
    name_en: str = Form(""),
    commercial_register: str = Form(""),
    bank_account: str = Form(""),
    technical_capacity: str = Form(""),
    trade_id: int = Form(...)
):
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # 1. إدخال المحل الجديد
                cur.execute(
                    """
                    INSERT INTO shop (name_ar, name_en, commercial_register, bank_account, technical_capacity)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id;
                    """,
                    (
                        name_ar.strip(),
                        name_en.strip() if name_en and name_en.strip() else None,
                        commercial_register.strip() if commercial_register and commercial_register.strip() else None,
                        bank_account.strip() if bank_account and bank_account.strip() else None,
                        technical_capacity.strip() if technical_capacity and technical_capacity.strip() else None
                    )
                )
                shop_id = cur.fetchone()[0]

                # 2. ربط المحل بالقسم
                cur.execute(
                    "INSERT INTO shop_trade (shop_id, trade_id) VALUES (%s, %s);",
                    (int(shop_id), int(trade_id))
                )
                conn.commit()

        return RedirectResponse(url=f"/shops/{shop_id}", status_code=303)

    except psycopg.errors.UniqueViolation:
        # إرجاع المستخدم لصفحة الإضافة مع إظهار رسالة تنبيه
        trades = query("SELECT * FROM trade ORDER BY name_ar;")
        return templates.TemplateResponse(
            request=request, 
            name="add_shop.html", 
            context={
                "trades": trades, 
                "error": "رقم السجل التجاري هذا مُسجل بالفعل لمحل آخر، يرجى إدخال رقم مختلف."
            }
        )
    except Exception as e:
        # Log the real error for us; show the user a plain message. Echoing the
        # raw exception back would expose table and column names.
        print(f"Error adding shop: {e}")
        raise HTTPException(status_code=500, detail="حدث خطأ أثناء حفظ المحل.")

@app.get("/shops/{shop_id}/edit")
def edit_shop_page(request: Request, shop_id: int):
    shop_data = query("SELECT * FROM shop WHERE id = %s;", (shop_id,))
    if not shop_data:
        raise HTTPException(status_code=404, detail="المحل غير موجود")
    shop = shop_data[0]
    return templates.TemplateResponse(
        request=request,
        name="edit_shop.html",
        context={"shop": shop}
    )

@app.post("/shops/{shop_id}/edit")
def edit_shop_action(
    request: Request,
    shop_id: int,
    name_ar: str = Form(...),
    name_en: str = Form(""),
    commercial_register: str = Form(""),
    bank_account: str = Form(""),
    technical_capacity: str = Form("")
):
    try:
        execute(
            """
            UPDATE shop
            SET name_ar = %s, name_en = %s, commercial_register = %s, bank_account = %s, technical_capacity = %s
            WHERE id = %s;
            """,
            (
                name_ar.strip(),
                name_en.strip() if name_en and name_en.strip() else None,
                commercial_register.strip() if commercial_register and commercial_register.strip() else None,
                bank_account.strip() if bank_account and bank_account.strip() else None,
                technical_capacity.strip() if technical_capacity and technical_capacity.strip() else None,
                shop_id
            )
        )
        return RedirectResponse(url=f"/shops/{shop_id}", status_code=303)
    except psycopg.errors.UniqueViolation:
        shop_data = query("SELECT * FROM shop WHERE id = %s;", (shop_id,))
        shop = shop_data[0] if shop_data else None
        return templates.TemplateResponse(
            request=request,
            name="edit_shop.html",
            context={
                "shop": shop,
                "error": "رقم السجل التجاري هذا مُسجل بالفعل لمحل آخر."
            }
        )

@app.get("/shops/{shop_id}/add-branch")
def add_branch_page(request: Request, shop_id: int):
    shop_data = query("SELECT * FROM shop WHERE id = %s;", (shop_id,))
    if not shop_data:
        raise HTTPException(status_code=404, detail="المحل غير موجود")
    return templates.TemplateResponse(
        request=request,
        name="add_branch.html",
        context={"shop": shop_data[0], "shop_id": shop_id}
    )

@app.post("/shops/{shop_id}/add-branch")
def add_branch_action(
    request: Request,
    shop_id: int,
    branch_name: str = Form(""),
    address: str = Form(...),
    phone_number: str = Form("")
):
    shop_data = query("SELECT * FROM shop WHERE id = %s;", (shop_id,))
    if not shop_data:
        raise HTTPException(status_code=404, detail="المحل غير موجود")

    address = address.strip()
    phone_number = phone_number.strip()
    branch_name = branch_name.strip() if branch_name and branch_name.strip() else None

    def reject(message):
        return templates.TemplateResponse(
            request=request,
            name="add_branch.html",
            context={
                "shop": shop_data[0],
                "shop_id": shop_id,
                "error": message,
                "form": {
                    "branch_name": branch_name or "",
                    "address": address,
                    "phone_number": phone_number,
                },
            },
            status_code=400,
        )

    # address and phone_number are NOT NULL in schema.sql, and phone_number has
    # a CHECK constraint. Validate here, or an empty form field becomes a 500.
    if not address:
        return reject("يرجى إدخال عنوان الفرع.")
    if not re.fullmatch(r"\+?[0-9]{7,15}", phone_number):
        return reject("يرجى إدخال رقم هاتف صحيح من 7 إلى 15 رقماً.")

    # Branches may deliberately share a phone number — a shop often runs one
    # central line across all of its branches, so there is no UNIQUE to violate.
    try:
        execute(
            """
            INSERT INTO branch (shop_id, branch_name, address, phone_number)
            VALUES (%s, %s, %s, %s);
            """,
            (shop_id, branch_name, address, phone_number),
        )
    except (psycopg.errors.CheckViolation,
            psycopg.errors.NotNullViolation,
            psycopg.errors.StringDataRightTruncation):
        return reject("بيانات الفرع غير صالحة.")
    return RedirectResponse(url=f"/shops/{shop_id}", status_code=303)