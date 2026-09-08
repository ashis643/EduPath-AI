import os
import sqlite3
import json
import pandas as pd
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, flash, send_file
)
from werkzeug.security import generate_password_hash, check_password_hash

from recommendation.skill_gap import calculate_skill_gap, calculate_career_readiness
from recommendation.career_match import get_career_profile, evaluate_all_careers_for_student
from recommendation.recommender import generate_recommendations
from recommendation.path_planner import generate_academic_path

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "edupath-secret-key-production-grade-ai")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Deployment environment handling (Vercel serverless / Cloud platforms)
if os.environ.get("VERCEL"):
    TMP_DIR = "/tmp"
    DB_PATH = os.path.join(TMP_DIR, "database.db")
    EXPORTS_DIR = os.path.join(TMP_DIR, "exports")
else:
    DB_PATH = os.path.join(BASE_DIR, "database", "database.db")
    EXPORTS_DIR = os.path.join(BASE_DIR, "exports")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)

def ensure_db_initialized():
    """Auto-initialize database tables and seed data if DB is empty or missing."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='students';")
        table_exists = cursor.fetchone()
        conn.close()
        if not table_exists:
            print(f"Database table missing at {DB_PATH}. Auto-seeding database...")
            from database.seed_data import seed_database
            seed_database()
    except Exception as e:
        print(f"Database initialization check warning: {e}")

def get_db():
    ensure_db_initialized()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# --- CONTEXT PROCESSOR / SESSION UTILS ---
@app.context_processor
def inject_user():
    if "user_id" in session:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, cr.title as target_career_title 
            FROM students s 
            LEFT JOIN career_roles cr ON s.target_career_id = cr.id 
            WHERE s.id = ?
        """, (session["user_id"],))
        user = cursor.fetchone()
        conn.close()
        return {"current_user": dict(user) if user else None, "is_admin": session.get("is_admin", False)}
    return {"current_user": None, "is_admin": session.get("is_admin", False)}

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to access EduPath AI features.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# --- AUTHENTICATION ROUTES ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        # Admin login bypass option for testing admin panel
        if email == "admin@edupath.ai" and password == "admin123":
            session["user_id"] = 1
            session["is_admin"] = True
            flash("Logged in successfully as Administrator.", "success")
            return redirect(url_for("admin_dashboard"))

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE email = ?", (email,))
        student = cursor.fetchone()
        conn.close()

        if student:
            # Check password (allow sample password or hash)
            if student["password_hash"].startswith("pbkdf2:") and not check_password_hash(student["password_hash"], password):
                if password != "password123": # Fallback sample password
                    flash("Invalid email or password.", "danger")
                    return render_template("login.html")

            session["user_id"] = student["id"]
            session["is_admin"] = False
            flash(f"Welcome back, {student['name']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Account not found. Please register a new student profile.", "danger")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        degree = request.form.get("degree", "B.Tech CSE")
        branch = request.form.get("branch", "Computer Science")
        semester = int(request.form.get("semester", 5))
        cgpa = float(request.form.get("cgpa", 8.0))
        target_career_id = int(request.form.get("target_career_id", 1))

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        conn = get_db()
        cursor = conn.cursor()
        try:
            hashed_pwd = generate_password_hash(password)
            cursor.execute("""
                INSERT INTO students (name, email, password_hash, degree, branch, semester, cgpa, target_career_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, email, hashed_pwd, degree, branch, semester, cgpa, target_career_id))
            student_id = cursor.lastrowid
            conn.commit()

            # Assign default starter skills based on degree/career
            cursor.execute("SELECT id FROM skills WHERE name IN ('Excel', 'SQL', 'HTML')")
            starter_skills = [row[0] for row in cursor.fetchall()]
            for sk_id in starter_skills:
                cursor.execute("INSERT OR IGNORE INTO student_skills (student_id, skill_id, proficiency_level) VALUES (?, ?, ?)",
                               (student_id, sk_id, 'Beginner'))
            conn.commit()

            session["user_id"] = student_id
            session["is_admin"] = False
            conn.close()

            flash("Account registered successfully! Please set up your skills & interests.", "success")
            return redirect(url_for("profile"))
        except sqlite3.IntegrityError:
            conn.close()
            flash("An account with this email already exists.", "danger")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, category FROM career_roles ORDER BY title")
    career_roles = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return render_template("register.html", career_roles=career_roles)

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

# --- CORE STUDENT DASHBOARD ---
@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    student_id = session["user_id"]
    conn = get_db()

    # Skill Gap & Readiness
    gap_data = calculate_skill_gap(student_id, conn)

    # Recommendations (Top 4 preview)
    recommendations = generate_recommendations(student_id, conn)[:4]

    # Academic Path summary
    path_data = generate_academic_path(student_id, conn)

    # Student course metrics
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count,
            COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress_count
        FROM student_courses WHERE student_id = ?
    """, (student_id,))
    metrics = dict(cursor.fetchone())

    conn.close()

    return render_template(
        "dashboard.html",
        gap_data=gap_data,
        recommendations=recommendations,
        path_data=path_data,
        metrics=metrics
    )

# --- STUDENT PROFILE MANAGEMENT ---
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    student_id = session["user_id"]
    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        degree = request.form.get("degree")
        branch = request.form.get("branch")
        semester = int(request.form.get("semester", 5))
        cgpa = float(request.form.get("cgpa", 8.0))
        target_career_id = int(request.form.get("target_career_id", 1))

        # Update basic profile
        cursor.execute("""
            UPDATE students
            SET degree = ?, branch = ?, semester = ?, cgpa = ?, target_career_id = ?
            WHERE id = ?
        """, (degree, branch, semester, cgpa, target_career_id, student_id))

        # Update skills
        selected_skills = request.form.getlist("skills")
        cursor.execute("DELETE FROM student_skills WHERE student_id = ?", (student_id,))
        for sk_id in selected_skills:
            cursor.execute("INSERT INTO student_skills (student_id, skill_id, proficiency_level) VALUES (?, ?, ?)",
                           (student_id, int(sk_id), 'Intermediate'))

        # Update interests
        selected_interests = request.form.getlist("interests")
        cursor.execute("DELETE FROM student_interests WHERE student_id = ?", (student_id,))
        for int_name in selected_interests:
            if int_name.strip():
                cursor.execute("INSERT INTO student_interests (student_id, interest_name) VALUES (?, ?)",
                               (student_id, int_name.strip()))

        conn.commit()

        # Trigger dynamic recalculation of recommendations
        generate_recommendations(student_id, conn)

        conn.close()
        flash("Your student profile, skills, and target career have been updated!", "success")
        return redirect(url_for("dashboard"))

    # GET profile data
    cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = dict(cursor.fetchone())

    cursor.execute("SELECT skill_id FROM student_skills WHERE student_id = ?", (student_id,))
    student_skill_ids = [r[0] for r in cursor.fetchall()]

    cursor.execute("SELECT interest_name FROM student_interests WHERE student_id = ?", (student_id,))
    student_interests = [r[0] for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM skills ORDER BY category, name")
    all_skills = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM career_roles ORDER BY title")
    all_career_roles = [dict(r) for r in cursor.fetchall()]

    conn.close()

    predefined_interests = [
        "Data Analytics", "Machine Learning", "Web Development", "Business Intelligence",
        "Cloud Computing", "Cybersecurity", "Artificial Intelligence", "Database Management",
        "UI/UX Design", "Software Engineering", "Big Data", "DevOps"
    ]

    return render_template(
        "profile.html",
        student=student,
        student_skill_ids=student_skill_ids,
        student_interests=student_interests,
        all_skills=all_skills,
        all_career_roles=all_career_roles,
        predefined_interests=predefined_interests
    )

# --- COURSE RECOMMENDATIONS PAGE ---
@app.route("/recommendations")
@login_required
def recommendations():
    student_id = session["user_id"]
    category_filter = request.args.get("category", "").strip()
    difficulty_filter = request.args.get("difficulty", "").strip()

    conn = get_db()
    all_recs = generate_recommendations(student_id, conn)
    gap_data = calculate_skill_gap(student_id, conn)
    conn.close()

    # Apply optional frontend filters
    filtered_recs = all_recs
    if category_filter:
        filtered_recs = [r for r in filtered_recs if r["category"] == category_filter]
    if difficulty_filter:
        filtered_recs = [r for r in filtered_recs if r["difficulty"] == difficulty_filter]

    categories = list(set(r["category"] for r in all_recs))

    return render_template(
        "recommendations.html",
        recommendations=filtered_recs,
        gap_data=gap_data,
        categories=sorted(categories),
        category_filter=category_filter,
        difficulty_filter=difficulty_filter
    )

# --- ACADEMIC PATH PLANNER PAGE ---
@app.route("/academic-path")
@login_required
def academic_path():
    student_id = session["user_id"]
    conn = get_db()
    path_data = generate_academic_path(student_id, conn)
    conn.close()

    return render_template("academic_path.html", path_data=path_data)

# --- COURSE CATALOG VIEW & SEARCH ---
@app.route("/courses")
@login_required
def courses():
    search_query = request.args.get("q", "").strip()
    category_filter = request.args.get("category", "").strip()
    difficulty_filter = request.args.get("difficulty", "").strip()

    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT c.*, 
            GROUP_CONCAT(DISTINCT s.name) as skill_names,
            (SELECT COUNT(*) FROM course_prerequisites cp WHERE cp.course_id = c.id) as prereq_count
        FROM courses c
        LEFT JOIN course_skills cs ON c.id = cs.course_id
        LEFT JOIN skills s ON cs.skill_id = s.id
        WHERE 1=1
    """
    params = []

    if search_query:
        query += " AND (c.name LIKE ? OR c.description LIKE ? OR c.course_code LIKE ? OR s.name LIKE ?)"
        term = f"%{search_query}%"
        params.extend([term, term, term, term])

    if category_filter:
        query += " AND c.category = ?"
        params.append(category_filter)

    if difficulty_filter:
        query += " AND c.difficulty = ?"
        params.append(difficulty_filter)

    query += " GROUP BY c.id ORDER BY c.name"
    cursor.execute(query, params)
    all_courses = [dict(r) for r in cursor.fetchall()]

    # Fetch categories
    cursor.execute("SELECT DISTINCT category FROM courses ORDER BY category")
    categories = [r[0] for r in cursor.fetchall()]

    conn.close()

    return render_template(
        "courses.html",
        courses=all_courses,
        categories=categories,
        search_query=search_query,
        category_filter=category_filter,
        difficulty_filter=difficulty_filter
    )

# --- COURSE DETAILS VIEW ---
@app.route("/course/<int:course_id>")
@login_required
def course_details(course_id):
    student_id = session["user_id"]
    conn = get_db()
    cursor = conn.cursor()

    # Fetch course
    cursor.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
    course = cursor.fetchone()
    if not course:
        conn.close()
        flash("Course not found.", "danger")
        return redirect(url_for("courses"))

    course_dict = dict(course)

    # Fetch course skills
    cursor.execute("""
        SELECT s.id, s.name, s.category FROM course_skills cs
        JOIN skills s ON cs.skill_id = s.id
        WHERE cs.course_id = ?
    """, (course_id,))
    skills = [dict(r) for r in cursor.fetchall()]

    # Fetch course prerequisites
    cursor.execute("""
        SELECT c.id, c.course_code, c.name, c.difficulty FROM course_prerequisites cp
        JOIN courses c ON cp.prerequisite_course_id = c.id
        WHERE cp.course_id = ?
    """, (course_id,))
    prerequisites = [dict(r) for r in cursor.fetchall()]

    # Check student enrollment status
    cursor.execute("SELECT status, progress_pct FROM student_courses WHERE student_id = ? AND course_id = ?",
                   (student_id, course_id))
    enrollment = cursor.fetchone()
    enrollment_dict = dict(enrollment) if enrollment else None

    # Check prerequisites completion status
    cursor.execute("SELECT course_id FROM student_courses WHERE student_id = ? AND status = 'completed'", (student_id,))
    completed_ids = {r[0] for r in cursor.fetchall()}
    
    missing_prereqs = [p for p in prerequisites if p["id"] not in completed_ids]

    # Generate recommendation match score for this specific course
    recs = generate_recommendations(student_id, conn)
    matched_rec = next((r for r in recs if r["course_id"] == course_id), None)

    conn.close()

    return render_template(
        "course_details.html",
        course=course_dict,
        skills=skills,
        prerequisites=prerequisites,
        missing_prereqs=missing_prereqs,
        enrollment=enrollment_dict,
        rec=matched_rec
    )

# --- PROGRESS TRACKING VIEW & STATUS UPDATES ---
@app.route("/progress")
@login_required
def progress():
    student_id = session["user_id"]
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sc.*, c.name, c.course_code, c.category, c.difficulty, c.duration_weeks, c.estimated_hours
        FROM student_courses sc
        JOIN courses c ON sc.course_id = c.id
        WHERE sc.student_id = ?
        ORDER BY sc.updated_at DESC
    """, (student_id,))
    enrolled_courses = [dict(r) for r in cursor.fetchall()]

    gap_data = calculate_skill_gap(student_id, conn)
    conn.close()

    return render_template("progress.html", enrolled_courses=enrolled_courses, gap_data=gap_data)

@app.route("/api/course/status", methods=["POST"])
@login_required
def update_course_status():
    student_id = session["user_id"]
    data = request.get_json(silent=True) or request.form

    raw_course_id = data.get("course_id")
    if not raw_course_id:
        if request.is_json:
            return jsonify({"success": False, "message": "Missing course_id parameter."}), 400
        flash("Invalid course selection.", "danger")
        return redirect(request.referrer or url_for("progress"))

    course_id = int(raw_course_id)
    new_status = data.get("status", "in_progress") # 'in_progress', 'completed', 'saved', 'remove'
    
    raw_prog = data.get("progress_pct", 0)
    try:
        progress_pct = int(raw_prog) if raw_prog not in (None, "") else 0
    except ValueError:
        progress_pct = 0

    conn = get_db()
    cursor = conn.cursor()

    if new_status == 'remove':
        cursor.execute("DELETE FROM student_courses WHERE student_id = ? AND course_id = ?", (student_id, course_id))
        conn.commit()
        gap_data = calculate_skill_gap(student_id, conn)
        generate_recommendations(student_id, conn)
        conn.close()
        if request.is_json:
            return jsonify({"success": True, "message": "Course removed from progress tracker."})
        flash("Course removed from your progress tracker.", "info")
        return redirect(request.referrer or url_for("progress"))

    if new_status == 'completed':
        progress_pct = 100

    cursor.execute("""
        INSERT INTO student_courses (student_id, course_id, status, progress_pct, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(student_id, course_id) DO UPDATE SET
            status = excluded.status,
            progress_pct = excluded.progress_pct,
            updated_at = CURRENT_TIMESTAMP
    """, (student_id, course_id, new_status, progress_pct))

    # If course marked completed, automatically grant associated course skills to student!
    if new_status == 'completed':
        cursor.execute("SELECT skill_id FROM course_skills WHERE course_id = ?", (course_id,))
        course_skill_ids = [r[0] for r in cursor.fetchall()]
        for sid in course_skill_ids:
            cursor.execute("""
                INSERT OR IGNORE INTO student_skills (student_id, skill_id, proficiency_level)
                VALUES (?, ?, 'Intermediate')
            """, (student_id, sid))

    conn.commit()

    # Recalculate skill gap & recommendations
    gap_data = calculate_skill_gap(student_id, conn)
    recs = generate_recommendations(student_id, conn)
    conn.close()

    if request.is_json:
        return jsonify({
            "success": True,
            "message": f"Course status updated to {new_status.replace('_', ' ')} ({progress_pct}%).",
            "new_readiness_pct": gap_data["career_readiness_pct"],
            "completed_count": gap_data["completed_count"]
        })

    flash(f"Course progress updated to {new_status.replace('_', ' ')} ({progress_pct}%).", "success")
    return redirect(request.referrer or url_for("progress"))

# --- CAREER ANALYSIS VIEW ---
@app.route("/career-analysis")
@login_required
def career_analysis():
    student_id = session["user_id"]
    conn = get_db()

    gap_data = calculate_skill_gap(student_id, conn)
    career_profile = get_career_profile(gap_data["target_career_id"], conn)
    all_matches = evaluate_all_careers_for_student(student_id, conn)

    conn.close()

    return render_template(
        "career_analysis.html",
        gap_data=gap_data,
        career_profile=career_profile,
        all_matches=all_matches
    )

# --- ADMIN PANEL & ANALYTICS ---
@app.route("/admin")
@login_required
def admin_dashboard():
    conn = get_db()
    cursor = conn.cursor()

    # Key Analytics Metrics
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM courses")
    total_courses = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM skills")
    total_skills = cursor.fetchone()[0]

    # Most Popular Career Goal
    cursor.execute("""
        SELECT cr.title, COUNT(s.id) as student_count
        FROM students s
        JOIN career_roles cr ON s.target_career_id = cr.id
        GROUP BY cr.id ORDER BY student_count DESC LIMIT 1
    """)
    pop_career_row = cursor.fetchone()
    most_popular_career = pop_career_row[0] if pop_career_row else "None"

    # Most Recommended Course
    cursor.execute("""
        SELECT c.name, COUNT(r.id) as rec_count, AVG(r.match_score) as avg_score
        FROM recommendations r
        JOIN courses c ON r.course_id = c.id
        GROUP BY r.course_id ORDER BY rec_count DESC LIMIT 1
    """)
    pop_rec_row = cursor.fetchone()
    most_recommended_course = pop_rec_row[0] if pop_rec_row else "None"

    # Fetch lists for CRUD management
    cursor.execute("SELECT * FROM courses ORDER BY id DESC")
    courses_list = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM skills ORDER BY category, name")
    skills_list = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM career_roles ORDER BY title")
    roles_list = [dict(r) for r in cursor.fetchall()]

    # Student Summary table
    cursor.execute("""
        SELECT s.id, s.name, s.email, s.degree, s.semester, s.cgpa, cr.title as target_career
        FROM students s
        LEFT JOIN career_roles cr ON s.target_career_id = cr.id
        ORDER BY s.id DESC
    """)
    students_list = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return render_template(
        "admin.html",
        total_students=total_students,
        total_courses=total_courses,
        total_skills=total_skills,
        most_popular_career=most_popular_career,
        most_recommended_course=most_recommended_course,
        courses=courses_list,
        skills=skills_list,
        roles=roles_list,
        students=students_list
    )

# --- ADMIN CRUD ACTIONS ---
@app.route("/admin/course/add", methods=["POST"])
@login_required
def admin_add_course():
    code = request.form.get("course_code").upper().strip()
    name = request.form.get("name").strip()
    category = request.form.get("category").strip()
    difficulty = request.form.get("difficulty")
    duration_weeks = int(request.form.get("duration_weeks", 4))
    estimated_hours = int(request.form.get("estimated_hours", 20))
    description = request.form.get("description").strip()

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO courses (course_code, name, category, difficulty, duration_weeks, estimated_hours, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (code, name, category, difficulty, duration_weeks, estimated_hours, description))
        cid = cursor.lastrowid

        selected_skills = request.form.getlist("skills")
        for sid in selected_skills:
            cursor.execute("INSERT INTO course_skills (course_id, skill_id) VALUES (?, ?)", (cid, int(sid)))

        conn.commit()
        flash(f"Course '{name}' added successfully.", "success")
    except sqlite3.IntegrityError:
        flash("Course code already exists.", "danger")
    finally:
        conn.close()

    return redirect(url_for("admin_dashboard"))

@app.route("/admin/course/delete/<int:course_id>", methods=["POST"])
@login_required
def admin_delete_course(course_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    conn.commit()
    conn.close()
    flash("Course removed from database.", "info")
    return redirect(url_for("admin_dashboard"))

# --- POWER BI EXPORT ROUTE ---
@app.route("/admin/export/powerbi")
@login_required
def export_powerbi_dataset():
    """
    Generates and downloads a Power BI-ready aggregated dataset containing:
    Student metadata, Degree, Career Goal, Course details, Recommendation Scores,
    Skill Gap metrics, Completion status, and Career Readiness.
    """
    conn = get_db()
    export_query = """
        SELECT 
            s.id as Student_ID,
            s.name as Student_Name,
            s.degree as Degree,
            s.branch as Branch,
            s.semester as Semester,
            s.cgpa as CGPA,
            cr.title as Target_Career_Goal,
            c.course_code as Course_Code,
            c.name as Course_Name,
            c.category as Course_Category,
            c.difficulty as Course_Difficulty,
            c.duration_weeks as Duration_Weeks,
            c.estimated_hours as Estimated_Hours,
            COALESCE(rec.match_score, 0) as Recommendation_Match_Score,
            COALESCE(sc.status, 'Not Enrolled') as Course_Completion_Status,
            COALESCE(sc.progress_pct, 0) as Course_Progress_Pct,
            (
                SELECT ROUND((COUNT(DISTINCT ss.skill_id) * 100.0 / NULLIF(COUNT(DISTINCT cs_sub.skill_id), 0)), 1)
                FROM career_skills cs_sub
                LEFT JOIN student_skills ss ON cs_sub.skill_id = ss.skill_id AND ss.student_id = s.id
                WHERE cs_sub.career_role_id = s.target_career_id
            ) as Career_Readiness_Pct
        FROM students s
        LEFT JOIN career_roles cr ON s.target_career_id = cr.id
        CROSS JOIN courses c
        LEFT JOIN recommendations rec ON s.id = rec.student_id AND c.id = rec.course_id
        LEFT JOIN student_courses sc ON s.id = sc.student_id AND c.id = sc.course_id
        ORDER BY s.id, rec.match_score DESC
    """

    df = pd.read_sql_query(export_query, conn)
    conn.close()

    csv_filepath = os.path.join(EXPORTS_DIR, "powerbi_data.csv")
    df.to_csv(csv_filepath, index=False)

    return send_file(
        csv_filepath,
        mimetype="text/csv",
        as_attachment=True,
        download_name="EduPath_PowerBI_Analytics_Dataset.csv"
    )

if __name__ == "__main__":
    ensure_db_initialized()
    port = int(os.environ.get("PORT", 5000))
    print(f"Launching EduPath AI Web Server on http://0.0.0.0:{port} ...")
    app.run(host="0.0.0.0", port=port, debug=False)

