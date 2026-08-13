-- Ready-made queries for every page. Copy these; don't write your own.
-- %s is a placeholder — pass the value as a parameter, never paste it in.

-- 1. Home page: the 7 trades
SELECT id, name_ar, name_en
FROM trade
ORDER BY id;

-- 2. Shops in one trade, with branch counts
SELECT s.id, s.name_ar, s.name_en, s.commercial_register,
       count(b.id) AS branch_count
FROM shop s
JOIN shop_trade st ON st.shop_id = s.id
LEFT JOIN branch b ON b.shop_id = s.id
WHERE st.trade_id = %s
GROUP BY s.id, s.name_ar, s.name_en, s.commercial_register
ORDER BY s.name_ar;

-- 3a. One shop
SELECT id, name_ar, name_en, commercial_register, bank_account, technical_capacity
FROM shop
WHERE id = %s;

-- 3b. That shop's branches, with staff counts
SELECT b.id, b.branch_name, b.address, b.phone_number,
       count(e.id) AS staff_count
FROM branch b
LEFT JOIN employee e ON e.branch_id = b.id
WHERE b.shop_id = %s
GROUP BY b.id, b.branch_name, b.address, b.phone_number
ORDER BY b.id;

-- 3c. That shop's trades
SELECT t.name_ar
FROM trade t
JOIN shop_trade st ON st.trade_id = t.id
WHERE st.shop_id = %s
ORDER BY t.id;

-- 5. Add a shop
INSERT INTO shop(name_ar, name_en, commercial_register, bank_account, technical_capacity)
VALUES (%s, %s, %s, %s, %s)
RETURNING id;

-- 6. Search by name or phone (optional)
SELECT DISTINCT s.id, s.name_ar, s.name_en
FROM shop s
LEFT JOIN branch b ON b.shop_id = s.id
WHERE s.name_ar ILIKE %s OR s.name_en ILIKE %s OR b.phone_number LIKE %s
ORDER BY s.name_ar;

-- Employees of one branch
SELECT name_ar, name_en, national_id, phone_number
FROM employee
WHERE branch_id = %s
ORDER BY id;
