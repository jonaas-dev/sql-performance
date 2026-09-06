-- Schema only. Data is loaded by sql/seed.py so the row count follows
-- DB_SEED_SIZE instead of being hardcoded here.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT gen_random_uuid(),
    name VARCHAR(100),
    surname VARCHAR(100),
    email VARCHAR(100),
    address VARCHAR(200),
    city VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    phone VARCHAR(15),
    age INT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    bio TEXT
);
