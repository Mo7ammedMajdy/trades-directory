import os
import psycopg
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

# Database connection
# خينا نستخدم 127.0.0.1 لضمان سرعة الاتصال وعدم حدوث Connection Timeout على الويندوز
DATABASE_URL = "dbname=trades_db user=postgres password=KitKat56 host=127.0.0.1 port=5432"

app = FastAPI(title="Trades Directory")
templates = Jinja2Templates(directory="templates")


def query(sql, params=()):
    """Run a SELECT and return a list of dicts, one per row."""
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            columns = [c.name for c in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def execute(sql, params=()):
    """Run an INSERT/UPDATE/DELETE."""
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()


@app.get("/")
def home(request: Request):
    # هنا بقى التعديل الصح لجلب كل المحلات المتاحة
    shops = query("SELECT * FROM shop")
    return templates.TemplateResponse("index.html", {"request": request, "shops": shops})