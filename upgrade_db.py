
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = (
    os.getenv("DATABASE_URL_POOLED")
    or os.getenv("DATABASE_URL")
)

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL topilmadi!")


with psycopg.connect(DATABASE_URL) as connection:

    with connection.cursor() as cursor:

        # Talabalar jadvaliga yangi ustunlar qo'shish
        cursor.execute("""
            ALTER TABLE students
            ADD COLUMN IF NOT EXISTS email VARCHAR(255);
        """)

        cursor.execute("""
            ALTER TABLE students
            ADD COLUMN IF NOT EXISTS password_hash TEXT;
        """)

        # Email takrorlanmasligini ta'minlash
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_students_email_unique
            ON students(email)
            WHERE email IS NOT NULL;
        """)

        # Quiz natijalarini saqlash jadvali
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id BIGSERIAL PRIMARY KEY,

                student_id BIGINT NOT NULL
                    REFERENCES students(id)
                    ON DELETE CASCADE,

                correct_answers INTEGER NOT NULL
                    CHECK (correct_answers BETWEEN 0 AND 10),

                total_questions INTEGER NOT NULL
                    DEFAULT 10
                    CHECK (total_questions = 10),

                score INTEGER NOT NULL
                    CHECK (score BETWEEN 0 AND 100),

                completed_at TIMESTAMPTZ NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Talabaning test tarixini tez qidirish
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_quiz_attempts_student_completed
            ON quiz_attempts(student_id, completed_at DESC);
        """)

    connection.commit()


print("Quiz ma'lumotlar bazasi muvaffaqiyatli tayyorlandi!")
