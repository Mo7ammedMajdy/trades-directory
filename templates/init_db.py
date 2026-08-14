import psycopg

DATABASE_URL = "dbname=trades_db user=postgres password=1234 host=127.0.0.1 port=1111 client_encoding='UTF8'"

print("🔄 جاري إعادة ضبط وتنظيف قاعدة البيانات من الصفر...")

try:
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            # 1. حذف الجداول القديمة تماماً وإعادة إنشاء الـ schema
            cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
            conn.commit()

    # 2. تنفيذ ملف بناء الجداول (schema.sql)
    with open("schema.sql", "r", encoding="utf-8") as f:
        schema_script = f.read()

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(schema_script)
            conn.commit()

    # 3. تنفيذ ملف إدخال البيانات الأولية (seed.sql)
    with open("seed.sql", "r", encoding="utf-8") as f:
        seed_script = f.read()

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(seed_script)
            conn.commit()

    print("✅ تم إعادة ضبط قاعدة البيانات وإدخال البيانات بنجاح تام!")

except Exception as e:
    print(f"❌ حدث خطأ أثناء إعادة الضبط: {e}")