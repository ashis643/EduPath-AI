import sqlite3
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .skill_gap import calculate_skill_gap

def generate_recommendations(student_id, conn):
    """
    Generates dynamic, personalized course recommendations for a student using:
    1. Content-based Cosine Similarity (TF-IDF on Skills + Interests + Target Career)
    2. Multi-factor Weighted Scoring Formula:
       40% Skill Gap Match
     + 30% Career Relevance
     + 15% Interest Match
     + 10% Difficulty Fit
     + 5% Prerequisite Compatibility
    3. Explainability engine providing 5 explicit recommendation reasons.
    """
    cursor = conn.cursor()

    # 1. Fetch Student Profile Data
    cursor.execute("""
        SELECT s.name, s.degree, s.branch, s.semester, s.cgpa, s.target_career_id, cr.title
        FROM students s
        LEFT JOIN career_roles cr ON s.target_career_id = cr.id
        WHERE s.id = ?
    """, (student_id,))
    student_row = cursor.fetchone()
    if not student_row:
        return []

    degree, branch, semester, cgpa, target_career_id, career_title = (
        student_row[1], student_row[2], student_row[3], student_row[4], student_row[5], student_row[6]
    )
    if not target_career_id:
        target_career_id = 1
        career_title = "Data Analyst"

    # Fetch Student's current skills
    cursor.execute("""
        SELECT s.id, s.name FROM student_skills ss
        JOIN skills s ON ss.skill_id = s.id
        WHERE ss.student_id = ?
    """, (student_id,))
    student_skills = cursor.fetchall()
    student_skill_ids = {s[0] for s in student_skills}
    student_skill_names = {s[1] for s in student_skills}

    # Fetch Student's interests
    cursor.execute("SELECT interest_name FROM student_interests WHERE student_id = ?", (student_id,))
    student_interests = [row[0] for row in cursor.fetchall()]

    # Fetch Student's course enrollment status
    cursor.execute("SELECT course_id, status FROM student_courses WHERE student_id = ?", (student_id,))
    student_courses_status = {row[0]: row[1] for row in cursor.fetchall()}
    completed_course_ids = {cid for cid, st in student_courses_status.items() if st == 'completed'}

    # Fetch Skill Gap data
    gap_data = calculate_skill_gap(student_id, conn)
    missing_skill_ids = {s["id"] for s in gap_data["missing_skills"]}
    missing_skill_names = {s["name"] for s in gap_data["missing_skills"]}

    # Fetch required skills for target career role with weights
    cursor.execute("""
        SELECT skill_id, weight FROM career_skills WHERE career_role_id = ?
    """, (target_career_id,))
    career_required_weights = {row[0]: row[1] for row in cursor.fetchall()}

    # 2. Fetch All Courses
    cursor.execute("""
        SELECT id, course_code, name, category, description, difficulty, duration_weeks, estimated_hours
        FROM courses
    """)
    courses = cursor.fetchall()

    # Pre-fetch course skills and prerequisites for all courses
    cursor.execute("""
        SELECT cs.course_id, cs.skill_id, s.name FROM course_skills cs
        JOIN skills s ON cs.skill_id = s.id
    """)
    course_skills_pairs_map = {}
    for cid, sid, sname in cursor.fetchall():
        course_skills_pairs_map.setdefault(cid, []).append((sid, sname))

    cursor.execute("""
        SELECT cp.course_id, cp.prerequisite_course_id, c.name, c.course_code
        FROM course_prerequisites cp
        JOIN courses c ON cp.prerequisite_course_id = c.id
    """)
    course_prereqs_map = {}
    for cid, pid, pname, pcode in cursor.fetchall():
        course_prereqs_map.setdefault(cid, []).append({"id": pid, "name": pname, "code": pcode})

    # 3. TF-IDF Cosine Similarity setup
    # Construct student corpus string
    student_corpus = " ".join(list(student_skill_names) + student_interests + list(missing_skill_names) + [career_title or ""])
    
    course_corpuses = []
    course_list_clean = []

    for c in courses:
        cid = c[0]
        c_pairs = course_skills_pairs_map.get(cid, [])
        cskills = [sname for _, sname in c_pairs]
        ccategory = c[3]
        cdesc = c[4]
        ccorpus = f"{ccategory} {' '.join(cskills)} {cdesc}"
        course_corpuses.append(ccorpus)
        course_list_clean.append(c)

    # Compute Cosine Similarity matrix
    tfidf = TfidfVectorizer(stop_words='english')
    if course_corpuses:
        all_texts = [student_corpus] + course_corpuses
        tfidf_matrix = tfidf.fit_transform(all_texts)
        cosine_sims = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    else:
        cosine_sims = np.zeros(len(courses))

    recommendations = []

    for idx, c in enumerate(course_list_clean):
        cid, code, name, category, desc, difficulty, duration, hours = c

        # Skip already completed courses from active recommendations
        status = student_courses_status.get(cid, None)

        c_pairs = course_skills_pairs_map.get(cid, [])
        c_skills = {sid for sid, _ in c_pairs}
        c_skill_names = [sname for _, sname in c_pairs]
        c_prereqs = course_prereqs_map.get(cid, [])

        # Check Prerequisite Compatibility
        missing_prereqs = [p for p in c_prereqs if p["id"] not in completed_course_ids]
        prereq_satisfied = len(missing_prereqs) == 0

        # --- MULTI-FACTOR SCORE COMPONENTS ---

        # 1. Skill Gap Match (40%): How many missing career skills does this course cover?
        covered_missing = c_skills.intersection(missing_skill_ids)
        if len(missing_skill_ids) > 0:
            skill_gap_match_score = (len(covered_missing) / max(1, len(missing_skill_ids))) * 100.0
            # Boost if it covers high weight missing skills
            weight_sum = sum(career_required_weights.get(sid, 1.0) for sid in covered_missing)
            max_weight_sum = sum(career_required_weights.get(sid, 1.0) for sid in missing_skill_ids)
            if max_weight_sum > 0:
                skill_gap_match_score = (weight_sum / max_weight_sum) * 100.0
        else:
            skill_gap_match_score = 50.0

        # Cap skill gap match score
        skill_gap_match_score = min(100.0, skill_gap_match_score * 1.5 if covered_missing else 10.0)

        # 2. Career Relevance (30%): Relevance of course skills to target career role
        career_covered_skills = c_skills.intersection(set(career_required_weights.keys()))
        if len(career_required_weights) > 0:
            career_relevance_score = (len(career_covered_skills) / len(career_required_weights)) * 100.0
            # Weight boost
            c_weight = sum(career_required_weights.get(sid, 0.0) for sid in career_covered_skills)
            career_relevance_score = min(100.0, (c_weight / 5.0) * 100.0) if c_weight > 0 else 20.0
        else:
            career_relevance_score = 40.0

        # 3. Interest Match (15%): Cosine similarity + interest text overlap
        cos_score = float(cosine_sims[idx]) * 100.0
        interest_overlap = any(int_name.lower() in category.lower() or int_name.lower() in name.lower() for int_name in student_interests)
        interest_match_score = min(100.0, cos_score + (30.0 if interest_overlap else 0.0))

        # 4. Difficulty Fit (10%): Match student's semester level
        if semester <= 3:
            preferred_diff = "Beginner"
        elif semester <= 6:
            preferred_diff = "Intermediate"
        else:
            preferred_diff = "Advanced"

        if difficulty == preferred_diff:
            difficulty_fit_score = 100.0
        elif (preferred_diff == "Intermediate" and difficulty in ["Beginner", "Advanced"]):
            difficulty_fit_score = 75.0
        else:
            difficulty_fit_score = 50.0

        # 5. Prerequisite Compatibility (5%)
        prereq_score = 100.0 if prereq_satisfied else 30.0

        # --- WEIGHTED FINAL RECOMMENDATION SCORE ---
        raw_final_score = (
            (0.40 * skill_gap_match_score) +
            (0.30 * career_relevance_score) +
            (15 * (interest_match_score / 100.0)) + # 15% weight
            (10 * (difficulty_fit_score / 100.0)) + # 10% weight
            (5 * (prereq_score / 100.0))          # 5% weight
        )

        # Normalize score strictly between 0 and 100
        final_match_score = round(min(99.0, max(45.0, raw_final_score)), 1)

        # Adjust score penalties if completed
        if status == 'completed':
            final_match_score = round(final_match_score * 0.5, 1)

        # --- EXPLAINABILITY ENGINE ---
        reasons = []

        # Reason 1: Career Skill Gap
        if covered_missing:
            cov_names = [sname for sid, sname in c_pairs if sid in missing_skill_ids]
            reasons.append(f"Fills critical skill gap(s): {', '.join(cov_names)} required for {career_title}.")
        elif career_covered_skills:
            reasons.append(f"Reinforces target skills required for the {career_title} role.")
        else:
            reasons.append(f"Provides foundational technical knowledge in {category}.")

        # Reason 2: Interest & Domain Alignment
        if interest_overlap:
            reasons.append(f"Directly matches your indicated interest in Data & Tech domain.")
        else:
            reasons.append(f"Expands your specialization in {category}.")

        # Reason 3: Career Relevance
        reasons.append(f"High relevance score ({round(career_relevance_score, 0)}%) for {career_title} path.")

        # Reason 4: Prerequisites
        if prereq_satisfied:
            if c_prereqs:
                p_names = [p['name'] for p in c_prereqs]
                reasons.append(f"All prerequisites satisfied ({', '.join(p_names)} completed).")
            else:
                reasons.append("No prior course prerequisites required — start immediately.")
        else:
            missing_names = [p['name'] for p in missing_prereqs]
            reasons.append(f"Prerequisite required: Complete {', '.join(missing_names)} first.")

        # Reason 5: Difficulty & Semester fit
        reasons.append(f"{difficulty} difficulty level is optimal for Semester {semester} students.")

        breakdown = {
            "skill_gap_match": round(skill_gap_match_score, 1),
            "career_relevance": round(career_relevance_score, 1),
            "interest_match": round(interest_match_score, 1),
            "difficulty_fit": round(difficulty_fit_score, 1),
            "prerequisite_compat": round(prereq_score, 1),
            "reasons": reasons
        }

        recommendations.append({
            "course_id": cid,
            "course_code": code,
            "name": name,
            "category": category,
            "description": desc,
            "difficulty": difficulty,
            "duration_weeks": duration,
            "estimated_hours": hours,
            "skills": c_skill_names,
            "prerequisites": c_prereqs,
            "prereq_satisfied": prereq_satisfied,
            "missing_prereqs": missing_prereqs,
            "match_score": final_match_score,
            "status": status,
            "breakdown": breakdown
        })

    # Sort recommendations from highest score to lowest
    recommendations.sort(key=lambda x: (x["status"] == 'completed', -x["match_score"]))

    # Save top recommendations to recommendations database log
    cursor.execute("DELETE FROM recommendations WHERE student_id = ?", (student_id,))
    rec_log = [
        (student_id, r["course_id"], r["match_score"], json.dumps(r["breakdown"]))
        for r in recommendations[:20]
    ]
    cursor.executemany("""
        INSERT INTO recommendations (student_id, course_id, match_score, breakdown_json)
        VALUES (?, ?, ?, ?)
    """, rec_log)
    conn.commit()

    return recommendations
