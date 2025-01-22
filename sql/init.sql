-- Enable the necessary extension for UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create the table with 15 columns
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT gen_random_uuid(),
    name VARCHAR(100),
    surname VARCHAR(100),
    email VARCHAR(100),
    direction VARCHAR(200),
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

-- Insert synthetic data into the table
DO $$
DECLARE
    first_names TEXT[] := ARRAY['John', 'Jane', 'Alice', 'Bob', 'Charlie', 'Emily', 'Daniel', 'Sophia', 'Liam', 'Olivia'];
    last_names TEXT[] := ARRAY['Doe', 'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Martinez', 'Davis', 'Miller'];
    cities TEXT[] := ARRAY['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose'];
    countries TEXT[] := ARRAY['USA', 'Canada', 'UK', 'Germany', 'France', 'Spain', 'Italy', 'Australia', 'India', 'Brazil'];
    i INT;
BEGIN
    FOR i IN 1..10000000 LOOP
        INSERT INTO users (name, surname, email, direction, city, country, postal_code, phone, age, bio)
        VALUES (
            first_names[(random() * array_length(first_names, 1))::INT + 1], -- Random first name
            last_names[(random() * array_length(last_names, 1))::INT + 1], -- Random last name
            lower(md5(random()::TEXT || clock_timestamp()::TEXT) || '@example.com'), -- Random email
            'Street ' || (random() * 100)::INT || ', Apt ' || (random() * 50)::INT, -- Random address
            cities[(random() * array_length(cities, 1))::INT + 1], -- Random city
            countries[(random() * array_length(countries, 1))::INT + 1], -- Random country
            LPAD((random() * 99999)::INT::TEXT, 5, '0'), -- Random postal code
            '+1-' || LPAD((random() * 999)::INT::TEXT, 3, '0') || '-' || LPAD((random() * 999999)::INT::TEXT, 6, '0'), -- Random phone number
            (random() * 60 + 18)::INT, -- Random age between 18 and 78
            'Bio for user ' || i -- Synthetic bio
        );
    END LOOP;
END $$;
