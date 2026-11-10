

import os
from functools import wraps

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from quiz_data import QUIZ_QUESTIONS, QUIZ_ANSWERS


from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    session
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


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "student_id" not in session:
            return redirect(url_for("login"))

        return view(*args, **kwargs)

    return wrapped_view



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


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get(
            "full_name", ""
        ).strip()

        group_name = request.form.get(
            "group_name", ""
        ).strip()

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get(
            "password", ""
        )

        confirm_password = request.form.get(
            "confirm_password", ""
        )

        if not full_name or not group_name or not email:
            flash("Barcha maydonlarni to'ldiring!")
            return render_template("register.html")

        if "@" not in email:
            flash("Email manzili noto'g'ri!")
            return render_template("register.html")

        if len(password) < 8:
            flash("Parol kamida 8 ta belgidan iborat bo'lsin!")
            return render_template("register.html")

        if password != confirm_password:
            flash("Parollar bir xil emas!")
            return render_template("register.html")

        password_hash = generate_password_hash(password)

        try:
            with get_db() as connection:
                with connection.cursor() as cursor:

                    cursor.execute("""
                        SELECT id
                        FROM students
                        WHERE email = %s
                    """, (email,))

                    existing = cursor.fetchone()

                    if existing:
                        flash("Bu email allaqachon ro'yxatdan o'tgan!")
                        return render_template("register.html")

                    cursor.execute("""
                        INSERT INTO students
                        (full_name, group_name, email, password_hash)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """, (
                        full_name,
                        group_name,
                        email,
                        password_hash
                    ))

                    student_id = cursor.fetchone()["id"]

            session.clear()
            session["student_id"] = student_id
            session["student_name"] = full_name

            flash("Ro'yxatdan o'tish muvaffaqiyatli!")

            return redirect(url_for("profile"))

        except psycopg.Error:
            flash("Ma'lumotlarni saqlashda xatolik yuz berdi!")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get(
            "password", ""
        )

        with get_db() as connection:
            with connection.cursor() as cursor:

                cursor.execute("""
                    SELECT id, full_name, password_hash
                    FROM students
                    WHERE email = %s
                    AND password_hash IS NOT NULL
                """, (email,))

                student = cursor.fetchone()

        if student and check_password_hash(
            student["password_hash"], password
        ):

            session.clear()

            session["student_id"] = student["id"]
            session["student_name"] = student["full_name"]

            return redirect(url_for("profile"))

        flash("Email yoki parol noto'g'ri!")

    return render_template("login.html")

@app.route("/logout", methods=["POST"])
def logout():

    session.clear()

    flash("Hisobingizdan muvaffaqiyatli chiqdingiz!")

    return redirect(url_for("login"))


@app.route("/profile")
@login_required
def profile():

    student_id = session["student_id"]

    with get_db() as connection:
        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT *
                FROM students
                WHERE id = %s
            """, (student_id,))

            student = cursor.fetchone()

            if student is None:
                session.clear()
                return redirect(url_for("login"))

            cursor.execute("""
                SELECT *
                FROM quiz_attempts
                WHERE student_id = %s
                ORDER BY completed_at DESC
                LIMIT 10
            """, (student_id,))

            attempts = cursor.fetchall()

    return render_template(
        "profile.html",
        student=student,
        attempts=attempts
    )



@app.route("/quiz", methods=["GET", "POST"])
@login_required
def quiz():

    if request.method == "POST":

        correct_count = 0

        # Javoblarni serverda tekshirish
        for question in QUIZ_QUESTIONS:

            selected_answer = request.form.get(
                question["id"], ""
            )

            if selected_answer == QUIZ_ANSWERS[question["id"]]:
                correct_count += 1

        total_questions = len(QUIZ_QUESTIONS)

        # Har bir to'g'ri javob 10 ball
        score = correct_count * 10

        student_id = session["student_id"]

        with get_db() as connection:

            with connection.cursor() as cursor:

                # Test natijasini tarixga saqlash
                cursor.execute("""
                    INSERT INTO quiz_attempts
                    (student_id, correct_answers, total_questions, score)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (
                    student_id,
                    correct_count,
                    total_questions,
                    score
                ))

                attempt_id = cursor.fetchone()["id"]

                # Talabaning joriy balini yangilash
                cursor.execute("""
                    UPDATE students
                    SET score = %s
                    WHERE id = %s
                """, (score, student_id))

        return redirect(
            url_for("quiz_result", attempt_id=attempt_id)
        )

    return render_template(
        "quiz.html",
        questions=QUIZ_QUESTIONS
    )


@app.route("/quiz/result/<int:attempt_id>")
@login_required
def quiz_result(attempt_id):

    student_id = session["student_id"]

    with get_db() as connection:

        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT *
                FROM quiz_attempts
                WHERE id = %s AND student_id = %s
            """, (attempt_id, student_id))

            attempt = cursor.fetchone()

    if attempt is None:
        abort(404)

    return render_template(
        "quiz_result.html",
        attempt=attempt
    )


if __name__ == "__main__":
    app.run()


