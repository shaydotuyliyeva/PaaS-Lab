
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

database_url = (
    os.getenv("DATABASE_URL_POOLED")
    or os.getenv("DATABASE_URL")
)

if not database_url:
    print("XATOLIK: DATABASE_URL topilmadi!")
else:
    try:
        connection = psycopg.connect(database_url)

        cursor = connection.cursor()
        cursor.execute(
            "SELECT current_database(), current_user"
        )

        result = cursor.fetchone()

        print("Neon PostgreSQL bilan aloqa o'rnatildi!")
        print("Ma'lumotlar bazasi:", result[0])
        print("Foydalanuvchi:", result[1])

        cursor.close()
        connection.close()

    except Exception as error:
        print("Ulanishda xatolik:", error)
