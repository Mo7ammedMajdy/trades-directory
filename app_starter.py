import os
import psycopg
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Database connection
DATABASE_URL = "dbname=trades_db user=postgres password=1234 host=127.0.0.1 port=1111 client_encoding='UTF8'"

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
    trade = trade_data[0] if trade_data else None
    
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
    shop = shop_data[0] if shop_data else None
    
    trades = query("SELECT t.* FROM trade t JOIN shop_trade st ON t.id = st.trade_id WHERE st.shop_id = %s;", (shop_id,))
    branches = query("SELECT * FROM branch WHERE shop_id = %s;", (shop_id,))

    return templates.TemplateResponse(
        request=request,
        name="shop.html",
        context={"shop": shop, "trades": trades, "branches": branches}
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
        print(f"Error adding shop: {e}")
        raise HTTPException(status_code=500, detail=f"حدث خطأ أثناء حفظ المحل: {e}")

@app.get("/shops/{shop_id}/edit")
def edit_shop_page(request: Request, shop_id: int):
    shop_data = query("SELECT * FROM shop WHERE id = %s;", (shop_id,))
    shop = shop_data[0] if shop_data else None
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
    shop = shop_data[0] if shop_data else None
    return templates.TemplateResponse(
        request=request,
        name="add_branch.html",
        context={"shop": shop, "shop_id": shop_id}
    )

@app.post("/shops/{shop_id}/add-branch")
def add_branch_action(
    shop_id: int,
    branch_name: str = Form(""),
    address: str = Form(...),
    phone_number: str = Form("")
):
    execute(
        """
        INSERT INTO branch (shop_id, branch_name, address, phone_number)
        VALUES (%s, %s, %s, %s);
        """,
        (
            shop_id,
            branch_name.strip() if branch_name and branch_name.strip() else None,
            address.strip(),
            phone_number.strip() if phone_number and phone_number.strip() else None
        )
    )
    return RedirectResponse(url=f"/shops/{shop_id}", status_code=303)