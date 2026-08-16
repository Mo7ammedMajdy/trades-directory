\encoding UTF8
CREATE TABLE trade(
    id                      SERIAL PRIMARY KEY,
    name_en                 TEXT NOT NULL UNIQUE,
    name_ar                 TEXT NOT NULL UNIQUE
);
CREATE TABLE shop(
    id                      SERIAL PRIMARY KEY,
    name_en                 TEXT,
    name_ar                 TEXT NOT NULL,
    commercial_register     TEXT UNIQUE,
    bank_account            TEXT,
    technical_capacity      TEXT
);
CREATE TABLE branch(
    id                      SERIAL PRIMARY KEY,
    shop_id                 INTEGER NOT NULL REFERENCES shop(id) ON DELETE CASCADE,
    address                 TEXT NOT NULL,
    branch_name             TEXT,
    phone_number            VARCHAR(15) NOT NULL CHECK(phone_number ~ '^\+?[0-9]{7,15}$')
);
CREATE TABLE employee(
    id                      SERIAL PRIMARY KEY,
    name_ar                 TEXT NOT NULL,
    name_en                 TEXT,
    branch_id               INTEGER NOT NULL REFERENCES branch(id) ON DELETE CASCADE,
    national_id             TEXT UNIQUE CHECK (national_id ~ '^[0-9]{14}$'),
    phone_number            VARCHAR(15) NOT NULL CHECK(phone_number ~ '^\+?[0-9]{7,15}$')
);
CREATE TABLE shop_trade(
    shop_id                 INTEGER NOT NULL REFERENCES shop(id) ON DELETE CASCADE,
    trade_id                INTEGER NOT NULL REFERENCES trade(id) ON DELETE CASCADE,
    PRIMARY KEY             (shop_id , trade_id)
);
