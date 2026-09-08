import sqlite3

def calculate_skill_gap(student_id, conn):
    """
    Computes completed skills, missing skills for target career role,
    skill gap percentage, and detailed skill progress.
    """
    cursor = conn.cursor()

    # Get student's target career role ID
    cursor.execute("SELECT target_career_id FROM students WHERE id = ?", (student_id,))
    row = cursor.fetchone()
    if not row or not row[0]:
        target_career_id = 1 # Fallback to Data Analyst
    else:
        target_career_id = row[0]

    # Fetch career title and category
    cursor.execute("SELECT title, category FROM career_roles WHERE id = ?", (target_career_id,))
    career_row = cursor.fetchone()
    career_title = career_row[0] if career_row else "Target Career"

    # Fetch student's current skills
    cursor.execute("""
        SELECT s.id, s.name, s.category, ss.proficiency_level
        FROM student_skills ss
        JOIN skills s ON ss.skill_id = s.id
        WHERE ss.student_id = ?
    """, (student_id,))
    student_skills_list = cursor.fetchall()
    student_skill_ids = {s[0] for s in student_skills_list}

    # Fetch required skills for target career role with weights
    cursor.execute("""
        SELECT s.id, s.name, cs.weight, s.category
        FROM career_skills cs
        JOIN skills s ON cs.skill_id = s.id
        WHERE cs.career_role_id = ?
        ORDER BY cs.weight DESC
    """, (target_career_id,))
    required_skills = cursor.fetchall()

    completed_required = []
    missing_required = []
    total_required_weight = 0.0
    acquired_required_weight = 0.0

    skill_progress_list = []

    for sid, sname, weight, scategory in required_skills:
        total_required_weight += weight
        is_completed = sid in student_skill_ids
        if is_completed:
            acquired_required_weight += weight
            completed_required.append({"id": sid, "name": sname, "weight": weight, "category": scategory})
            progress_pct = 100
        else:
            missing_required.append({"id": sid, "name": sname, "weight": weight, "category": scategory})
            # Check if student has in-progress course covering this skill
            cursor.execute("""
                SELECT sc.progress_pct 
                FROM student_courses sc
                JOIN course_skills csk ON sc.course_id = csk.course_id
                WHERE sc.student_id = ? AND csk.skill_id = ? AND sc.status = 'in_progress'
                ORDER BY sc.progress_pct DESC LIMIT 1
            """, (student_id, sid))
            prog_row = cursor.fetchone()
            progress_pct = prog_row[0] if prog_row else 0

        skill_progress_list.append({
            "id": sid,
            "name": sname,
            "weight": weight,
            "completed": is_completed,
            "progress_pct": progress_pct
        })

    total_count = len(required_skills)
    completed_count = len(completed_required)
    missing_count = len(missing_required)

    skill_gap_pct = round((missing_count / total_count * 100), 1) if total_count > 0 else 0.0

    # Calculate weighted career readiness percentage
    if total_required_weight > 0:
        career_readiness_pct = round((acquired_required_weight / total_required_weight) * 100, 1)
    else:
        career_readiness_pct = 0.0

    return {
        "target_career_id": target_career_id,
        "target_career_title": career_title,
        "completed_skills": completed_required,
        "missing_skills": missing_required,
        "completed_count": completed_count,
        "missing_count": missing_count,
        "total_required_count": total_count,
        "skill_gap_pct": skill_gap_pct,
        "career_readiness_pct": career_readiness_pct,
        "skill_progress": skill_progress_list
    }

def calculate_career_readiness(student_id, conn):
    gap_data = calculate_skill_gap(student_id, conn)
    return gap_data["career_readiness_pct"]
