"""
curriculum_data.py - Inbuilt Anna University Curricula Repository
Regulations: R2021, R2023, R2025
Degrees: B.E., B.Tech
Departments: CSE, IT, AIDS, ECE, EEE, MECH, CIVIL, BME, CSBS, CYBER
Semesters: Semester 1 through Semester 8
"""

from typing import Dict, List, Any, Optional

# ══════════════════════════════════════════════════════════════════════════════
# COMMON FIRST YEAR (SEMESTER 1 & 2)
# ══════════════════════════════════════════════════════════════════════════════

SEM1_COMMON = [
    {"subject_code": "IP3151", "subject_name": "Induction Programme", "abbreviation": "IP", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 1, "credits": 0},
    {"subject_code": "HS3151", "subject_name": "Professional English - I", "abbreviation": "ENG-1", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 3},
    {"subject_code": "MA3151", "subject_name": "Matrices and Calculus", "abbreviation": "M-1", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "PH3151", "subject_name": "Engineering Physics", "abbreviation": "PHY", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "CY3151", "subject_name": "Engineering Chemistry", "abbreviation": "CHEM", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "GE3151", "subject_name": "Problem Solving and Python Programming", "abbreviation": "PYTHON", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "GE3152", "subject_name": "Heritage of Tamils", "abbreviation": "TAMIL-1", "periods_per_week": 1, "is_lab": False, "lab_duration": 0, "difficulty_level": 1, "credits": 1},
    {"subject_code": "GE3171", "subject_name": "Problem Solving and Python Programming Laboratory", "abbreviation": "PY LAB", "periods_per_week": 4, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 2},
    {"subject_code": "BS3171", "subject_name": "Physics and Chemistry Laboratory", "abbreviation": "P/C LAB", "periods_per_week": 4, "is_lab": True, "lab_duration": 2, "difficulty_level": 3, "credits": 2},
    {"subject_code": "GE3172", "subject_name": "English Laboratory", "abbreviation": "ENG LAB", "periods_per_week": 2, "is_lab": True, "lab_duration": 2, "difficulty_level": 2, "credits": 1}
]

SEM2_CIRCUIT = [
    {"subject_code": "HS3252", "subject_name": "Professional English - II", "abbreviation": "ENG-2", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
    {"subject_code": "MA3251", "subject_name": "Statistics and Numerical Methods", "abbreviation": "SNM", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "PH3256", "subject_name": "Physics for Information Science", "abbreviation": "PIS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "BE3251", "subject_name": "Basic Electrical and Electronics Engineering", "abbreviation": "BEEE", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "GE3251", "subject_name": "Engineering Graphics", "abbreviation": "EG", "periods_per_week": 4, "is_lab": True, "lab_duration": 3, "difficulty_level": 4, "credits": 4},
    {"subject_code": "CS3251", "subject_name": "Programming in C", "abbreviation": "C PROG", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "GE3252", "subject_name": "Tamils and Technology", "abbreviation": "TAMIL-2", "periods_per_week": 1, "is_lab": False, "lab_duration": 0, "difficulty_level": 1, "credits": 1},
    {"subject_code": "GE3271", "subject_name": "Engineering Practices Laboratory", "abbreviation": "EP LAB", "periods_per_week": 4, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 2},
    {"subject_code": "CS3271", "subject_name": "Programming in C Laboratory", "abbreviation": "C LAB", "periods_per_week": 4, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 2}
]

SEM2_NON_CIRCUIT = [
    {"subject_code": "HS3252", "subject_name": "Professional English - II", "abbreviation": "ENG-2", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
    {"subject_code": "MA3251", "subject_name": "Statistics and Numerical Methods", "abbreviation": "SNM", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "PH3251", "subject_name": "Materials Science", "abbreviation": "MAT SCI", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "BE3252", "subject_name": "Basic Electrical, Electronics and Instrumentation Engineering", "abbreviation": "BEEI", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "GE3251", "subject_name": "Engineering Graphics", "abbreviation": "EG", "periods_per_week": 4, "is_lab": True, "lab_duration": 3, "difficulty_level": 4, "credits": 4},
    {"subject_code": "GE3252", "subject_name": "Tamils and Technology", "abbreviation": "TAMIL-2", "periods_per_week": 1, "is_lab": False, "lab_duration": 0, "difficulty_level": 1, "credits": 1},
    {"subject_code": "GE3271", "subject_name": "Engineering Practices Laboratory", "abbreviation": "EP LAB", "periods_per_week": 4, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 2}
]

# ══════════════════════════════════════════════════════════════════════════════
# REGULATION 2021 (R2021) CURRICULA
# ══════════════════════════════════════════════════════════════════════════════

R2021_DATA = {
    # ── CSE ──
    ("B.E.", "CSE", "Semester 1"): SEM1_COMMON,
    ("B.E.", "CSE", "Semester 2"): SEM2_CIRCUIT,
    ("B.E.", "CSE", "Semester 3"): [
        {"subject_code": "MA3354", "subject_name": "Discrete Mathematics", "abbreviation": "DM", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "CS3351", "subject_name": "Digital Principles and Computer Organization", "abbreviation": "DPCO", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "CS3352", "subject_name": "Foundations of Data Science", "abbreviation": "FDS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "CS3301", "subject_name": "Data Structures", "abbreviation": "DS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "CS3391", "subject_name": "Object Oriented Programming", "abbreviation": "OOP", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "CS3381", "subject_name": "Data Structures Laboratory", "abbreviation": "DS LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "CS3361", "subject_name": "Object Oriented Programming Laboratory", "abbreviation": "OOP LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "GE3361", "subject_name": "Professional Development", "abbreviation": "PD LAB", "periods_per_week": 2, "is_lab": True, "lab_duration": 2, "difficulty_level": 2, "credits": 1}
    ],
    ("B.E.", "CSE", "Semester 4"): [
        {"subject_code": "CS3452", "subject_name": "Theory of Computation", "abbreviation": "TOC", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "CS3491", "subject_name": "Artificial Intelligence and Machine Learning", "abbreviation": "AIML", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "CS3492", "subject_name": "Database Management Systems", "abbreviation": "DBMS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "CS3401", "subject_name": "Algorithms", "abbreviation": "DAA", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "CS3451", "subject_name": "Introduction to Operating Systems", "abbreviation": "OS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "GE3451", "subject_name": "Environmental Sciences and Sustainability", "abbreviation": "EVS", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
        {"subject_code": "CS3461", "subject_name": "Database Management Systems Laboratory", "abbreviation": "DBMS LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "CS3481", "subject_name": "Operating Systems Laboratory", "abbreviation": "OS LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ],
    ("B.E.", "CSE", "Semester 5"): [
        {"subject_code": "CS3591", "subject_name": "Computer Networks", "abbreviation": "CN", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "CS3501", "subject_name": "Compiler Design", "abbreviation": "CD", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "CB3491", "subject_name": "Cryptography and Cyber Security", "abbreviation": "CCS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "CS3551", "subject_name": "Distributed Computing", "abbreviation": "DC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "PE3501", "subject_name": "Professional Elective I (Cloud Computing / Agile)", "abbreviation": "PE-1", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
        {"subject_code": "MC3501", "subject_name": "Mandatory Course: Constitution of India", "abbreviation": "COI", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 0},
        {"subject_code": "CS3561", "subject_name": "Compiler Design Laboratory", "abbreviation": "CD LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "CS3562", "subject_name": "Networks and Security Laboratory", "abbreviation": "NET LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ],
    ("B.E.", "CSE", "Semester 6"): [
        {"subject_code": "CCS334", "subject_name": "Big Data Analytics", "abbreviation": "BDA", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "CS3691", "subject_name": "Embedded Systems and IoT", "abbreviation": "IOT", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "PE3602", "subject_name": "Professional Elective II (Deep Learning)", "abbreviation": "PE-2", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "PE3603", "subject_name": "Professional Elective III (Software Testing)", "abbreviation": "PE-3", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
        {"subject_code": "OE3601", "subject_name": "Open Elective I", "abbreviation": "OE-1", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
        {"subject_code": "CS3661", "subject_name": "Embedded Systems and IoT Laboratory", "abbreviation": "IOT LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "CS3681", "subject_name": "Mini Project / Socially Relevant Project", "abbreviation": "PROJECT", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ],
    ("B.E.", "CSE", "Semester 7"): [
        {"subject_code": "GE3791", "subject_name": "Human Values and Ethics", "abbreviation": "HVE", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
        {"subject_code": "CS3701", "subject_name": "Software Project Management", "abbreviation": "SPM", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
        {"subject_code": "PE3704", "subject_name": "Professional Elective IV (Block Chain)", "abbreviation": "PE-4", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "PE3705", "subject_name": "Professional Elective V (Quantum Computing)", "abbreviation": "PE-5", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "OE3702", "subject_name": "Open Elective II", "abbreviation": "OE-2", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
        {"subject_code": "CS3781", "subject_name": "Project Work Phase I", "abbreviation": "PROJ-1", "periods_per_week": 4, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 2}
    ],
    ("B.E.", "CSE", "Semester 8"): [
        {"subject_code": "CS3881", "subject_name": "Project Work Phase II / Industrial Internship", "abbreviation": "PROJ-2", "periods_per_week": 12, "is_lab": True, "lab_duration": 4, "difficulty_level": 4, "credits": 10}
    ],

    # ── IT ──
    ("B.Tech.", "IT", "Semester 1"): SEM1_COMMON,
    ("B.Tech.", "IT", "Semester 2"): SEM2_CIRCUIT,
    ("B.Tech.", "IT", "Semester 3"): [
        {"subject_code": "MA3354", "subject_name": "Discrete Mathematics", "abbreviation": "DM", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "CS3351", "subject_name": "Digital Principles and Computer Organization", "abbreviation": "DPCO", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "IT3301", "subject_name": "Data Structures and Algorithms", "abbreviation": "DSA", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "IT3351", "subject_name": "Object Oriented Programming in Java", "abbreviation": "JAVA", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "IT3352", "subject_name": "Web Technology", "abbreviation": "WT", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
        {"subject_code": "IT3381", "subject_name": "Data Structures Laboratory", "abbreviation": "DS LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "IT3361", "subject_name": "Java Programming Laboratory", "abbreviation": "JAVA LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "GE3361", "subject_name": "Professional Development", "abbreviation": "PD LAB", "periods_per_week": 2, "is_lab": True, "lab_duration": 2, "difficulty_level": 2, "credits": 1}
    ],
    ("B.Tech.", "IT", "Semester 4"): [
        {"subject_code": "CS3491", "subject_name": "Artificial Intelligence and Machine Learning", "abbreviation": "AIML", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "CS3492", "subject_name": "Database Management Systems", "abbreviation": "DBMS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "IT3401", "subject_name": "Web Essentials", "abbreviation": "WE", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
        {"subject_code": "CS3451", "subject_name": "Introduction to Operating Systems", "abbreviation": "OS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "GE3451", "subject_name": "Environmental Sciences and Sustainability", "abbreviation": "EVS", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
        {"subject_code": "CS3461", "subject_name": "Database Management Systems Laboratory", "abbreviation": "DBMS LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "IT3481", "subject_name": "Web Application Development Laboratory", "abbreviation": "WEB LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ],

    # ── AI & DS ──
    ("B.Tech.", "AIDS", "Semester 1"): SEM1_COMMON,
    ("B.Tech.", "AIDS", "Semester 2"): SEM2_CIRCUIT,
    ("B.Tech.", "AIDS", "Semester 3"): [
        {"subject_code": "MA3354", "subject_name": "Discrete Mathematics", "abbreviation": "DM", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "AD3351", "subject_name": "Design and Analysis of Algorithms", "abbreviation": "DAA", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "CS3352", "subject_name": "Foundations of Data Science", "abbreviation": "FDS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "AD3301", "subject_name": "Data Structures and Modern Tools", "abbreviation": "DS-MT", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "AD3391", "subject_name": "Database Design and Management", "abbreviation": "DDM", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "AD3381", "subject_name": "Data Structures and Algorithm Laboratory", "abbreviation": "DSA LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "AD3361", "subject_name": "Data Science Tools Laboratory", "abbreviation": "DS TOOLS", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "GE3361", "subject_name": "Professional Development", "abbreviation": "PD LAB", "periods_per_week": 2, "is_lab": True, "lab_duration": 2, "difficulty_level": 2, "credits": 1}
    ],
    ("B.Tech.", "AIDS", "Semester 4"): [
        {"subject_code": "MA3452", "subject_name": "Linear Algebra and Statistics for Data Science", "abbreviation": "LAS", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "AD3491", "subject_name": "Fundamentals of Machine Learning", "abbreviation": "FML", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "AD3401", "subject_name": "Data Analytics and Visualization", "abbreviation": "DAV", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
        {"subject_code": "CS3451", "subject_name": "Operating Systems & Virtualization", "abbreviation": "OS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "GE3451", "subject_name": "Environmental Sciences and Sustainability", "abbreviation": "EVS", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
        {"subject_code": "AD3461", "subject_name": "Machine Learning Laboratory", "abbreviation": "ML LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "AD3481", "subject_name": "Data Analytics Laboratory", "abbreviation": "DA LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ],

    # ── ECE ──
    ("B.E.", "ECE", "Semester 1"): SEM1_COMMON,
    ("B.E.", "ECE", "Semester 2"): SEM2_CIRCUIT,
    ("B.E.", "ECE", "Semester 3"): [
        {"subject_code": "MA3355", "subject_name": "Random Processes and Linear Algebra", "abbreviation": "RPLA", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "EC3354", "subject_name": "Signals and Systems", "abbreviation": "SS", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "EC3353", "subject_name": "Electronic Devices and Circuits", "abbreviation": "EDC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "EC3351", "subject_name": "Control Systems", "abbreviation": "CS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "EC3352", "subject_name": "Digital Systems Design", "abbreviation": "DSD", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "EC3361", "subject_name": "Electronic Devices and Circuits Laboratory", "abbreviation": "EDC LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "EC3362", "subject_name": "Digital Systems Design Laboratory", "abbreviation": "DSD LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ],
    ("B.E.", "ECE", "Semester 4"): [
        {"subject_code": "EC3452", "subject_name": "Electromagnetic Fields", "abbreviation": "EMF", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "EC3401", "subject_name": "Networks and Security", "abbreviation": "NET", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "EC3451", "subject_name": "Linear Integrated Circuits", "abbreviation": "LIC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "EC3492", "subject_name": "Digital Signal Processing", "abbreviation": "DSP", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "EC3491", "subject_name": "Communication Systems", "abbreviation": "COMM", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "EC3461", "subject_name": "Communication Systems Laboratory", "abbreviation": "COMM LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "EC3462", "subject_name": "Linear Integrated Circuits Laboratory", "abbreviation": "LIC LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ],

    # ── EEE ──
    ("B.E.", "EEE", "Semester 1"): SEM1_COMMON,
    ("B.E.", "EEE", "Semester 2"): SEM2_CIRCUIT,
    ("B.E.", "EEE", "Semester 3"): [
        {"subject_code": "MA3353", "subject_name": "Linear Algebra and Numerical Methods", "abbreviation": "LANM", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "EE3301", "subject_name": "Electromagnetic Fields", "abbreviation": "EMF", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "EE3302", "subject_name": "Digital Logic Circuits", "abbreviation": "DLC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "EE3303", "subject_name": "Electrical Machines - I", "abbreviation": "EM-1", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "EC3301", "subject_name": "Electron Devices and Circuits", "abbreviation": "EDC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "EE3311", "subject_name": "Electrical Machines Laboratory - I", "abbreviation": "EM1 LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "EC3311", "subject_name": "Electronic Devices and Circuits Laboratory", "abbreviation": "EDC LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ],

    # ── MECH ──
    ("B.E.", "MECH", "Semester 1"): SEM1_COMMON,
    ("B.E.", "MECH", "Semester 2"): SEM2_NON_CIRCUIT,
    ("B.E.", "MECH", "Semester 3"): [
        {"subject_code": "MA3351", "subject_name": "Transforms and Partial Differential Equations", "abbreviation": "TPDE", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "ME3351", "subject_name": "Engineering Thermodynamics", "abbreviation": "THERMO", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "ME3391", "subject_name": "Fluid Mechanics and Machinery", "abbreviation": "FMM", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "ME3392", "subject_name": "Engineering Materials and Metallurgy", "abbreviation": "EMM", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
        {"subject_code": "ME3393", "subject_name": "Manufacturing Processes", "abbreviation": "MP", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
        {"subject_code": "ME3381", "subject_name": "Fluid Mechanics and Machinery Laboratory", "abbreviation": "FMM LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "ME3382", "subject_name": "Manufacturing Technology Laboratory", "abbreviation": "MT LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ],

    # ── CIVIL ──
    ("B.E.", "CIVIL", "Semester 1"): SEM1_COMMON,
    ("B.E.", "CIVIL", "Semester 2"): SEM2_NON_CIRCUIT,
    ("B.E.", "CIVIL", "Semester 3"): [
        {"subject_code": "MA3351", "subject_name": "Transforms and Partial Differential Equations", "abbreviation": "TPDE", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "CE3301", "subject_name": "Fluid Mechanics", "abbreviation": "FM", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "CE3302", "subject_name": "Construction Materials and Technology", "abbreviation": "CMT", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
        {"subject_code": "CE3303", "subject_name": "Water Supply and Wastewater Engineering", "abbreviation": "WSWE", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "CE3351", "subject_name": "Surveying and Levelling", "abbreviation": "SURVEY", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
        {"subject_code": "CE3361", "subject_name": "Surveying and Levelling Laboratory", "abbreviation": "SURV LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "CE3362", "subject_name": "Water and Wastewater Analysis Laboratory", "abbreviation": "WW LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ],

    # ── BME ──
    ("B.E.", "BME", "Semester 3"): [
        {"subject_code": "MA3355", "subject_name": "Random Processes and Linear Algebra", "abbreviation": "RPLA", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "BM3351", "subject_name": "Anatomy and Human Physiology", "abbreviation": "AHP", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "BM3352", "subject_name": "Sensors and Measurements", "abbreviation": "SM", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
        {"subject_code": "EC3353", "subject_name": "Electronic Devices and Circuits", "abbreviation": "EDC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "BM3361", "subject_name": "Human Physiology Laboratory", "abbreviation": "HP LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "EC3361", "subject_name": "Electronic Devices and Circuits Laboratory", "abbreviation": "EDC LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ],

    # ── CSBS ──
    ("B.Tech.", "CSBS", "Semester 3"): [
        {"subject_code": "MA3354", "subject_name": "Discrete Mathematics and Graph Theory", "abbreviation": "DMGT", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "CB3301", "subject_name": "Data Structures and Algorithms with Business Cases", "abbreviation": "DSA-BC", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "CB3302", "subject_name": "Computational Statistics", "abbreviation": "CS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "CB3303", "subject_name": "Fundamentals of Economics and Financial Accounting", "abbreviation": "FEFA", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
        {"subject_code": "CB3381", "subject_name": "Data Structures Laboratory", "abbreviation": "DS LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "CB3382", "subject_name": "Statistical Software Laboratory (R / Python)", "abbreviation": "STAT LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ],

    # ── CYBER ──
    ("B.E.", "CYBER", "Semester 3"): [
        {"subject_code": "MA3354", "subject_name": "Discrete Mathematics and Number Theory", "abbreviation": "DMNT", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "CS3351", "subject_name": "Digital Principles and Computer Organization", "abbreviation": "DPCO", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "CY3301", "subject_name": "Data Structures and Secure Coding", "abbreviation": "DS-SEC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "CY3302", "subject_name": "Foundations of Cyber Security", "abbreviation": "FCS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "CY3381", "subject_name": "Data Structures & Secure Coding Lab", "abbreviation": "SEC LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "CY3382", "subject_name": "Cyber Defense and Linux System Lab", "abbreviation": "LINUX LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ]
}


# ══════════════════════════════════════════════════════════════════════════════
# REGULATION 2023 (R2023) CURRICULA - AUTONOMOUS & AICTE REVISED
# ══════════════════════════════════════════════════════════════════════════════

R2023_DATA = {
    # ── CSE ──
    ("B.E.", "CSE", "Semester 1"): SEM1_COMMON,
    ("B.E.", "CSE", "Semester 2"): SEM2_CIRCUIT,
    ("B.E.", "CSE", "Semester 3"): [
        {"subject_code": "23CS301", "subject_name": "Discrete Mathematical Structures", "abbreviation": "DMS", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "23CS302", "subject_name": "Data Structures using C++ and STL", "abbreviation": "DS-STL", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "23CS303", "subject_name": "Computer Architecture and RISC-V", "abbreviation": "RISC-V", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "23CS304", "subject_name": "Python for Data Science & AI", "abbreviation": "PY-AI", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
        {"subject_code": "23CS305", "subject_name": "Database Management & NoSQL Systems", "abbreviation": "NOSQL", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "23CS311", "subject_name": "Data Structures & STL Laboratory", "abbreviation": "STL LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "23CS312", "subject_name": "Database & NoSQL Laboratory", "abbreviation": "NOSQL LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "23PD301", "subject_name": "Critical Thinking & Design Innovation", "abbreviation": "DES INN", "periods_per_week": 2, "is_lab": True, "lab_duration": 2, "difficulty_level": 2, "credits": 1}
    ],
    ("B.E.", "CSE", "Semester 4"): [
        {"subject_code": "23CS401", "subject_name": "Design & Analysis of Algorithms", "abbreviation": "DAA", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "23CS402", "subject_name": "Operating Systems & Linux Internals", "abbreviation": "OS-LINUX", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "23CS403", "subject_name": "Applied Machine Learning", "abbreviation": "AML", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "23CS404", "subject_name": "Full Stack Web Development (React & Node)", "abbreviation": "FULLSTACK", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
        {"subject_code": "23CS411", "subject_name": "Algorithms & Problem Solving Lab", "abbreviation": "ALG LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "23CS412", "subject_name": "Full Stack Web Development Lab", "abbreviation": "WEB LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ],

    # ── IT ──
    ("B.Tech.", "IT", "Semester 3"): [
        {"subject_code": "23IT301", "subject_name": "Discrete Mathematics", "abbreviation": "DM", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "23IT302", "subject_name": "Advanced Data Structures and Algorithms", "abbreviation": "ADSA", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "23IT303", "subject_name": "Modern Web Technologies and Cloud Services", "abbreviation": "WEB-CLOUD", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "23IT304", "subject_name": "Database Systems and Warehousing", "abbreviation": "DSW", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "23IT311", "subject_name": "Advanced Data Structures Laboratory", "abbreviation": "ADSA LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "23IT312", "subject_name": "Cloud and Web Technologies Lab", "abbreviation": "CLOUD LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ],

    # ── AI & DS ──
    ("B.Tech.", "AIDS", "Semester 3"): [
        {"subject_code": "23AD301", "subject_name": "Probability, Statistics and Linear Algebra", "abbreviation": "PSLA", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "23AD302", "subject_name": "Data Structures & Computational Complexity", "abbreviation": "DSCC", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "23AD303", "subject_name": "Artificial Intelligence Concepts & Search", "abbreviation": "AI-SRCH", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "23AD304", "subject_name": "Relational and Vector Databases", "abbreviation": "VEC-DB", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "23AD311", "subject_name": "AI Implementation Laboratory", "abbreviation": "AI LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "23AD312", "subject_name": "Vector Database & Data Analysis Lab", "abbreviation": "VDB LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ],

    # ── ECE ──
    ("B.E.", "ECE", "Semester 3"): [
        {"subject_code": "23EC301", "subject_name": "Applied Linear Algebra and Complex Analysis", "abbreviation": "LACA", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "23EC302", "subject_name": "Circuit Analysis & Simulation", "abbreviation": "CAS", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "23EC303", "subject_name": "Digital Logic and Verilog HDL", "abbreviation": "VERILOG", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "23EC304", "subject_name": "Semiconductor Devices & Nanotechnology", "abbreviation": "SEMI", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "23EC311", "subject_name": "Circuits & Simulation Laboratory", "abbreviation": "SIM LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "23EC312", "subject_name": "Verilog HDL & FPGA Laboratory", "abbreviation": "FPGA LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ],

    # ── MECH ──
    ("B.E.", "MECH", "Semester 3"): [
        {"subject_code": "23ME301", "subject_name": "Partial Differential Equations & Calculus of Variations", "abbreviation": "PDE", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "23ME302", "subject_name": "Thermal Engineering & Heat Power", "abbreviation": "THERM", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "23ME303", "subject_name": "Computer Aided Design & Solid Modeling", "abbreviation": "CAD", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "23ME304", "subject_name": "Mechanics of Materials", "abbreviation": "MOM", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "23ME311", "subject_name": "CAD / CAM 3D Modeling Laboratory", "abbreviation": "CAD LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "23ME312", "subject_name": "Thermal & Energy Systems Lab", "abbreviation": "THERM LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ],

    # ── EEE ──
    ("B.E.", "EEE", "Semester 3"): [
        {"subject_code": "23EE301", "subject_name": "Engineering Mathematics III", "abbreviation": "M-3", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "23EE302", "subject_name": "Electric Circuit Theory and Network Synthesis", "abbreviation": "ECT", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "23EE303", "subject_name": "DC Machines and Transformers", "abbreviation": "DCMT", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "23EE304", "subject_name": "Analog & Digital Electronics", "abbreviation": "ADE", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "23EE311", "subject_name": "Electrical Machines Laboratory", "abbreviation": "EM LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "23EE312", "subject_name": "Electronics & Circuit Simulation Lab", "abbreviation": "ELEC LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ],

    # ── CIVIL ──
    ("B.E.", "CIVIL", "Semester 3"): [
        {"subject_code": "23CE301", "subject_name": "Differential Equations and Transform Techniques", "abbreviation": "DTT", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "23CE302", "subject_name": "Strength of Materials and Solid Mechanics", "abbreviation": "SOM", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "23CE303", "subject_name": "Modern Surveying with GIS and GPS", "abbreviation": "GIS-GPS", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "23CE304", "subject_name": "Fluid Mechanics and Hydraulic Machinery", "abbreviation": "FMHM", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "23CE311", "subject_name": "Strength of Materials Laboratory", "abbreviation": "SOM LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "23CE312", "subject_name": "GIS and Modern Surveying Laboratory", "abbreviation": "GIS LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ]
}


# ══════════════════════════════════════════════════════════════════════════════
# REGULATION 2025 (R2025) CURRICULA - NEXTGEN AI & INDUSTRY 5.0
# ══════════════════════════════════════════════════════════════════════════════

R2025_DATA = {
    # ── CSE ──
    ("B.E.", "CSE", "Semester 1"): SEM1_COMMON,
    ("B.E.", "CSE", "Semester 2"): SEM2_CIRCUIT,
    ("B.E.", "CSE", "Semester 3"): [
        {"subject_code": "25CS301", "subject_name": "Discrete Mathematics & Graph Analytics", "abbreviation": "DMGA", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "25CS302", "subject_name": "Modern Data Structures in Rust & C++", "abbreviation": "DS-RUST", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "25CS303", "subject_name": "Computer Systems & Heterogeneous Computing", "abbreviation": "CS-HET", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "25CS304", "subject_name": "Generative AI Foundations & Prompt Engineering", "abbreviation": "GEN-AI", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "25CS305", "subject_name": "Cloud-Native Databases & Distributed Storage", "abbreviation": "CLOUD-DB", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
        {"subject_code": "25CS311", "subject_name": "High-Performance Data Structures Laboratory", "abbreviation": "HPDS LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "25CS312", "subject_name": "Generative AI & LLM Systems Laboratory", "abbreviation": "LLM LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "25PD301", "subject_name": "AI Product Development & Agile Studio", "abbreviation": "AI STUDIO", "periods_per_week": 2, "is_lab": True, "lab_duration": 2, "difficulty_level": 2, "credits": 1}
    ],
    ("B.E.", "CSE", "Semester 4"): [
        {"subject_code": "25CS401", "subject_name": "Quantum Computing & Advanced Algorithms", "abbreviation": "QUANTUM", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "25CS402", "subject_name": "Microservices & Distributed Systems", "abbreviation": "MICROSERV", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "25CS403", "subject_name": "Deep Learning & Transformer Architectures", "abbreviation": "DL-TRANS", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "25CS404", "subject_name": "Cyber Threat Intelligence & Zero Trust", "abbreviation": "ZERO-TRST", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "25CS411", "subject_name": "Deep Learning & Vision Laboratory", "abbreviation": "DL LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "25CS412", "subject_name": "Cloud DevOps & Microservices Laboratory", "abbreviation": "DEVOPS LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ],

    # ── AI & DS ──
    ("B.Tech.", "AIDS", "Semester 3"): [
        {"subject_code": "25AD301", "subject_name": "Mathematical Foundations of Deep Learning", "abbreviation": "MFDL", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "25AD302", "subject_name": "Scalable Machine Learning on Big Data", "abbreviation": "SML", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "25AD303", "subject_name": "Large Language Models & Agentic AI", "abbreviation": "LLM-AGNT", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "25AD304", "subject_name": "Vector Databases & Semantic Search", "abbreviation": "SEM-SRCH", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
        {"subject_code": "25AD311", "subject_name": "Agentic AI & LangChain Laboratory", "abbreviation": "AGENT LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "25AD312", "subject_name": "Scalable ML Pipeline Laboratory", "abbreviation": "MLPIPE LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ],

    # ── ECE ──
    ("B.E.", "ECE", "Semester 3"): [
        {"subject_code": "25EC301", "subject_name": "Applied Mathematics for 6G and Beyond", "abbreviation": "MATH-6G", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "25EC302", "subject_name": "Edge AI & Embedded Neural Processing", "abbreviation": "EDGE-AI", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "25EC303", "subject_name": "VLSI Design with Chiplet & RISC-V", "abbreviation": "VLSI-CHIP", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "25EC304", "subject_name": "RF Systems and Terahertz Communications", "abbreviation": "RF-THZ", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
        {"subject_code": "25EC311", "subject_name": "Edge AI & TinyML Laboratory", "abbreviation": "TINYML LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "25EC312", "subject_name": "VLSI Design & Electronic EDA Lab", "abbreviation": "EDA LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ],

    # ── MECH ──
    ("B.E.", "MECH", "Semester 3"): [
        {"subject_code": "25ME301", "subject_name": "Engineering Mathematics for Autonomous Systems", "abbreviation": "EM-AS", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
        {"subject_code": "25ME302", "subject_name": "Electric Vehicle Powertrain & Battery Tech", "abbreviation": "EV-TECH", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "25ME303", "subject_name": "Additive Manufacturing and 3D Printing", "abbreviation": "AM-3D", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
        {"subject_code": "25ME304", "subject_name": "Robotics Kinematics and Cobots", "abbreviation": "ROBOTICS", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
        {"subject_code": "25ME311", "subject_name": "Robotics & Automation Laboratory", "abbreviation": "ROBOT LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
        {"subject_code": "25ME312", "subject_name": "EV Systems & Battery Testing Lab", "abbreviation": "EV LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
    ]
}


def get_all_curricula_index() -> Dict[str, Any]:
    """Returns the full searchable tree of available regulations, degrees, departments, and semesters."""
    tree = {
        "R2021": {"label": "Anna University R2021 (CBCS Affiliated)", "degrees": {}},
        "R2023": {"label": "Anna University R2023 (Autonomous / AICTE)", "degrees": {}},
        "R2025": {"label": "Anna University R2025 (NextGen AI & Industry 5.0)", "degrees": {}},
    }

    # Populate R2021
    for (deg, dept, sem), subs in R2021_DATA.items():
        tree["R2021"]["degrees"].setdefault(deg, {}).setdefault(dept, []).append(sem)

    # Populate R2023
    for (deg, dept, sem), subs in R2023_DATA.items():
        tree["R2023"]["degrees"].setdefault(deg, {}).setdefault(dept, []).append(sem)

    # Populate R2025
    for (deg, dept, sem), subs in R2025_DATA.items():
        tree["R2025"]["degrees"].setdefault(deg, {}).setdefault(dept, []).append(sem)

    return tree


def get_curriculum(regulation: str, degree: str, department: str, semester: str) -> Optional[Dict[str, Any]]:
    """Retrieve specific curriculum subjects for given parameters."""
    reg = regulation.upper().strip()
    data_source = None
    if "2025" in reg:
        data_source = R2025_DATA
        reg_title = "Anna University R2025"
    elif "2023" in reg:
        data_source = R2023_DATA
        reg_title = "Anna University R2023"
    else:
        data_source = R2021_DATA
        reg_title = "Anna University R2021"

    key = (degree, department, semester)
    if key in data_source:
        subjects = [dict(s) for s in data_source[key]]
        for s in subjects:
            s["department"] = department
        
        # Build default section class name
        sem_num = semester.split()[-1] if " " in semester else semester
        class_name = f"{degree} {department} - Sem {sem_num} (Sec A)"
        
        return {
            "success": True,
            "regulation": reg_title,
            "degree": degree,
            "department": department,
            "semester": semester,
            "class_name": class_name,
            "subjects": subjects
        }
    
    # Check fallback (e.g. B.Tech vs B.E. or common Sem 1 / 2)
    for (d, dept, sem), subs in data_source.items():
        if dept == department and sem == semester:
            subjects = [dict(s) for s in subs]
            for s in subjects:
                s["department"] = department
            sem_num = semester.split()[-1] if " " in semester else semester
            return {
                "success": True,
                "regulation": reg_title,
                "degree": d,
                "department": department,
                "semester": semester,
                "class_name": f"{d} {department} - Sem {sem_num} (Sec A)",
                "subjects": subjects
            }

    return None
