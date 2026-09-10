import os
import sqlite3
import pandas as pd
import json
from werkzeug.security import generate_password_hash

DB_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(DB_DIR)
DB_PATH = os.path.join(DB_DIR, "database.db")
SCHEMA_PATH = os.path.join(DB_DIR, "schema.sql")
DATA_DIR = os.path.join(PROJECT_DIR, "data")
EXPORTS_DIR = os.path.join(PROJECT_DIR, "exports")

try:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(EXPORTS_DIR, exist_ok=True)
except Exception:
    pass

def seed_database(target_db_path=None):
    db_file = target_db_path
    if not db_file:
        if os.environ.get("VERCEL"):
            db_file = os.path.join("/tmp", "database.db")
        else:
            db_file = DB_PATH

    os.makedirs(os.path.dirname(db_file), exist_ok=True)
    print(f"Connecting to database at {db_file}...")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Read and execute schema
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)
    conn.commit()

    # 1. Seed Skills
    skills_data = [
        ("Excel", "Data Analytics"),
        ("SQL", "Databases"),
        ("Python", "Programming"),
        ("Java", "Programming"),
        ("JavaScript", "Web Development"),
        ("HTML", "Web Development"),
        ("CSS", "Web Development"),
        ("React", "Web Development"),
        ("Node.js", "Web Development"),
        ("Statistics", "Mathematics"),
        ("Power BI", "Data Analytics"),
        ("Tableau", "Data Analytics"),
        ("Pandas", "Data Science"),
        ("NumPy", "Data Science"),
        ("Machine Learning", "Artificial Intelligence"),
        ("Deep Learning", "Artificial Intelligence"),
        ("Git", "DevOps & Tools"),
        ("Linux", "Operating Systems"),
        ("AWS", "Cloud Computing"),
        ("Docker", "DevOps & Tools"),
        ("Kubernetes", "DevOps & Tools"),
        ("Communication", "Soft Skills"),
        ("Business Analysis", "Management"),
        ("Data Visualization", "Data Analytics"),
        ("Database Management", "Databases"),
        ("Computer Networks", "Cybersecurity & IT"),
        ("Cybersecurity Fundamentals", "Cybersecurity & IT"),
        ("Security Engineering", "Cybersecurity & IT"),
        ("UI/UX Design", "Design"),
        ("Figma", "Design"),
        ("User Research", "Design"),
        ("Data Structures", "Computer Science"),
        ("FastAPI", "Web Development"),
        ("MLOps", "DevOps & Tools"),
        ("System Design", "Software Architecture"),
        ("Reinforcement Learning", "Artificial Intelligence"),
        ("R Programming", "Data Science"),
        ("Spark", "Big Data"),
        ("Hadoop", "Big Data"),
        ("Kafka", "Big Data"),
        ("Microservices", "Software Architecture"),
        ("Data Governance", "Management"),
        ("Agile Methodology", "Management"),
        ("Next.js", "Web Development"),
        ("TypeScript", "Web Development"),
        ("PostgreSQL", "Databases"),
        ("MongoDB", "Databases"),
        ("Prompt Engineering", "Artificial Intelligence"),
        ("Product Management", "Management"),
        ("Data Engineering", "Data Engineering"),
        ("NLP", "Artificial Intelligence"),
        ("Computer Vision", "Artificial Intelligence")
    ]

    cursor.executemany("INSERT INTO skills (name, category) VALUES (?, ?)", skills_data)
    conn.commit()

    # Fetch skill dictionary for easy lookup
    cursor.execute("SELECT id, name FROM skills")
    skill_map = {name: sid for sid, name in cursor.fetchall()}

    # 2. Seed Career Roles
    career_roles_data = [
        ("Data Analyst", "Analyzes quantitative data, builds visual dashboards, and delivers actionable business metrics.", "Data & Analytics"),
        ("Data Scientist", "Builds predictive machine learning models, statistical analyses, and data processing pipelines.", "Data & Analytics"),
        ("Business Analyst", "Bridges business stakeholders and IT through requirements analysis, data insights, and storytelling.", "Business & Strategy"),
        ("Software Developer", "Designs, develops, tests, and maintains software applications using robust programming principles.", "Software Engineering"),
        ("Web Developer", "Builds responsive, high-performance web applications across frontend and backend technologies.", "Software Engineering"),
        ("Cloud Engineer", "Architects, deploys, and manages scalable infrastructure in cloud environments like AWS.", "Cloud & DevOps"),
        ("Database Administrator", "Ensures high availability, security, query optimization, and schema design for enterprise databases.", "Databases & Infrastructure"),
        ("Machine Learning Engineer", "Designs scalable AI pipelines, train neural networks, and deploys production ML models.", "Artificial Intelligence"),
        ("Cybersecurity Analyst", "Protects IT infrastructure, monitors network traffic, investigates breaches, and enforces security policies.", "Cybersecurity"),
        ("UI/UX Designer", "Crafts intuitve user experiences, interactive wireframes, design systems, and visually engaging interfaces.", "Design")
    ]

    cursor.executemany("INSERT INTO career_roles (title, description, category) VALUES (?, ?, ?)", career_roles_data)
    conn.commit()

    cursor.execute("SELECT id, title FROM career_roles")
    role_map = {title: rid for rid, title in cursor.fetchall()}

    # 3. Seed Career Skills & Weights
    # (career_role_title, skill_name, weight)
    career_skills_data = [
        # Data Analyst
        ("Data Analyst", "Excel", 4.5),
        ("Data Analyst", "SQL", 5.0),
        ("Data Analyst", "Statistics", 4.0),
        ("Data Analyst", "Python", 4.0),
        ("Data Analyst", "Power BI", 4.5),
        ("Data Analyst", "Data Visualization", 4.0),
        ("Data Analyst", "Pandas", 3.5),
        ("Data Analyst", "Tableau", 3.5),

        # Data Scientist
        ("Data Scientist", "Python", 5.0),
        ("Data Scientist", "SQL", 4.5),
        ("Data Scientist", "Statistics", 5.0),
        ("Data Scientist", "Pandas", 4.5),
        ("Data Scientist", "NumPy", 4.0),
        ("Data Scientist", "Machine Learning", 5.0),
        ("Data Scientist", "Deep Learning", 4.0),
        ("Data Scientist", "Data Visualization", 4.0),

        # Business Analyst
        ("Business Analyst", "Excel", 5.0),
        ("Business Analyst", "SQL", 4.0),
        ("Business Analyst", "Power BI", 4.5),
        ("Business Analyst", "Statistics", 3.5),
        ("Business Analyst", "Business Analysis", 5.0),
        ("Business Analyst", "Communication", 4.5),
        ("Business Analyst", "Agile Methodology", 4.0),

        # Software Developer
        ("Software Developer", "Python", 4.5),
        ("Software Developer", "Java", 4.0),
        ("Software Developer", "JavaScript", 4.5),
        ("Software Developer", "Data Structures", 5.0),
        ("Software Developer", "Git", 4.5),
        ("Software Developer", "Database Management", 4.0),
        ("Software Developer", "System Design", 4.0),

        # Web Developer
        ("Web Developer", "HTML", 5.0),
        ("Web Developer", "CSS", 5.0),
        ("Web Developer", "JavaScript", 5.0),
        ("Web Developer", "React", 4.5),
        ("Web Developer", "Node.js", 4.0),
        ("Web Developer", "Git", 4.0),
        ("Web Developer", "TypeScript", 3.5),

        # Cloud Engineer
        ("Cloud Engineer", "Linux", 4.5),
        ("Cloud Engineer", "AWS", 5.0),
        ("Cloud Engineer", "Docker", 4.5),
        ("Cloud Engineer", "Kubernetes", 4.0),
        ("Cloud Engineer", "Computer Networks", 4.0),
        ("Cloud Engineer", "Git", 3.5),

        # Database Administrator
        ("Database Administrator", "SQL", 5.0),
        ("Database Administrator", "PostgreSQL", 4.5),
        ("Database Administrator", "Database Management", 5.0),
        ("Database Administrator", "Linux", 4.0),
        ("Database Administrator", "Security Engineering", 3.5),
        ("Database Administrator", "MongoDB", 3.5),

        # Machine Learning Engineer
        ("Machine Learning Engineer", "Python", 5.0),
        ("Machine Learning Engineer", "Statistics", 4.5),
        ("Machine Learning Engineer", "Machine Learning", 5.0),
        ("Machine Learning Engineer", "Deep Learning", 4.5),
        ("Machine Learning Engineer", "MLOps", 4.5),
        ("Machine Learning Engineer", "Docker", 4.0),

        # Cybersecurity Analyst
        ("Cybersecurity Analyst", "Computer Networks", 5.0),
        ("Cybersecurity Analyst", "Linux", 4.5),
        ("Cybersecurity Analyst", "Cybersecurity Fundamentals", 5.0),
        ("Cybersecurity Analyst", "Security Engineering", 4.5),
        ("Cybersecurity Analyst", "Python", 3.5),

        # UI/UX Designer
        ("UI/UX Designer", "Figma", 5.0),
        ("UI/UX Designer", "UI/UX Design", 5.0),
        ("UI/UX Designer", "User Research", 4.5),
        ("UI/UX Designer", "HTML", 3.5),
        ("UI/UX Designer", "CSS", 3.5),
        ("UI/UX Designer", "Communication", 4.0)
    ]

    cs_rows = []
    for rtitle, sname, weight in career_skills_data:
        if rtitle in role_map and sname in skill_map:
            cs_rows.append((role_map[rtitle], skill_map[sname], weight))

    cursor.executemany("INSERT INTO career_skills (career_role_id, skill_id, weight) VALUES (?, ?, ?)", cs_rows)
    conn.commit()

    # 4. Seed 52 Courses
    raw_courses = [
        # (code, name, category, desc, difficulty, wks, hrs, [skills], [prereq_codes])
        ("CS101", "Python Fundamentals", "Computer Science", "Learn the essential syntax, control flows, data types, and functions in Python.", "Beginner", 4, 20, ["Python"], []),
        ("CS102", "Advanced Python Programming", "Computer Science", "Master OOP, decorators, generators, multi-threading, and advanced modules in Python.", "Intermediate", 6, 30, ["Python"], ["CS101"]),
        ("DB101", "SQL Fundamentals", "Databases", "Master relational queries, SELECT, JOIN, GROUP BY, and basic database normalization.", "Beginner", 4, 20, ["SQL", "Database Management"], []),
        ("DB102", "Advanced SQL & Query Optimization", "Databases", "Learn window functions, CTEs, indexing, query execution plans, and stored procedures.", "Intermediate", 6, 30, ["SQL", "Database Management"], ["DB101"]),
        ("DA101", "Excel for Data Analysis & BI", "Data Analytics", "Use VLOOKUP, INDEX-MATCH, Pivot Tables, and financial formulas for business intelligence.", "Beginner", 3, 15, ["Excel", "Business Analysis"], []),
        ("MATH101", "Applied Statistics & Probability", "Mathematics", "Understand mean, variance, hypothesis testing, p-values, regression, and distributions.", "Beginner", 5, 25, ["Statistics"], []),
        ("BI101", "Power BI Dashboard Mastery", "Data Analytics", "Connect datasets, model DAX relationships, and build interactive executive dashboards in Power BI.", "Intermediate", 4, 20, ["Power BI", "Data Visualization"], ["DA101", "DB101"]),
        ("BI102", "Tableau Essentials for Visual Storytelling", "Data Analytics", "Transform raw data into captivating interactive charts and dashboards using Tableau.", "Intermediate", 4, 20, ["Tableau", "Data Visualization"], ["DA101"]),
        ("DA102", "Data Visualization with Python", "Data Analytics", "Create charts with Matplotlib, Seaborn, and Plotly to convey statistical insights.", "Intermediate", 4, 20, ["Data Visualization", "Python", "Pandas"], ["CS101"]),
        ("DA103", "Data Analysis with Pandas & NumPy", "Data Analytics", "Perform data cleaning, reshaping, indexing, aggregations, and numerical calculations.", "Intermediate", 5, 25, ["Pandas", "NumPy", "Python"], ["CS101"]),
        ("ML101", "Introduction to Machine Learning", "Artificial Intelligence", "Supervised and unsupervised algorithms: Linear Regression, Decision Trees, K-Means, and SVM.", "Intermediate", 8, 40, ["Machine Learning", "Python", "Statistics"], ["CS101", "DA103", "MATH101"]),
        ("ML102", "Applied Deep Learning & Neural Networks", "Artificial Intelligence", "Build CNNs, RNNs, and Transformers using PyTorch/TensorFlow for deep learning tasks.", "Advanced", 8, 45, ["Deep Learning", "Python", "Machine Learning"], ["ML101"]),
        ("DB103", "Database Management Systems (DBMS)", "Databases", "ACID properties, relational algebra, concurrency control, and database architecture.", "Intermediate", 6, 30, ["Database Management", "SQL"], ["DB101"]),
        ("WEB101", "HTML5 & CSS3 Web Fundamentals", "Web Development", "Build semantic HTML documents and responsive layouts with modern CSS Flexbox and Grid.", "Beginner", 3, 15, ["HTML", "CSS"], []),
        ("WEB102", "Modern JavaScript Essentials", "Web Development", "ES6+ syntax, async programming, DOM manipulation, promises, and fetch API.", "Beginner", 5, 25, ["JavaScript"], ["WEB101"]),
        ("WEB103", "React.js Frontend Framework", "Web Development", "Component architecture, hooks, state management, router, and virtual DOM concepts.", "Intermediate", 6, 30, ["React", "JavaScript"], ["WEB102"]),
        ("WEB104", "Node.js & Express Backend Architecture", "Web Development", "Build RESTful APIs, event loop, middleware, JWT auth, and database integration.", "Intermediate", 6, 30, ["Node.js", "JavaScript", "Database Management"], ["WEB102"]),
        ("DEV101", "Git & GitHub Version Control", "DevOps", "Version management, branching, merging, pull requests, and collaborative Git workflows.", "Beginner", 2, 10, ["Git"], []),
        ("CLOUD101", "Cloud Computing Fundamentals", "Cloud Computing", "Understand cloud service models (IaaS, PaaS, SaaS), virtualization, and cloud providers.", "Beginner", 4, 20, ["AWS"], []),
        ("CLOUD102", "AWS Solutions Architecture", "Cloud Computing", "Architect resilient cloud architectures using EC2, S3, RDS, IAM, VPC, and Lambda.", "Intermediate", 6, 35, ["AWS"], ["CLOUD101"]),
        ("SYS101", "Linux System Administration & Bash", "Operating Systems", "CLI mastery, file permissions, process management, shell scripting, and environment config.", "Beginner", 4, 20, ["Linux"], []),
        ("NET101", "Computer Networks & Internet Protocols", "Network & IT", "TCP/IP stack, OSI model, routing, DNS, HTTP/S, and network diagnostics.", "Intermediate", 6, 30, ["Computer Networks"], ["SYS101"]),
        ("SEC101", "Cybersecurity Fundamentals & Defense", "Cybersecurity", "Core security concepts: CIA triad, cryptography, firewall design, and threat mitigation.", "Beginner", 5, 25, ["Cybersecurity Fundamentals", "Computer Networks"], ["NET101"]),
        ("UI101", "UI/UX Design Principles & Wireframing", "Design", "User-centered design, wireframing, color theory, typography, and usability testing.", "Beginner", 4, 20, ["UI/UX Design", "User Research"], []),
        ("UI102", "Figma Masterclass for UI Designers", "Design", "Master Figma components, auto-layout, interactive prototypes, and design systems.", "Beginner", 3, 15, ["Figma", "UI/UX Design"], ["UI101"]),
        ("BI103", "Business Analytics & Problem Solving", "Business", "Deconstruct business challenges, define KPIs, perform root cause analysis, and report metrics.", "Intermediate", 5, 25, ["Business Analysis", "Communication"], ["DA101"]),
        ("CS103", "Data Structures & Algorithms in Java", "Computer Science", "Arrays, Linked Lists, Trees, Graphs, Sorting algorithms, and Time/Space complexity.", "Intermediate", 8, 40, ["Data Structures", "Java"], []),
        ("DEV102", "Docker & Containerization Essentials", "DevOps", "Create Dockerfiles, containerize applications, manage volumes, network bridge, and Compose.", "Intermediate", 4, 20, ["Docker", "Linux"], ["SYS101"]),
        ("DEV103", "Kubernetes Orchestration for Engineers", "DevOps", "Deploy scalable microservices using K8s Pods, Deployments, Services, and Ingress.", "Advanced", 6, 30, ["Kubernetes", "Docker"], ["DEV102"]),
        ("WEB105", "API Development with FastAPI & Python", "Web Development", "Build lightning-fast async RESTful APIs with auto Swagger docs, Pydantic, and SQLAlchemy.", "Intermediate", 4, 20, ["FastAPI", "Python"], ["CS101"]),
        ("WEB106", "Full-Stack Web Development with Django", "Web Development", "Build secure full-stack web applications with Django ORM, authentication, and templates.", "Intermediate", 7, 35, ["Python", "HTML", "CSS", "JavaScript", "SQL"], ["CS101", "WEB101"]),
        ("ML103", "Natural Language Processing (NLP) with Python", "Artificial Intelligence", "Tokenization, TF-IDF, Word Embeddings, Sentiment Analysis, and Transformers with HuggingFace.", "Advanced", 6, 30, ["NLP", "Python", "Machine Learning"], ["ML101"]),
        ("ML104", "Computer Vision & OpenCV Essentials", "Artificial Intelligence", "Image processing, object detection, segmentation, and CNN architectures using OpenCV and PyTorch.", "Advanced", 6, 30, ["Computer Vision", "Python", "Deep Learning"], ["ML102"]),
        ("ML105", "MLOps: Machine Learning Model Deployment", "DevOps", "Model registry, automated CI/CD pipelines, Docker deployment, and drift monitoring.", "Advanced", 6, 35, ["MLOps", "Docker", "AWS", "Machine Learning"], ["ML101", "DEV102"]),
        ("CS104", "System Design & Distributed Architecture", "Software Engineering", "Load balancers, caching strategies, horizontal scaling, database sharding, and message queues.", "Advanced", 8, 40, ["System Design", "Database Management"], ["CS103", "WEB104"]),
        ("ML106", "Reinforcement Learning Foundations", "Artificial Intelligence", "Markov Decision Processes, Q-Learning, Deep Q-Networks (DQN), and Policy Gradients.", "Advanced", 6, 30, ["Reinforcement Learning", "Python"], ["ML101"]),
        ("DA104", "R Programming for Statistical Computing", "Data Analytics", "Data manipulation with dplyr, ggplot2 graphics, and statistical model fitting in R.", "Intermediate", 5, 25, ["R Programming", "Statistics"], ["MATH101"]),
        ("DE101", "Apache Spark for Big Data Analytics", "Big Data", "Distributed dataframes, Spark SQL, PySpark processing, and streaming pipelines.", "Advanced", 6, 30, ["Spark", "Python"], ["CS101", "DA103"]),
        ("DE102", "Big Data Infrastructure with Hadoop & Hive", "Big Data", "HDFS architecture, MapReduce paradigms, data warehousing with Apache Hive.", "Advanced", 7, 35, ["Hadoop", "SQL"], ["DB102"]),
        ("DE103", "Event-Driven Streaming with Apache Kafka", "Big Data", "Producers, consumers, Kafka brokers, event streaming, and real-time data integration.", "Advanced", 5, 25, ["Kafka", "Java", "System Design"], ["CS103"]),
        ("CS105", "Microservices Architecture & Design Patterns", "Software Engineering", "Service discovery, API gateway pattern, event-driven decoupling, and fault tolerance.", "Advanced", 6, 30, ["Microservices", "System Design", "Docker"], ["DEV102", "WEB104"]),
        ("SEC102", "Ethical Hacking & Penetration Testing", "Cybersecurity", "Vulnerability assessment, network sniffing, exploit frameworks, and security auditing.", "Intermediate", 7, 35, ["Cybersecurity Fundamentals", "Linux", "Computer Networks"], ["SEC101"]),
        ("SEC103", "Cloud Security Architecture & Compliance", "Cybersecurity", "IAM policy hardening, VPC isolation, zero-trust models, and cloud compliance auditing.", "Advanced", 6, 30, ["Security Engineering", "AWS"], ["SEC101", "CLOUD102"]),
        ("DA105", "Data Governance, Ethics & Quality Control", "Data Analytics", "Data lineage, privacy regulations (GDPR/HIPAA), data cataloging, and quality frameworks.", "Intermediate", 4, 20, ["Data Governance", "Business Analysis"], []),
        ("MGMT101", "Agile & Scrum Methodologies for Teams", "Management", "Scrum ceremonies, user stories, backlog grooming, sprint velocity, and Kanban.", "Beginner", 3, 15, ["Agile Methodology", "Communication"], []),
        ("WEB107", "Next.js Framework & Server-Side Rendering", "Web Development", "App Router, SSR, SSG, API routes, and full-stack React performance optimization.", "Intermediate", 5, 25, ["Next.js", "React", "JavaScript"], ["WEB103"]),
        ("WEB108", "TypeScript Essentials for Enterprise Apps", "Web Development", "Static typing, interfaces, generics, type guards, and TypeScript integration in React/Node.", "Intermediate", 4, 20, ["TypeScript", "JavaScript"], ["WEB102"]),
        ("DB104", "PostgreSQL Query Tuning & Optimization", "Databases", "EXPLAIN ANALYZE, custom indexing, table partitioning, and high-performance tuning.", "Advanced", 5, 25, ["PostgreSQL", "SQL", "Database Management"], ["DB102"]),
        ("DB105", "NoSQL Databases with MongoDB", "Databases", "Document stores, BSON schemas, aggregation framework, and replication sets.", "Intermediate", 4, 20, ["MongoDB", "Database Management"], ["DB101"]),
        ("ML107", "Generative AI & Prompt Engineering", "Artificial Intelligence", "LLM architectures, prompt design techniques, RAG pipelines, and API integrations.", "Intermediate", 4, 20, ["Prompt Engineering", "Python"], ["CS101"]),
        ("MGMT102", "Product Management Essentials for Tech", "Management", "Product strategy, roadmapping, feature prioritization, customer feedback loops, and analytics.", "Intermediate", 5, 25, ["Product Management", "Business Analysis"], []),
        ("DE104", "Data Engineering Pipelines with Apache Airflow", "Data Analytics", "DAG workflow orchestration, task dependencies, custom operators, and data ETL pipelines.", "Advanced", 6, 30, ["Data Engineering", "Python", "SQL"], ["CS101", "DB102"])
    ]

    print(f"Seeding {len(raw_courses)} realistic courses...")

    course_code_to_id = {}
    prereq_pairs = []

    for code, name, cat, desc, diff, wks, hrs, sk_list, prereq_list in raw_courses:
        cursor.execute(
            "INSERT INTO courses (course_code, name, category, description, difficulty, duration_weeks, estimated_hours) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (code, name, cat, desc, diff, wks, hrs)
        )
        cid = cursor.lastrowid
        course_code_to_id[code] = cid

        # Link course skills
        for sname in sk_list:
            if sname in skill_map:
                cursor.execute("INSERT OR IGNORE INTO course_skills (course_id, skill_id) VALUES (?, ?)", (cid, skill_map[sname]))

        # Queue prerequisites
        for pcode in prereq_list:
            prereq_pairs.append((code, pcode))

    conn.commit()

    # Link course prerequisites
    for code, pcode in prereq_pairs:
        if code in course_code_to_id and pcode in course_code_to_id:
            cursor.execute(
                "INSERT OR IGNORE INTO course_prerequisites (course_id, prerequisite_course_id) VALUES (?, ?)",
                (course_code_to_id[code], course_code_to_id[pcode])
            )
    conn.commit()

    # 5. Seed Sample Students
    da_role_id = role_map.get("Data Analyst")
    ds_role_id = role_map.get("Data Scientist")
    default_pwd_hash = generate_password_hash("password123")

    students = [
        ("Alex Mercer", "alex.mercer@univ.edu", default_pwd_hash, "B.Tech CSE", "Computer Science", 5, 8.4, da_role_id),
        ("Sarah Jenkins", "sarah.j@univ.edu", default_pwd_hash, "B.S. Data Science", "Information Technology", 6, 9.1, ds_role_id)
    ]

    cursor.executemany(
        "INSERT INTO students (name, email, password_hash, degree, branch, semester, cgpa, target_career_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        students
    )
    conn.commit()

    alex_id = 1
    # Give Alex initial skills (Excel, SQL)
    alex_skills = ["Excel", "SQL"]
    for sk in alex_skills:
        if sk in skill_map:
            cursor.execute("INSERT INTO student_skills (student_id, skill_id, proficiency_level) VALUES (?, ?, ?)", (alex_id, skill_map[sk], "Intermediate"))

    # Alex interests
    alex_interests = ["Data Analytics", "Business Intelligence", "Machine Learning"]
    for int_name in alex_interests:
        cursor.execute("INSERT INTO student_interests (student_id, interest_name) VALUES (?, ?)", (alex_id, int_name))

    # Alex completed courses (DA101: Excel, DB101: SQL)
    if "DA101" in course_code_to_id:
        cursor.execute("INSERT INTO student_courses (student_id, course_id, status, progress_pct) VALUES (?, ?, 'completed', 100)", (alex_id, course_code_to_id["DA101"]))
    if "DB101" in course_code_to_id:
        cursor.execute("INSERT INTO student_courses (student_id, course_id, status, progress_pct) VALUES (?, ?, 'completed', 100)", (alex_id, course_code_to_id["DB101"]))
    if "CS101" in course_code_to_id:
        cursor.execute("INSERT INTO student_courses (student_id, course_id, status, progress_pct) VALUES (?, ?, 'in_progress', 65)", (alex_id, course_code_to_id["CS101"]))

    conn.commit()
    conn.close()
    print("Database seeding completed successfully!")

    export_static_csvs(db_file)

def export_static_csvs(target_db_path=None):
    try:
        db_file = target_db_path
        if not db_file:
            if os.environ.get("VERCEL"):
                db_file = os.path.join("/tmp", "database.db")
            else:
                db_file = DB_PATH

        conn = sqlite3.connect(db_file)
        courses_df = pd.read_sql_query("SELECT * FROM courses", conn)
        skills_df = pd.read_sql_query("SELECT * FROM skills", conn)
        roles_df = pd.read_sql_query("SELECT * FROM career_roles", conn)
        conn.close()

        target_data_dir = os.path.join("/tmp", "data") if os.environ.get("VERCEL") else DATA_DIR
        os.makedirs(target_data_dir, exist_ok=True)

        courses_df.to_csv(os.path.join(target_data_dir, "courses.csv"), index=False)
        skills_df.to_csv(os.path.join(target_data_dir, "skills.csv"), index=False)
        roles_df.to_csv(os.path.join(target_data_dir, "career_roles.csv"), index=False)
        print("CSV files exported successfully.")
    except Exception as e:
        print(f"CSV export warning (non-fatal): {e}")

if __name__ == "__main__":
    seed_database()
