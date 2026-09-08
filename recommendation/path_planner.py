import sqlite3
from .skill_gap import calculate_skill_gap

def generate_academic_path(student_id, conn):
    """
    Generates a personalized step-by-step academic learning roadmap
    for the student's target career role.
    Uses prerequisite topological sort & dynamic status mapping.
    """
    cursor = conn.cursor()

    # Get student target career & completed courses
    cursor.execute("SELECT target_career_id FROM students WHERE id = ?", (student_id,))
    row = cursor.fetchone()
    target_career_id = row[0] if row and row[0] else 1

    cursor.execute("SELECT title FROM career_roles WHERE id = ?", (target_career_id,))
    career_row = cursor.fetchone()
    career_title = career_row[0] if career_row else "Target Career"

    # Get student course statuses
    cursor.execute("SELECT course_id, status, progress_pct FROM student_courses WHERE student_id = ?", (student_id,))
    student_courses = {cid: {"status": st, "progress": prg} for cid, st, prg in cursor.fetchall()}
    completed_ids = {cid for cid, info in student_courses.items() if info["status"] == 'completed'}

    # Get required skills for target career
    cursor.execute("SELECT skill_id FROM career_skills WHERE career_role_id = ?", (target_career_id,))
    career_skill_ids = {r[0] for r in cursor.fetchall()}

    # Select courses that teach target career skills OR are prerequisites for those courses
    cursor.execute("SELECT DISTINCT course_id FROM course_skills WHERE skill_id IN ({})".format(
        ",".join("?" for _ in career_skill_ids) if career_skill_ids else "0"
    ), list(career_skill_ids) if career_skill_ids else [])
    
    target_course_ids = {r[0] for r in cursor.fetchall()}

    # Recursively expand to include prerequisites of target courses
    all_path_course_ids = set(target_course_ids)
    added = True
    while added:
        added = False
        if not all_path_course_ids:
            break
        placeholders = ",".join("?" for _ in all_path_course_ids)
        cursor.execute(f"SELECT prerequisite_course_id FROM course_prerequisites WHERE course_id IN ({placeholders})", list(all_path_course_ids))
        prereq_ids = {r[0] for r in cursor.fetchall()}
        new_ids = prereq_ids - all_path_course_ids
        if new_ids:
            all_path_course_ids.update(new_ids)
            added = True

    if not all_path_course_ids:
        # Fallback to beginner/intermediate courses if none found
        cursor.execute("SELECT id FROM courses ORDER BY id LIMIT 8")
        all_path_course_ids = {r[0] for r in cursor.fetchall()}

    # Fetch full course details for all roadmap courses
    placeholders = ",".join("?" for _ in all_path_course_ids)
    cursor.execute(f"""
        SELECT id, course_code, name, category, difficulty, duration_weeks, estimated_hours, description
        FROM courses WHERE id IN ({placeholders})
    """, list(all_path_course_ids))
    course_records = cursor.fetchall()
    course_dict = {r[0]: {
        "id": r[0], "code": r[1], "name": r[2], "category": r[3],
        "difficulty": r[4], "duration": r[5], "hours": r[6], "description": r[7]
    } for r in course_records}

    # Fetch prerequisites for path courses
    cursor.execute(f"""
        SELECT course_id, prerequisite_course_id
        FROM course_prerequisites
        WHERE course_id IN ({placeholders}) AND prerequisite_course_id IN ({placeholders})
    """, list(all_path_course_ids) + list(all_path_course_ids))
    prereq_graph = {cid: set() for cid in all_path_course_ids}
    for cid, pid in cursor.fetchall():
        prereq_graph[cid].add(pid)

    # Fetch skills for path courses
    cursor.execute(f"""
        SELECT cs.course_id, s.name FROM course_skills cs
        JOIN skills s ON cs.skill_id = s.id
        WHERE cs.course_id IN ({placeholders})
    """, list(all_path_course_ids))
    course_skills_map = {}
    for cid, sname in cursor.fetchall():
        course_skills_map.setdefault(cid, []).append(sname)

    # Topological Sort based on prerequisite dependencies & difficulty order
    diff_order = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}
    
    # Calculate indegrees
    in_degree = {cid: len(prereq_graph[cid]) for cid in all_path_course_ids}
    
    # Priority Queue / Sort order
    sorted_path = []
    visited = set()

    # Process nodes iteratively
    while len(visited) < len(all_path_course_ids):
        # Find candidates with 0 unvisited prerequisites
        candidates = [
            cid for cid in all_path_course_ids
            if cid not in visited and all(p in visited for p in prereq_graph[cid])
        ]

        if not candidates:
            # Handle cycles or missing ties gracefully by picking lowest difficulty unvisited candidate
            candidates = [cid for cid in all_path_course_ids if cid not in visited]

        # Sort candidates: completed first, then by difficulty order, then duration
        candidates.sort(key=lambda cid: (
            0 if cid in completed_ids else 1,
            diff_order.get(course_dict[cid]["difficulty"], 2),
            course_dict[cid]["duration"]
        ))

        chosen = candidates[0]
        visited.add(chosen)
        sorted_path.append(chosen)

    # Build detailed roadmap steps
    roadmap_nodes = []
    has_found_next = False

    for idx, cid in enumerate(sorted_path, 1):
        c_info = course_dict[cid]
        c_status_info = student_courses.get(cid, {"status": "unstarted", "progress": 0})
        st = c_status_info["status"]
        prog = c_status_info["progress"]

        prereqs = list(prereq_graph[cid])
        prereqs_completed = all(p in completed_ids for p in prereqs)

        if st == "completed":
            step_status = "completed"
            status_label = "Completed"
            badge_class = "badge-completed"
        elif st == "in_progress":
            step_status = "in_progress"
            status_label = f"In Progress ({prog}%)"
            badge_class = "badge-in-progress"
        elif not prereqs_completed:
            step_status = "prereq_locked"
            status_label = "Prerequisite Required"
            badge_class = "badge-locked"
        elif not has_found_next:
            step_status = "next"
            status_label = "Recommended Next Step"
            badge_class = "badge-next"
            has_found_next = True
        else:
            step_status = "upcoming"
            status_label = "Upcoming"
            badge_class = "badge-upcoming"

        # Lookup prerequisite course names
        prereq_names = [course_dict[p]["name"] for p in prereqs if p in course_dict]

        roadmap_nodes.append({
            "step_number": idx,
            "course_id": cid,
            "code": c_info["code"],
            "name": c_info["name"],
            "category": c_info["category"],
            "difficulty": c_info["difficulty"],
            "duration": c_info["duration"],
            "hours": c_info["hours"],
            "description": c_info["description"],
            "skills": course_skills_map.get(cid, []),
            "prerequisites": prereq_names,
            "step_status": step_status,
            "status_label": status_label,
            "badge_class": badge_class,
            "progress_pct": prog
        })

    # Add Capstone Milestone Node at the end
    gap_info = calculate_skill_gap(student_id, conn)

    return {
        "target_career_title": career_title,
        "career_readiness_pct": gap_info["career_readiness_pct"],
        "total_steps": len(roadmap_nodes) + 1,
        "nodes": roadmap_nodes,
        "capstone": {
            "title": f"{career_title} Capstone Project & Certification",
            "description": f"Apply all acquired skills in a full-scale portfolio project to transition into a professional {career_title}.",
            "target_role": career_title
        }
    }
