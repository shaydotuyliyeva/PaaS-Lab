
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = (
    os.getenv("DATABASE_URL_POOLED")
    or os.getenv("DATABASE_URL")
)

if not DATABASE_URL:
    raise RuntimeError("Ma'lumotlar bazasi manzili topilmadi!")

with psycopg.connect(DATABASE_URL) as connection:
    with connection.cursor() as cursor:

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id BIGSERIAL PRIMARY KEY,
                full_name VARCHAR(150) NOT NULL,
                group_name VARCHAR(50) NOT NULL,
                subject VARCHAR(120) NOT NULL
                    DEFAULT 'Bulutli texnologiyalar',
                score INTEGER NOT NULL DEFAULT 0
                    CHECK (score BETWEEN 0 AND 100),
                created_at TIMESTAMPTZ NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            );
        """)

    connection.commit()

print("Talabalar jadvali muvaffaqiyatli yaratildi!")
