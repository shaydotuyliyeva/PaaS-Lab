
import os

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort
)

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "local-development-key"
)

DATABASE_URL = (
    os.getenv("DATABASE_URL_POOLED")
    or os.getenv("DATABASE_URL")
)


def get_db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL topilmadi!")

    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row
    )


@app.route("/")
def home():
    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) AS total_students,
                    COALESCE(AVG(score), 0) AS average_score
                FROM students
            """)
            stats = cursor.fetchone()

    return render_template(
        "index.html",
        stats=stats
    )


@app.route("/students")
def students():
    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM students
                ORDER BY id DESC
            """)
            student_list = cursor.fetchall()

    return render_template(
        "students.html",
        students=student_list
    )


@app.route("/students/add", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":

        full_name = request.form.get(
            "full_name", ""
        ).strip()

        group_name = request.form.get(
            "group_name", ""
        ).strip()

        subject = request.form.get(
            "subject", ""
        ).strip() or "Bulutli texnologiyalar"

        try:
            score = int(request.form.get("score", "0"))
        except ValueError:
            flash("Ball butun son bo'lishi kerak!")
            return render_template("add_student.html")

        if not full_name or not group_name:
            flash("F.I.Sh. va guruhni to'ldiring!")
            return render_template("add_student.html")

        if not 0 <= score <= 100:
            flash("Ball 0 dan 100 gacha bo'lishi kerak!")
            return render_template("add_student.html")

        with get_db() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO students
                    (full_name, group_name, subject, score)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (full_name, group_name, subject, score))

                new_id = cursor.fetchone()["id"]

        flash("Talaba muvaffaqiyatli qo'shildi!")
        return redirect(
            url_for("student_detail", student_id=new_id)
        )

    return render_template("add_student.html")


@app.route("/students/<int:student_id>")
def student_detail(student_id):
    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM students
                WHERE id = %s
            """, (student_id,))

            student = cursor.fetchone()

    if student is None:
        abort(404)

    return render_template(
        "student_detail.html",
        student=student
    )


@app.route("/students/<int:student_id>/score", methods=["POST"])
def update_score(student_id):
    try:
        score = int(request.form.get("score", ""))
    except ValueError:
        flash("Ball butun son bo'lishi kerak!")
        return redirect(
            url_for("student_detail", student_id=student_id)
        )

    if not 0 <= score <= 100:
        flash("Ball 0 dan 100 gacha bo'lishi kerak!")
        return redirect(
            url_for("student_detail", student_id=student_id)
        )

    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE students
                SET score = %s
                WHERE id = %s
                RETURNING id
            """, (score, student_id))

            result = cursor.fetchone()

    if result is None:
        abort(404)

    flash("Talaba bali muvaffaqiyatli yangilandi!")

    return redirect(
        url_for("student_detail", student_id=student_id)
    )


if __name__ == "__main__":
    app.run()


