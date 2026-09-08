-- Database Schema for Intelligent Course Recommendation & Academic Path Planning System

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS recommendations;
DROP TABLE IF EXISTS career_skills;
DROP TABLE IF EXISTS course_prerequisites;
DROP TABLE IF EXISTS course_skills;
DROP TABLE IF EXISTS student_courses;
DROP TABLE IF EXISTS student_interests;
DROP TABLE IF EXISTS student_skills;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS career_roles;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS skills;

-- Skills Table
CREATE TABLE skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL
);

-- Career Roles Table
CREATE TABLE career_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL UNIQUE,
    description TEXT,
    category TEXT NOT NULL
);

-- Courses Table
CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    difficulty TEXT NOT NULL CHECK(difficulty IN ('Beginner', 'Intermediate', 'Advanced')),
    duration_weeks INTEGER NOT NULL,
    estimated_hours INTEGER NOT NULL
);

-- Students Table
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    degree TEXT DEFAULT 'B.Tech CSE',
    branch TEXT DEFAULT 'Computer Science & Engineering',
    semester INTEGER DEFAULT 5,
    cgpa REAL DEFAULT 8.0,
    target_career_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (target_career_id) REFERENCES career_roles(id) ON DELETE SET NULL
);

-- Student Skills (Many-to-Many)
CREATE TABLE student_skills (
    student_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    proficiency_level TEXT DEFAULT 'Intermediate',
    PRIMARY KEY (student_id, skill_id),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- Student Interests
CREATE TABLE student_interests (
    student_id INTEGER NOT NULL,
    interest_name TEXT NOT NULL,
    PRIMARY KEY (student_id, interest_name),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- Student Course Enrollment / Progress (Many-to-Many)
CREATE TABLE student_courses (
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('in_progress', 'completed', 'saved')),
    progress_pct INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);

-- Course Skills (Many-to-Many)
CREATE TABLE course_skills (
    course_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    PRIMARY KEY (course_id, skill_id),
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- Course Prerequisites (Many-to-Many Self Reference)
CREATE TABLE course_prerequisites (
    course_id INTEGER NOT NULL,
    prerequisite_course_id INTEGER NOT NULL,
    PRIMARY KEY (course_id, prerequisite_course_id),
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY (prerequisite_course_id) REFERENCES courses(id) ON DELETE CASCADE
);

-- Career Role Skills & Weights (Many-to-Many)
CREATE TABLE career_skills (
    career_role_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    weight REAL DEFAULT 1.0, -- Importance score from 1.0 to 5.0
    PRIMARY KEY (career_role_id, skill_id),
    FOREIGN KEY (career_role_id) REFERENCES career_roles(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- Generated Recommendations Log
CREATE TABLE recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    match_score REAL NOT NULL,
    breakdown_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);
