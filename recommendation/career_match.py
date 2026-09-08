import sqlite3

def get_career_profile(career_role_id, conn):
    """
    Retrieves full breakdown of a career role including description,
    category, and required skills with importance weights.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description, category FROM career_roles WHERE id = ?", (career_role_id,))
    role = cursor.fetchone()
    if not role:
        return None

    role_dict = {
        "id": role[0],
        "title": role[1],
        "description": role[2],
        "category": role[3]
    }

    cursor.execute("""
        SELECT s.id, s.name, cs.weight, s.category
        FROM career_skills cs
        JOIN skills s ON cs.skill_id = s.id
        WHERE cs.career_role_id = ?
        ORDER BY cs.weight DESC
    """, (career_role_id,))

    skills = []
    for sid, sname, weight, scats in cursor.fetchall():
        skills.append({"id": sid, "name": sname, "weight": weight, "category": scats})

    role_dict["required_skills"] = skills
    return role_dict

def evaluate_all_careers_for_student(student_id, conn):
    """
    Evaluates student match readiness across all available career roles
    to recommend alternate or aligned career paths.
    """
    cursor = conn.cursor()

    # Student skills
    cursor.execute("SELECT skill_id FROM student_skills WHERE student_id = ?", (student_id,))
    student_skill_ids = {row[0] for row in cursor.fetchall()}

    cursor.execute("SELECT id, title, category FROM career_roles")
    roles = cursor.fetchall()

    career_matches = []

    for rid, title, cat in roles:
        cursor.execute("SELECT skill_id, weight FROM career_skills WHERE career_role_id = ?", (rid,))
        cskills = cursor.fetchall()
        total_w = sum(w for _, w in cskills)
        acquired_w = sum(w for sid, w in cskills if sid in student_skill_ids)

        readiness = round((acquired_w / total_w * 100), 1) if total_w > 0 else 0.0

        career_matches.append({
            "id": rid,
            "title": title,
            "category": cat,
            "readiness_pct": readiness,
            "total_skills": len(cskills),
            "acquired_skills": len([sid for sid, _ in cskills if sid in student_skill_ids])
        })

    career_matches.sort(key=lambda x: x["readiness_pct"], reverse=True)
    return career_matches
