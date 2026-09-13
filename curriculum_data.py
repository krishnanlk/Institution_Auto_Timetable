"""
curriculum_data.py - Inbuilt Anna University Curricula Repository
Regulations: R2021 (CBCS Affiliated), R2023 (Autonomous / AICTE), R2025 (NextGen AI & Industry 5.0)
Degrees: B.E., B.Tech.
Departments: CSE, IT, AIDS, ECE, EEE, MECH, CIVIL, BME, CSBS, CYBER
Semesters: Semester 1 through Semester 8
"""

import json, re
from typing import Dict, List, Any, Optional

# ══════════════════════════════════════════════════════════════════════════════
# COMMON 1ST YEAR CURRICULA (SEMESTER 1 & 2)
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
# REGULATION 2021 (R2021) COMPLETE 8 SEMESTERS
# ══════════════════════════════════════════════════════════════════════════════

R2021_DATA: Dict[tuple, List[Dict[str, Any]]] = {}

# 1. CSE (B.E.)
R2021_DATA[("B.E.", "CSE", "Semester 1")] = SEM1_COMMON
R2021_DATA[("B.E.", "CSE", "Semester 2")] = SEM2_CIRCUIT
R2021_DATA[("B.E.", "CSE", "Semester 3")] = [
    {"subject_code": "MA3354", "subject_name": "Discrete Mathematics", "abbreviation": "DM", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "CS3351", "subject_name": "Digital Principles and Computer Organization", "abbreviation": "DPCO", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "CS3352", "subject_name": "Foundations of Data Science", "abbreviation": "FDS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "CS3301", "subject_name": "Data Structures", "abbreviation": "DS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "CS3391", "subject_name": "Object Oriented Programming", "abbreviation": "OOP", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "CS3381", "subject_name": "Data Structures Laboratory", "abbreviation": "DS LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "CS3361", "subject_name": "Object Oriented Programming Laboratory", "abbreviation": "OOP LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "GE3361", "subject_name": "Professional Development", "abbreviation": "PD LAB", "periods_per_week": 2, "is_lab": True, "lab_duration": 2, "difficulty_level": 2, "credits": 1}
]
R2021_DATA[("B.E.", "CSE", "Semester 4")] = [
    {"subject_code": "CS3452", "subject_name": "Theory of Computation", "abbreviation": "TOC", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "CS3491", "subject_name": "Artificial Intelligence and Machine Learning", "abbreviation": "AIML", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "CS3492", "subject_name": "Database Management Systems", "abbreviation": "DBMS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "CS3401", "subject_name": "Algorithms", "abbreviation": "DAA", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "CS3451", "subject_name": "Introduction to Operating Systems", "abbreviation": "OS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "GE3451", "subject_name": "Environmental Sciences and Sustainability", "abbreviation": "EVS", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
    {"subject_code": "CS3461", "subject_name": "Database Management Systems Laboratory", "abbreviation": "DBMS LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "CS3481", "subject_name": "Operating Systems Laboratory", "abbreviation": "OS LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "CSE", "Semester 5")] = [
    {"subject_code": "CS3591", "subject_name": "Computer Networks", "abbreviation": "CN", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "CS3501", "subject_name": "Compiler Design", "abbreviation": "CD", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "CB3491", "subject_name": "Cryptography and Cyber Security", "abbreviation": "CCS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "CS3551", "subject_name": "Distributed Computing", "abbreviation": "DC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PE3501", "subject_name": "Professional Elective I (Cloud Computing)", "abbreviation": "PE-1", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "MC3501", "subject_name": "Mandatory Course: Constitution of India", "abbreviation": "COI", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 0},
    {"subject_code": "CS3561", "subject_name": "Compiler Design Laboratory", "abbreviation": "CD LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "CS3562", "subject_name": "Networks and Security Laboratory", "abbreviation": "NET LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "CSE", "Semester 6")] = [
    {"subject_code": "CCS334", "subject_name": "Big Data Analytics", "abbreviation": "BDA", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "CS3691", "subject_name": "Embedded Systems and IoT", "abbreviation": "IOT", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "PE3602", "subject_name": "Professional Elective II (Deep Learning)", "abbreviation": "PE-2", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PE3603", "subject_name": "Professional Elective III (Software Testing)", "abbreviation": "PE-3", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "OE3601", "subject_name": "Open Elective I", "abbreviation": "OE-1", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "CS3661", "subject_name": "Embedded Systems and IoT Laboratory", "abbreviation": "IOT LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "CS3681", "subject_name": "Mini Project / Socially Relevant Project", "abbreviation": "MINI PROJ", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "CSE", "Semester 7")] = [
    {"subject_code": "GE3791", "subject_name": "Human Values and Ethics", "abbreviation": "HVE", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
    {"subject_code": "CS3701", "subject_name": "Software Project Management", "abbreviation": "SPM", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "PE3704", "subject_name": "Professional Elective IV (Block Chain Technologies)", "abbreviation": "PE-4", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PE3705", "subject_name": "Professional Elective V (Quantum Computing)", "abbreviation": "PE-5", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "OE3702", "subject_name": "Open Elective II", "abbreviation": "OE-2", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "CS3781", "subject_name": "Project Work Phase I", "abbreviation": "PROJ-1", "periods_per_week": 4, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 2}
]
R2021_DATA[("B.E.", "CSE", "Semester 8")] = [
    {"subject_code": "CS3811", "subject_name": "Project Work Phase II / Industrial Internship", "abbreviation": "PROJ-2", "periods_per_week": 12, "is_lab": True, "lab_duration": 4, "difficulty_level": 4, "credits": 10}
]

# 2. IT (B.Tech.)
R2021_DATA[("B.Tech.", "IT", "Semester 1")] = SEM1_COMMON
R2021_DATA[("B.Tech.", "IT", "Semester 2")] = SEM2_CIRCUIT
R2021_DATA[("B.Tech.", "IT", "Semester 3")] = [
    {"subject_code": "MA3354", "subject_name": "Discrete Mathematics", "abbreviation": "DM", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "CS3351", "subject_name": "Digital Principles and Computer Organization", "abbreviation": "DPCO", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "IT3301", "subject_name": "Data Structures and Algorithms", "abbreviation": "DSA", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "IT3351", "subject_name": "Object Oriented Programming in Java", "abbreviation": "JAVA", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "IT3352", "subject_name": "Web Technology", "abbreviation": "WT", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "IT3381", "subject_name": "Data Structures Laboratory", "abbreviation": "DS LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "IT3361", "subject_name": "Java Programming Laboratory", "abbreviation": "JAVA LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "GE3361", "subject_name": "Professional Development", "abbreviation": "PD LAB", "periods_per_week": 2, "is_lab": True, "lab_duration": 2, "difficulty_level": 2, "credits": 1}
]
R2021_DATA[("B.Tech.", "IT", "Semester 4")] = [
    {"subject_code": "CS3491", "subject_name": "Artificial Intelligence and Machine Learning", "abbreviation": "AIML", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "CS3492", "subject_name": "Database Management Systems", "abbreviation": "DBMS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "IT3401", "subject_name": "Web Essentials", "abbreviation": "WE", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "CS3451", "subject_name": "Introduction to Operating Systems", "abbreviation": "OS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "GE3451", "subject_name": "Environmental Sciences and Sustainability", "abbreviation": "EVS", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
    {"subject_code": "CS3461", "subject_name": "Database Management Systems Laboratory", "abbreviation": "DBMS LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "IT3481", "subject_name": "Web Application Development Laboratory", "abbreviation": "WEB LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.Tech.", "IT", "Semester 5")] = [
    {"subject_code": "IT3501", "subject_name": "Computer Networks and Security", "abbreviation": "NET", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "IT3551", "subject_name": "Full Stack Web Development", "abbreviation": "FSW", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "CB3491", "subject_name": "Cryptography and Cyber Security", "abbreviation": "CCS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "IT3502", "subject_name": "Data Mining and Warehousing", "abbreviation": "DMW", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PEIT01", "subject_name": "Professional Elective I (Cloud & DevOps)", "abbreviation": "PE-1", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "MC3501", "subject_name": "Constitution of India", "abbreviation": "COI", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 0},
    {"subject_code": "IT3561", "subject_name": "Full Stack Web Development Laboratory", "abbreviation": "FSW LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "IT3562", "subject_name": "Networks and Security Laboratory", "abbreviation": "NET LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.Tech.", "IT", "Semester 6")] = [
    {"subject_code": "IT3601", "subject_name": "Mobile Computing & Applications", "abbreviation": "MC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "CS3691", "subject_name": "Embedded Systems and IoT", "abbreviation": "IOT", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "PEIT02", "subject_name": "Professional Elective II (Information Security)", "abbreviation": "PE-2", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PEIT03", "subject_name": "Professional Elective III (Cloud Architecture)", "abbreviation": "PE-3", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "OEIT01", "subject_name": "Open Elective I", "abbreviation": "OE-1", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "IT3661", "subject_name": "Mobile Application Development Laboratory", "abbreviation": "MAD LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "IT3681", "subject_name": "Mini Project", "abbreviation": "MINI PROJ", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.Tech.", "IT", "Semester 7")] = [
    {"subject_code": "GE3791", "subject_name": "Human Values and Ethics", "abbreviation": "HVE", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
    {"subject_code": "IT3701", "subject_name": "Cloud Computing and Big Data Analytics", "abbreviation": "CC-BDA", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "PEIT04", "subject_name": "Professional Elective IV (Software QA)", "abbreviation": "PE-4", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "PEIT05", "subject_name": "Professional Elective V (NLP)", "abbreviation": "PE-5", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "OEIT02", "subject_name": "Open Elective II", "abbreviation": "OE-2", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "IT3781", "subject_name": "Project Work Phase I", "abbreviation": "PROJ-1", "periods_per_week": 4, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 2}
]
R2021_DATA[("B.Tech.", "IT", "Semester 8")] = [
    {"subject_code": "IT3881", "subject_name": "Project Work Phase II / Industrial Internship", "abbreviation": "PROJ-2", "periods_per_week": 12, "is_lab": True, "lab_duration": 4, "difficulty_level": 4, "credits": 10}
]

# 3. AIDS (B.Tech.)
R2021_DATA[("B.Tech.", "AIDS", "Semester 1")] = SEM1_COMMON
R2021_DATA[("B.Tech.", "AIDS", "Semester 2")] = SEM2_CIRCUIT
R2021_DATA[("B.Tech.", "AIDS", "Semester 3")] = [
    {"subject_code": "MA3354", "subject_name": "Discrete Mathematics", "abbreviation": "DM", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "AD3351", "subject_name": "Design and Analysis of Algorithms", "abbreviation": "DAA", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "CS3352", "subject_name": "Foundations of Data Science", "abbreviation": "FDS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "AD3301", "subject_name": "Data Structures and Modern Tools", "abbreviation": "DS-MT", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "AD3391", "subject_name": "Database Design and Management", "abbreviation": "DDM", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "AD3381", "subject_name": "Data Structures and Algorithm Laboratory", "abbreviation": "DSA LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "AD3361", "subject_name": "Data Science Tools Laboratory", "abbreviation": "DS TOOLS", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "GE3361", "subject_name": "Professional Development", "abbreviation": "PD LAB", "periods_per_week": 2, "is_lab": True, "lab_duration": 2, "difficulty_level": 2, "credits": 1}
]
R2021_DATA[("B.Tech.", "AIDS", "Semester 4")] = [
    {"subject_code": "MA3452", "subject_name": "Linear Algebra and Statistics for Data Science", "abbreviation": "LAS", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "AD3491", "subject_name": "Fundamentals of Machine Learning", "abbreviation": "FML", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "AD3401", "subject_name": "Data Analytics and Visualization", "abbreviation": "DAV", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "CS3451", "subject_name": "Operating Systems & Virtualization", "abbreviation": "OS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "GE3451", "subject_name": "Environmental Sciences and Sustainability", "abbreviation": "EVS", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
    {"subject_code": "AD3461", "subject_name": "Machine Learning Laboratory", "abbreviation": "ML LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "AD3481", "subject_name": "Data Analytics Laboratory", "abbreviation": "DA LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.Tech.", "AIDS", "Semester 5")] = [
    {"subject_code": "AD3501", "subject_name": "Deep Learning Techniques", "abbreviation": "DL", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "AD3551", "subject_name": "Natural Language Processing", "abbreviation": "NLP", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "AD3502", "subject_name": "Big Data Technologies", "abbreviation": "BDT", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PEAD01", "subject_name": "Professional Elective I (Computer Vision)", "abbreviation": "CV", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PEAD02", "subject_name": "Professional Elective II (AI in Robotics)", "abbreviation": "ROBO", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "MC3501", "subject_name": "Constitution of India", "abbreviation": "COI", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 0},
    {"subject_code": "AD3561", "subject_name": "Deep Learning Laboratory", "abbreviation": "DL LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "AD3562", "subject_name": "Natural Language Processing Laboratory", "abbreviation": "NLP LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.Tech.", "AIDS", "Semester 6")] = [
    {"subject_code": "AD3601", "subject_name": "Reinforcement Learning", "abbreviation": "RL", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "AD3651", "subject_name": "Generative AI & Prompt Engineering", "abbreviation": "GEN-AI", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PEAD03", "subject_name": "Professional Elective III (MLOps)", "abbreviation": "MLOPS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PEAD04", "subject_name": "Professional Elective IV (Semantic Web)", "abbreviation": "SEM-WEB", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "OEAD01", "subject_name": "Open Elective I", "abbreviation": "OE-1", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "AD3661", "subject_name": "Generative AI & LLM Systems Laboratory", "abbreviation": "GENAI LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "AD3681", "subject_name": "Mini Project", "abbreviation": "MINI PROJ", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.Tech.", "AIDS", "Semester 7")] = [
    {"subject_code": "GE3791", "subject_name": "Human Values and Ethics", "abbreviation": "HVE", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
    {"subject_code": "AD3701", "subject_name": "AI Ethics, Governance and Trust", "abbreviation": "AI-ETHICS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "PEAD05", "subject_name": "Professional Elective V (Autonomous Systems)", "abbreviation": "AUTO", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PEAD06", "subject_name": "Professional Elective VI (Healthcare AI)", "abbreviation": "HEALTH-AI", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "OEAD02", "subject_name": "Open Elective II", "abbreviation": "OE-2", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "AD3781", "subject_name": "Project Work Phase I", "abbreviation": "PROJ-1", "periods_per_week": 4, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 2}
]
R2021_DATA[("B.Tech.", "AIDS", "Semester 8")] = [
    {"subject_code": "AD3881", "subject_name": "Project Work Phase II / Industrial Internship", "abbreviation": "PROJ-2", "periods_per_week": 12, "is_lab": True, "lab_duration": 4, "difficulty_level": 4, "credits": 10}
]

# 4. ECE (B.E.)
R2021_DATA[("B.E.", "ECE", "Semester 1")] = SEM1_COMMON
R2021_DATA[("B.E.", "ECE", "Semester 2")] = SEM2_CIRCUIT
R2021_DATA[("B.E.", "ECE", "Semester 3")] = [
    {"subject_code": "MA3355", "subject_name": "Random Processes and Linear Algebra", "abbreviation": "RPLA", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "EC3354", "subject_name": "Signals and Systems", "abbreviation": "SS", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "EC3353", "subject_name": "Electronic Devices and Circuits", "abbreviation": "EDC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "EC3351", "subject_name": "Control Systems", "abbreviation": "CS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "EC3352", "subject_name": "Digital Systems Design", "abbreviation": "DSD", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "EC3361", "subject_name": "Electronic Devices and Circuits Laboratory", "abbreviation": "EDC LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "EC3362", "subject_name": "Digital Systems Design Laboratory", "abbreviation": "DSD LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "ECE", "Semester 4")] = [
    {"subject_code": "EC3452", "subject_name": "Electromagnetic Fields", "abbreviation": "EMF", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "EC3401", "subject_name": "Networks and Security", "abbreviation": "NET", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "EC3451", "subject_name": "Linear Integrated Circuits", "abbreviation": "LIC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "EC3492", "subject_name": "Digital Signal Processing", "abbreviation": "DSP", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "EC3491", "subject_name": "Communication Systems", "abbreviation": "COMM", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "GE3451", "subject_name": "Environmental Sciences and Sustainability", "abbreviation": "EVS", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
    {"subject_code": "EC3461", "subject_name": "Communication Systems Laboratory", "abbreviation": "COMM LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "EC3462", "subject_name": "Linear Integrated Circuits Laboratory", "abbreviation": "LIC LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "ECE", "Semester 5")] = [
    {"subject_code": "EC3501", "subject_name": "Wireless Communication", "abbreviation": "WIRELESS", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "EC3551", "subject_name": "VLSI Design", "abbreviation": "VLSI", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "EC3502", "subject_name": "Transmission Lines and RF Systems", "abbreviation": "TLRF", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "PEEC01", "subject_name": "Professional Elective I (Embedded Systems)", "abbreviation": "EMBED", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "PEEC02", "subject_name": "Professional Elective II (Optical Communication)", "abbreviation": "OPTIC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "MC3501", "subject_name": "Constitution of India", "abbreviation": "COI", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 0},
    {"subject_code": "EC3561", "subject_name": "VLSI Design Laboratory", "abbreviation": "VLSI LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "EC3562", "subject_name": "Digital Signal Processing Laboratory", "abbreviation": "DSP LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "ECE", "Semester 6")] = [
    {"subject_code": "EC3601", "subject_name": "Antennas and Microwave Engineering", "abbreviation": "ANTENNA", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "EC3651", "subject_name": "Medical Electronics", "abbreviation": "MED", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "PEEC03", "subject_name": "Professional Elective III (Satellite Communication)", "abbreviation": "SAT", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "PEEC04", "subject_name": "Professional Elective IV (Radar & Navigational Aids)", "abbreviation": "RADAR", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "OEEC01", "subject_name": "Open Elective I", "abbreviation": "OE-1", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "EC3661", "subject_name": "Microwave and Optical Laboratory", "abbreviation": "MICROWV", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "EC3681", "subject_name": "Mini Project", "abbreviation": "MINI PROJ", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "ECE", "Semester 7")] = [
    {"subject_code": "GE3791", "subject_name": "Human Values and Ethics", "abbreviation": "HVE", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
    {"subject_code": "EC3701", "subject_name": "Advanced Microprocessors & Microcontrollers", "abbreviation": "MPMC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PEEC05", "subject_name": "Professional Elective V (Cognitive Radio)", "abbreviation": "COGNITIVE", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PEEC06", "subject_name": "Professional Elective VI (Nano Electronics)", "abbreviation": "NANO", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "OEEC02", "subject_name": "Open Elective II", "abbreviation": "OE-2", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "EC3781", "subject_name": "Project Work Phase I", "abbreviation": "PROJ-1", "periods_per_week": 4, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 2}
]
R2021_DATA[("B.E.", "ECE", "Semester 8")] = [
    {"subject_code": "EC3881", "subject_name": "Project Work Phase II / Industrial Internship", "abbreviation": "PROJ-2", "periods_per_week": 12, "is_lab": True, "lab_duration": 4, "difficulty_level": 4, "credits": 10}
]

# 5. EEE (B.E.)
R2021_DATA[("B.E.", "EEE", "Semester 1")] = SEM1_COMMON
R2021_DATA[("B.E.", "EEE", "Semester 2")] = SEM2_CIRCUIT
R2021_DATA[("B.E.", "EEE", "Semester 3")] = [
    {"subject_code": "MA3353", "subject_name": "Linear Algebra and Numerical Methods", "abbreviation": "LANM", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "EE3301", "subject_name": "Electromagnetic Fields", "abbreviation": "EMF", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "EE3302", "subject_name": "Digital Logic Circuits", "abbreviation": "DLC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "EE3303", "subject_name": "Electrical Machines - I", "abbreviation": "EM-1", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "EC3301", "subject_name": "Electron Devices and Circuits", "abbreviation": "EDC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "EE3311", "subject_name": "Electrical Machines Laboratory - I", "abbreviation": "EM1 LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "EC3311", "subject_name": "Electronic Devices and Circuits Laboratory", "abbreviation": "EDC LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "EEE", "Semester 4")] = [
    {"subject_code": "EE3401", "subject_name": "Electrical Machines - II", "abbreviation": "EM-2", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "EE3402", "subject_name": "Transmission and Distribution", "abbreviation": "TD", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "EE3403", "subject_name": "Linear Integrated Circuits and Applications", "abbreviation": "LICA", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "EE3404", "subject_name": "Measurements and Instrumentation", "abbreviation": "MI", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "EE3405", "subject_name": "Control Systems", "abbreviation": "CS", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "GE3451", "subject_name": "Environmental Sciences and Sustainability", "abbreviation": "EVS", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
    {"subject_code": "EE3411", "subject_name": "Electrical Machines Laboratory - II", "abbreviation": "EM2 LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "EE3412", "subject_name": "Control & Instrumentation Laboratory", "abbreviation": "CI LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "EEE", "Semester 5")] = [
    {"subject_code": "EE3501", "subject_name": "Power System Analysis", "abbreviation": "PSA", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "EE3502", "subject_name": "Power Electronics", "abbreviation": "PE", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "EE3503", "subject_name": "Microprocessors and Microcontrollers", "abbreviation": "MPMC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PEEE01", "subject_name": "Professional Elective I (Renewable Energy)", "abbreviation": "RE", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "PEEE02", "subject_name": "Professional Elective II (Smart Grid)", "abbreviation": "SMART", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "MC3501", "subject_name": "Constitution of India", "abbreviation": "COI", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 0},
    {"subject_code": "EE3511", "subject_name": "Power Electronics Laboratory", "abbreviation": "PE LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "EE3512", "subject_name": "Microprocessors & Controllers Lab", "abbreviation": "MPMC LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "EEE", "Semester 6")] = [
    {"subject_code": "EE3601", "subject_name": "Power System Operation and Control", "abbreviation": "PSOC", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "EE3602", "subject_name": "Electric Drives and Control", "abbreviation": "EDC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PEEE03", "subject_name": "Professional Elective III (High Voltage Engg)", "abbreviation": "HVE", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PEEE04", "subject_name": "Professional Elective IV (Electric Vehicles)", "abbreviation": "EV", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "OEEE01", "subject_name": "Open Elective I", "abbreviation": "OE-1", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "EE3611", "subject_name": "Power System Simulation Laboratory", "abbreviation": "PSS LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "EE3681", "subject_name": "Mini Project", "abbreviation": "MINI PROJ", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "EEE", "Semester 7")] = [
    {"subject_code": "GE3791", "subject_name": "Human Values and Ethics", "abbreviation": "HVE", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
    {"subject_code": "EE3701", "subject_name": "Protection and Switchgear", "abbreviation": "PS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PEEE05", "subject_name": "Professional Elective V (Energy Storage Tech)", "abbreviation": "STORAGE", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PEEE06", "subject_name": "Professional Elective VI (Power Quality)", "abbreviation": "PQ", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "OEEE02", "subject_name": "Open Elective II", "abbreviation": "OE-2", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "EE3781", "subject_name": "Project Work Phase I", "abbreviation": "PROJ-1", "periods_per_week": 4, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 2}
]
R2021_DATA[("B.E.", "EEE", "Semester 8")] = [
    {"subject_code": "EE3881", "subject_name": "Project Work Phase II / Industrial Internship", "abbreviation": "PROJ-2", "periods_per_week": 12, "is_lab": True, "lab_duration": 4, "difficulty_level": 4, "credits": 10}
]

# 6. MECH (B.E.)
R2021_DATA[("B.E.", "MECH", "Semester 1")] = SEM1_COMMON
R2021_DATA[("B.E.", "MECH", "Semester 2")] = SEM2_NON_CIRCUIT
R2021_DATA[("B.E.", "MECH", "Semester 3")] = [
    {"subject_code": "MA3351", "subject_name": "Transforms and Partial Differential Equations", "abbreviation": "TPDE", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "ME3351", "subject_name": "Engineering Thermodynamics", "abbreviation": "THERMO", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "ME3391", "subject_name": "Fluid Mechanics and Machinery", "abbreviation": "FMM", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "ME3392", "subject_name": "Engineering Materials and Metallurgy", "abbreviation": "EMM", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "ME3393", "subject_name": "Manufacturing Processes", "abbreviation": "MP", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "ME3381", "subject_name": "Fluid Mechanics and Machinery Laboratory", "abbreviation": "FMM LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "ME3382", "subject_name": "Manufacturing Technology Laboratory", "abbreviation": "MT LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "MECH", "Semester 4")] = [
    {"subject_code": "ME3451", "subject_name": "Thermal Engineering - I", "abbreviation": "TE-1", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "ME3491", "subject_name": "Theory of Machines", "abbreviation": "TOM", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "ME3492", "subject_name": "Kinematics of Machinery", "abbreviation": "KOM", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "ME3493", "subject_name": "Strength of Materials", "abbreviation": "SOM", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "GE3451", "subject_name": "Environmental Sciences and Sustainability", "abbreviation": "EVS", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
    {"subject_code": "ME3461", "subject_name": "Thermal Engineering Laboratory - I", "abbreviation": "TE LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "ME3462", "subject_name": "Strength of Materials Laboratory", "abbreviation": "SOM LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "MECH", "Semester 5")] = [
    {"subject_code": "ME3551", "subject_name": "Thermal Engineering - II", "abbreviation": "TE-2", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "ME3591", "subject_name": "Design of Machine Elements", "abbreviation": "DME", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "ME3592", "subject_name": "Metrology and Measurements", "abbreviation": "MM", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "PEME01", "subject_name": "Professional Elective I (Automobile Engineering)", "abbreviation": "AUTO", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "PEME02", "subject_name": "Professional Elective II (Gas Dynamics & Jet Prop)", "abbreviation": "GAS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "MC3501", "subject_name": "Constitution of India", "abbreviation": "COI", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 0},
    {"subject_code": "ME3561", "subject_name": "Thermal Engineering Laboratory - II", "abbreviation": "TE2 LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "ME3562", "subject_name": "Metrology and Dynamics Laboratory", "abbreviation": "MET LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "MECH", "Semester 6")] = [
    {"subject_code": "ME3691", "subject_name": "Design of Transmission Systems", "abbreviation": "DTS", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "ME3692", "subject_name": "Computer Integrated Manufacturing", "abbreviation": "CIM", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PEME03", "subject_name": "Professional Elective III (Robotics & Automation)", "abbreviation": "ROBO", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PEME04", "subject_name": "Professional Elective IV (Refrigeration & AC)", "abbreviation": "RAC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "OEME01", "subject_name": "Open Elective I", "abbreviation": "OE-1", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "ME3661", "subject_name": "CAD / CAM Laboratory", "abbreviation": "CAD LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "ME3681", "subject_name": "Mini Project", "abbreviation": "MINI PROJ", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "MECH", "Semester 7")] = [
    {"subject_code": "GE3791", "subject_name": "Human Values and Ethics", "abbreviation": "HVE", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
    {"subject_code": "ME3791", "subject_name": "Mechatronics Systems", "abbreviation": "MECHATRON", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PEME05", "subject_name": "Professional Elective V (Additive Manufacturing)", "abbreviation": "AM", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "PEME06", "subject_name": "Professional Elective VI (Power Plant Engineering)", "abbreviation": "PPE", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "OEME02", "subject_name": "Open Elective II", "abbreviation": "OE-2", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "ME3781", "subject_name": "Project Work Phase I", "abbreviation": "PROJ-1", "periods_per_week": 4, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 2}
]
R2021_DATA[("B.E.", "MECH", "Semester 8")] = [
    {"subject_code": "ME3881", "subject_name": "Project Work Phase II / Industrial Internship", "abbreviation": "PROJ-2", "periods_per_week": 12, "is_lab": True, "lab_duration": 4, "difficulty_level": 4, "credits": 10}
]

# 7. CIVIL (B.E.)
R2021_DATA[("B.E.", "CIVIL", "Semester 1")] = SEM1_COMMON
R2021_DATA[("B.E.", "CIVIL", "Semester 2")] = SEM2_NON_CIRCUIT
R2021_DATA[("B.E.", "CIVIL", "Semester 3")] = [
    {"subject_code": "MA3351", "subject_name": "Transforms and Partial Differential Equations", "abbreviation": "TPDE", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "CE3301", "subject_name": "Fluid Mechanics", "abbreviation": "FM", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "CE3302", "subject_name": "Construction Materials and Technology", "abbreviation": "CMT", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "CE3303", "subject_name": "Water Supply and Wastewater Engineering", "abbreviation": "WSWE", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "CE3351", "subject_name": "Surveying and Levelling", "abbreviation": "SURVEY", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "CE3361", "subject_name": "Surveying and Levelling Laboratory", "abbreviation": "SURV LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "CE3362", "subject_name": "Water and Wastewater Analysis Laboratory", "abbreviation": "WW LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "CIVIL", "Semester 4")] = [
    {"subject_code": "CE3401", "subject_name": "Applied Hydraulics Engineering", "abbreviation": "AHE", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "CE3402", "subject_name": "Strength of Materials - I", "abbreviation": "SOM-1", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "CE3403", "subject_name": "Concrete Technology", "abbreviation": "CT", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "CE3404", "subject_name": "Soil Mechanics", "abbreviation": "SM", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "GE3451", "subject_name": "Environmental Sciences and Sustainability", "abbreviation": "EVS", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
    {"subject_code": "CE3461", "subject_name": "Hydraulic Engineering Laboratory", "abbreviation": "HYD LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "CE3462", "subject_name": "Soil Mechanics Laboratory", "abbreviation": "SOIL LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "CIVIL", "Semester 5")] = [
    {"subject_code": "CE3501", "subject_name": "Structural Analysis - I", "abbreviation": "SA-1", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "CE3502", "subject_name": "Design of Reinforced Concrete Structural Elements", "abbreviation": "DRCS", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "CE3503", "subject_name": "Foundation Engineering", "abbreviation": "FE", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PECE01", "subject_name": "Professional Elective I (Transportation Engineering)", "abbreviation": "TE", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "PECE02", "subject_name": "Professional Elective II (Hydrology & Water Res)", "abbreviation": "HYDROL", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "MC3501", "subject_name": "Constitution of India", "abbreviation": "COI", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 0},
    {"subject_code": "CE3561", "subject_name": "Concrete and Highway Materials Laboratory", "abbreviation": "CHM LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "CE3562", "subject_name": "Survey Camp (2 Weeks)", "abbreviation": "CAMP", "periods_per_week": 2, "is_lab": True, "lab_duration": 2, "difficulty_level": 2, "credits": 1}
]
R2021_DATA[("B.E.", "CIVIL", "Semester 6")] = [
    {"subject_code": "CE3601", "subject_name": "Structural Analysis - II", "abbreviation": "SA-2", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "CE3602", "subject_name": "Design of Steel Structural Elements", "abbreviation": "DSSE", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "PECE03", "subject_name": "Professional Elective III (Irrigation Engineering)", "abbreviation": "IRRIG", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "PECE04", "subject_name": "Professional Elective IV (Remote Sensing and GIS)", "abbreviation": "GIS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "OECE01", "subject_name": "Open Elective I", "abbreviation": "OE-1", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "CE3661", "subject_name": "Computer Aided Design and Drafting Laboratory", "abbreviation": "CADD LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "CE3681", "subject_name": "Mini Project", "abbreviation": "MINI PROJ", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "CIVIL", "Semester 7")] = [
    {"subject_code": "GE3791", "subject_name": "Human Values and Ethics", "abbreviation": "HVE", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
    {"subject_code": "CE3701", "subject_name": "Estimation, Costing and Valuation Engineering", "abbreviation": "ECV", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PECE05", "subject_name": "Professional Elective V (Earthquake Engineering)", "abbreviation": "QUAKE", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PECE06", "subject_name": "Professional Elective VI (Ground Improvement Techniques)", "abbreviation": "GIT", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "OECE02", "subject_name": "Open Elective II", "abbreviation": "OE-2", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "CE3781", "subject_name": "Project Work Phase I", "abbreviation": "PROJ-1", "periods_per_week": 4, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 2}
]
R2021_DATA[("B.E.", "CIVIL", "Semester 8")] = [
    {"subject_code": "CE3881", "subject_name": "Project Work Phase II / Industrial Internship", "abbreviation": "PROJ-2", "periods_per_week": 12, "is_lab": True, "lab_duration": 4, "difficulty_level": 4, "credits": 10}
]

# 8. CSBS (B.Tech.)
R2021_DATA[("B.Tech.", "CSBS", "Semester 1")] = SEM1_COMMON
R2021_DATA[("B.Tech.", "CSBS", "Semester 2")] = SEM2_CIRCUIT
R2021_DATA[("B.Tech.", "CSBS", "Semester 3")] = [
    {"subject_code": "MA3354", "subject_name": "Discrete Mathematics and Graph Theory", "abbreviation": "DMGT", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "CB3301", "subject_name": "Data Structures and Algorithms with Business Cases", "abbreviation": "DSA-BC", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "CB3302", "subject_name": "Computational Statistics", "abbreviation": "CS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "CB3303", "subject_name": "Fundamentals of Economics and Financial Accounting", "abbreviation": "FEFA", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "CB3381", "subject_name": "Data Structures Laboratory", "abbreviation": "DS LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "CB3382", "subject_name": "Statistical Software Laboratory (R / Python)", "abbreviation": "STAT LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.Tech.", "CSBS", "Semester 4")] = [
    {"subject_code": "CB3401", "subject_name": "Operating Systems & Systems Programming", "abbreviation": "OS", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "CB3402", "subject_name": "Database Management Systems", "abbreviation": "DBMS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "CB3403", "subject_name": "Marketing Research and Management", "abbreviation": "MRM", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "CB3404", "subject_name": "Software Design & Architecture", "abbreviation": "SDA", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "GE3451", "subject_name": "Environmental Sciences and Sustainability", "abbreviation": "EVS", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
    {"subject_code": "CB3461", "subject_name": "Database Management Systems Laboratory", "abbreviation": "DBMS LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "CB3462", "subject_name": "Operating Systems Laboratory", "abbreviation": "OS LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.Tech.", "CSBS", "Semester 5")] = [
    {"subject_code": "CB3501", "subject_name": "Machine Learning & Cognitive Business", "abbreviation": "ML-COG", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "CB3502", "subject_name": "Financial Management and Business Valuation", "abbreviation": "FMBV", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "CB3503", "subject_name": "Enterprise Systems (ERP & SAP)", "abbreviation": "ERP", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "PECB01", "subject_name": "Professional Elective I (Design Thinking)", "abbreviation": "DES", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "MC3501", "subject_name": "Constitution of India", "abbreviation": "COI", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 0},
    {"subject_code": "CB3561", "subject_name": "Machine Learning for Business Lab", "abbreviation": "ML LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "CB3562", "subject_name": "Enterprise Systems Laboratory", "abbreviation": "ERP LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.Tech.", "CSBS", "Semester 6")] = [
    {"subject_code": "CB3601", "subject_name": "Business Analytics & Big Data", "abbreviation": "BABD", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "CB3602", "subject_name": "Information Security & Compliance", "abbreviation": "ISC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PECB02", "subject_name": "Professional Elective II (Business Strategy)", "abbreviation": "STRAT", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "PECB03", "subject_name": "Professional Elective III (Cloud for Business)", "abbreviation": "CLOUD", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "OECB01", "subject_name": "Open Elective I", "abbreviation": "OE-1", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "CB3661", "subject_name": "Business Analytics Laboratory", "abbreviation": "BA LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "CB3681", "subject_name": "Mini Project", "abbreviation": "MINI PROJ", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.Tech.", "CSBS", "Semester 7")] = [
    {"subject_code": "GE3791", "subject_name": "Human Values and Ethics", "abbreviation": "HVE", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
    {"subject_code": "CB3701", "subject_name": "Services Science & SOA", "abbreviation": "SOA", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "PECB04", "subject_name": "Professional Elective IV (Financial Technologies / Fintech)", "abbreviation": "FINTECH", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PECB05", "subject_name": "Professional Elective V (HR Analytics)", "abbreviation": "HR", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "OECB02", "subject_name": "Open Elective II", "abbreviation": "OE-2", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "CB3781", "subject_name": "Project Work Phase I", "abbreviation": "PROJ-1", "periods_per_week": 4, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 2}
]
R2021_DATA[("B.Tech.", "CSBS", "Semester 8")] = [
    {"subject_code": "CB3881", "subject_name": "Project Work Phase II / Corporate Internship", "abbreviation": "PROJ-2", "periods_per_week": 12, "is_lab": True, "lab_duration": 4, "difficulty_level": 4, "credits": 10}
]

# 9. CYBER (B.E.)
R2021_DATA[("B.E.", "CYBER", "Semester 1")] = SEM1_COMMON
R2021_DATA[("B.E.", "CYBER", "Semester 2")] = SEM2_CIRCUIT
R2021_DATA[("B.E.", "CYBER", "Semester 3")] = [
    {"subject_code": "MA3354", "subject_name": "Discrete Mathematics and Number Theory", "abbreviation": "DMNT", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "CS3351", "subject_name": "Digital Principles and Computer Organization", "abbreviation": "DPCO", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "CY3301", "subject_name": "Data Structures and Secure Coding", "abbreviation": "DS-SEC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "CY3302", "subject_name": "Foundations of Cyber Security", "abbreviation": "FCS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "CY3381", "subject_name": "Data Structures & Secure Coding Lab", "abbreviation": "SEC LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "CY3382", "subject_name": "Cyber Defense and Linux System Lab", "abbreviation": "LINUX LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "GE3361", "subject_name": "Professional Development", "abbreviation": "PD LAB", "periods_per_week": 2, "is_lab": True, "lab_duration": 2, "difficulty_level": 2, "credits": 1}
]
R2021_DATA[("B.E.", "CYBER", "Semester 4")] = [
    {"subject_code": "CY3401", "subject_name": "Applied Cryptography and PKI", "abbreviation": "CRYPTO", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "CY3402", "subject_name": "Operating System Security", "abbreviation": "OS-SEC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "CY3403", "subject_name": "Network Security and Protocols", "abbreviation": "NET-SEC", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "CS3492", "subject_name": "Database Management Systems", "abbreviation": "DBMS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "GE3451", "subject_name": "Environmental Sciences and Sustainability", "abbreviation": "EVS", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
    {"subject_code": "CY3461", "subject_name": "Network Security Laboratory", "abbreviation": "NET LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "CS3461", "subject_name": "Database Management Systems Laboratory", "abbreviation": "DBMS LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "CYBER", "Semester 5")] = [
    {"subject_code": "CY3501", "subject_name": "Ethical Hacking and Penetration Testing", "abbreviation": "ETHICAL", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "CY3502", "subject_name": "Cloud Security and DevSecOps", "abbreviation": "DEVSECOPS", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "CY3503", "subject_name": "Malware Analysis and Reverse Engineering", "abbreviation": "MALWARE", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "PECY01", "subject_name": "Professional Elective I (Digital Forensics)", "abbreviation": "FORENSIC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "MC3501", "subject_name": "Constitution of India", "abbreviation": "COI", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 0},
    {"subject_code": "CY3561", "subject_name": "Ethical Hacking and Pen-Testing Laboratory", "abbreviation": "HACK LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "CY3562", "subject_name": "Malware Analysis Laboratory", "abbreviation": "MAL LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "CYBER", "Semester 6")] = [
    {"subject_code": "CY3601", "subject_name": "Cyber Threat Intelligence & Threat Hunting", "abbreviation": "CTI", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "CY3602", "subject_name": "IoT and Industrial Cyber Security", "abbreviation": "IOT-SEC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PECY02", "subject_name": "Professional Elective II (Blockchain Security)", "abbreviation": "BC-SEC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PECY03", "subject_name": "Professional Elective III (SOC Operations)", "abbreviation": "SOC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "OECY01", "subject_name": "Open Elective I", "abbreviation": "OE-1", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "CY3661", "subject_name": "Security Operations Center (SOC) Lab", "abbreviation": "SOC LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "CY3681", "subject_name": "Mini Project", "abbreviation": "MINI PROJ", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "CYBER", "Semester 7")] = [
    {"subject_code": "GE3791", "subject_name": "Human Values and Ethics", "abbreviation": "HVE", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
    {"subject_code": "CY3701", "subject_name": "Cyber Law, Compliance and Standards (ISO/NIST)", "abbreviation": "CYBERLAW", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "PECY04", "subject_name": "Professional Elective IV (AI in Cyber Security)", "abbreviation": "AI-SEC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "PECY05", "subject_name": "Professional Elective V (Mobile Device Security)", "abbreviation": "MOB-SEC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "OECY02", "subject_name": "Open Elective II", "abbreviation": "OE-2", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "CY3781", "subject_name": "Project Work Phase I", "abbreviation": "PROJ-1", "periods_per_week": 4, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 2}
]
R2021_DATA[("B.E.", "CYBER", "Semester 8")] = [
    {"subject_code": "CY3881", "subject_name": "Project Work Phase II / Industrial Internship", "abbreviation": "PROJ-2", "periods_per_week": 12, "is_lab": True, "lab_duration": 4, "difficulty_level": 4, "credits": 10}
]

# 10. BME (B.E.)
R2021_DATA[("B.E.", "BME", "Semester 1")] = SEM1_COMMON
R2021_DATA[("B.E.", "BME", "Semester 2")] = SEM2_NON_CIRCUIT
R2021_DATA[("B.E.", "BME", "Semester 3")] = [
    {"subject_code": "MA3355", "subject_name": "Random Processes and Linear Algebra", "abbreviation": "RPLA", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "BM3351", "subject_name": "Anatomy and Human Physiology", "abbreviation": "AHP", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "BM3352", "subject_name": "Sensors and Measurements", "abbreviation": "SM", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "EC3353", "subject_name": "Electronic Devices and Circuits", "abbreviation": "EDC", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "BM3361", "subject_name": "Human Physiology Laboratory", "abbreviation": "HP LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "EC3361", "subject_name": "Electronic Devices and Circuits Laboratory", "abbreviation": "EDC LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "GE3361", "subject_name": "Professional Development", "abbreviation": "PD LAB", "periods_per_week": 2, "is_lab": True, "lab_duration": 2, "difficulty_level": 2, "credits": 1}
]
R2021_DATA[("B.E.", "BME", "Semester 4")] = [
    {"subject_code": "BM3401", "subject_name": "Biomedical Instrumentation", "abbreviation": "BMI", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "BM3402", "subject_name": "Analog and Digital Integrated Circuits", "abbreviation": "ADIC", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "BM3403", "subject_name": "Pathology and Microbiology", "abbreviation": "PATH", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "BM3404", "subject_name": "Biosignal Processing", "abbreviation": "BSP", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "GE3451", "subject_name": "Environmental Sciences and Sustainability", "abbreviation": "EVS", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
    {"subject_code": "BM3461", "subject_name": "Biomedical Instrumentation Laboratory", "abbreviation": "BMI LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "BM3462", "subject_name": "Bio-Signal Processing Laboratory", "abbreviation": "BSP LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "BME", "Semester 5")] = [
    {"subject_code": "BM3501", "subject_name": "Diagnostic and Therapeutic Equipment - I", "abbreviation": "DTE-1", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "BM3502", "subject_name": "Medical Physics and Radiation Safety", "abbreviation": "MEDPHY", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "BM3503", "subject_name": "Bio-Control Systems", "abbreviation": "BCS", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "PEBM01", "subject_name": "Professional Elective I (Biomaterials)", "abbreviation": "BIOMAT", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "MC3501", "subject_name": "Constitution of India", "abbreviation": "COI", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 0},
    {"subject_code": "BM3561", "subject_name": "Diagnostic Equipment Laboratory", "abbreviation": "DIAG LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "BM3562", "subject_name": "Pathology and Microbiology Laboratory", "abbreviation": "PATH LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "BME", "Semester 6")] = [
    {"subject_code": "BM3601", "subject_name": "Diagnostic and Therapeutic Equipment - II", "abbreviation": "DTE-2", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "BM3602", "subject_name": "Medical Image Processing", "abbreviation": "MIP", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "PEBM02", "subject_name": "Professional Elective II (Hospital Management)", "abbreviation": "HOSP", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "PEBM03", "subject_name": "Professional Elective III (Neural Engineering)", "abbreviation": "NEURAL", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "OEBM01", "subject_name": "Open Elective I", "abbreviation": "OE-1", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "BM3661", "subject_name": "Medical Image Processing Laboratory", "abbreviation": "MIP LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "BM3681", "subject_name": "Mini Project", "abbreviation": "MINI PROJ", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]
R2021_DATA[("B.E.", "BME", "Semester 7")] = [
    {"subject_code": "GE3791", "subject_name": "Human Values and Ethics", "abbreviation": "HVE", "periods_per_week": 2, "is_lab": False, "lab_duration": 0, "difficulty_level": 2, "credits": 2},
    {"subject_code": "BM3701", "subject_name": "Biotelemetry and Telemedicine", "abbreviation": "TELEMED", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "PEBM04", "subject_name": "Professional Elective IV (Rehabilitation Engineering)", "abbreviation": "REHAB", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "PEBM05", "subject_name": "Professional Elective V (Artificial Organs)", "abbreviation": "ARTORG", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "OEBM02", "subject_name": "Open Elective II", "abbreviation": "OE-2", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "BM3781", "subject_name": "Project Work Phase I", "abbreviation": "PROJ-1", "periods_per_week": 4, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 2}
]
R2021_DATA[("B.E.", "BME", "Semester 8")] = [
    {"subject_code": "BM3881", "subject_name": "Project Work Phase II / Clinical Internship", "abbreviation": "PROJ-2", "periods_per_week": 12, "is_lab": True, "lab_duration": 4, "difficulty_level": 4, "credits": 10}
]

# ══════════════════════════════════════════════════════════════════════════════
# REGULATION 2023 (R2023) - AUTONOMOUS ALIGNED
# ══════════════════════════════════════════════════════════════════════════════

R2023_DATA: Dict[tuple, List[Dict[str, Any]]] = {}

# Map Sem 1 & 2 for all branches
for dept in ["CSE", "ECE", "EEE", "MECH", "CIVIL", "BME", "CYBER"]:
    R2023_DATA[("B.E.", dept, "Semester 1")] = SEM1_COMMON
    R2023_DATA[("B.E.", dept, "Semester 2")] = SEM2_CIRCUIT if dept in ["CSE", "ECE", "EEE", "CYBER"] else SEM2_NON_CIRCUIT

for dept in ["IT", "AIDS", "CSBS"]:
    R2023_DATA[("B.Tech.", dept, "Semester 1")] = SEM1_COMMON
    R2023_DATA[("B.Tech.", dept, "Semester 2")] = SEM2_CIRCUIT

# R2023 core course samples across departments and semesters 3 to 8
R2023_DATA[("B.E.", "CSE", "Semester 3")] = [
    {"subject_code": "23CS301", "subject_name": "Discrete Mathematical Structures", "abbreviation": "DMS", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "23CS302", "subject_name": "Data Structures using C++ and STL", "abbreviation": "DS-STL", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "23CS303", "subject_name": "Computer Architecture and RISC-V", "abbreviation": "RISC-V", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "23CS304", "subject_name": "Python for Data Science & AI", "abbreviation": "PY-AI", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "23CS305", "subject_name": "Database Management & NoSQL Systems", "abbreviation": "NOSQL", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "23CS311", "subject_name": "Data Structures & STL Laboratory", "abbreviation": "STL LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "23CS312", "subject_name": "Database & NoSQL Laboratory", "abbreviation": "NOSQL LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "23PD301", "subject_name": "Critical Thinking & Design Innovation", "abbreviation": "DES INN", "periods_per_week": 2, "is_lab": True, "lab_duration": 2, "difficulty_level": 2, "credits": 1}
]
R2023_DATA[("B.E.", "CSE", "Semester 4")] = [
    {"subject_code": "23CS401", "subject_name": "Design & Analysis of Algorithms", "abbreviation": "DAA", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "23CS402", "subject_name": "Operating Systems & Linux Internals", "abbreviation": "OS-LINUX", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "23CS403", "subject_name": "Applied Machine Learning", "abbreviation": "AML", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "23CS404", "subject_name": "Full Stack Web Development (React & Node)", "abbreviation": "FULLSTACK", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "23CS411", "subject_name": "Algorithms & Problem Solving Lab", "abbreviation": "ALG LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "23CS412", "subject_name": "Full Stack Web Development Lab", "abbreviation": "WEB LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]

# For all other R2023 semesters & branches, inherit from R2021 with modern 23-prefix codes for seamless completeness
for (deg, dept, sem), subs in R2021_DATA.items():
    if (deg, dept, sem) not in R2023_DATA:
        r23_subs = []
        for s in subs:
            s_new = dict(s)
            s_new["subject_code"] = "23" + s["subject_code"][2:] if len(s["subject_code"]) >= 4 and s["subject_code"][:2].isalpha() else s["subject_code"]
            r23_subs.append(s_new)
        R2023_DATA[(deg, dept, sem)] = r23_subs


# ══════════════════════════════════════════════════════════════════════════════
# REGULATION 2025 (R2025) - NEXTGEN AI & INDUSTRY 5.0
# ══════════════════════════════════════════════════════════════════════════════

R2025_DATA: Dict[tuple, List[Dict[str, Any]]] = {}

# Map Sem 1 & 2 for all branches
for dept in ["CSE", "ECE", "EEE", "MECH", "CIVIL", "BME", "CYBER"]:
    R2025_DATA[("B.E.", dept, "Semester 1")] = SEM1_COMMON
    R2025_DATA[("B.E.", dept, "Semester 2")] = SEM2_CIRCUIT if dept in ["CSE", "ECE", "EEE", "CYBER"] else SEM2_NON_CIRCUIT

for dept in ["IT", "AIDS", "CSBS"]:
    R2025_DATA[("B.Tech.", dept, "Semester 1")] = SEM1_COMMON
    R2025_DATA[("B.Tech.", dept, "Semester 2")] = SEM2_CIRCUIT

R2025_DATA[("B.E.", "CSE", "Semester 3")] = [
    {"subject_code": "25CS301", "subject_name": "Discrete Mathematics & Graph Analytics", "abbreviation": "DMGA", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "25CS302", "subject_name": "Modern Data Structures in Rust & C++", "abbreviation": "DS-RUST", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "25CS303", "subject_name": "Computer Systems & Heterogeneous Computing", "abbreviation": "CS-HET", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "25CS304", "subject_name": "Generative AI Foundations & Prompt Engineering", "abbreviation": "GEN-AI", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 4},
    {"subject_code": "25CS305", "subject_name": "Cloud-Native Databases & Distributed Storage", "abbreviation": "CLOUD-DB", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 3, "credits": 3},
    {"subject_code": "25CS311", "subject_name": "High-Performance Data Structures Laboratory", "abbreviation": "HPDS LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "25CS312", "subject_name": "Generative AI & LLM Systems Laboratory", "abbreviation": "LLM LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "25PD301", "subject_name": "AI Product Development & Agile Studio", "abbreviation": "AI STUDIO", "periods_per_week": 2, "is_lab": True, "lab_duration": 2, "difficulty_level": 2, "credits": 1}
]
R2025_DATA[("B.E.", "CSE", "Semester 4")] = [
    {"subject_code": "25CS401", "subject_name": "Quantum Computing & Advanced Algorithms", "abbreviation": "QUANTUM", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "25CS402", "subject_name": "Microservices & Distributed Systems", "abbreviation": "MICROSERV", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "25CS403", "subject_name": "Deep Learning & Transformer Architectures", "abbreviation": "DL-TRANS", "periods_per_week": 4, "is_lab": False, "lab_duration": 0, "difficulty_level": 5, "credits": 4},
    {"subject_code": "25CS404", "subject_name": "Cyber Threat Intelligence & Zero Trust", "abbreviation": "ZERO-TRST", "periods_per_week": 3, "is_lab": False, "lab_duration": 0, "difficulty_level": 4, "credits": 3},
    {"subject_code": "25CS411", "subject_name": "Deep Learning & Vision Laboratory", "abbreviation": "DL LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5},
    {"subject_code": "25CS412", "subject_name": "Cloud DevOps & Microservices Laboratory", "abbreviation": "DEVOPS LAB", "periods_per_week": 3, "is_lab": True, "lab_duration": 3, "difficulty_level": 3, "credits": 1.5}
]

# For all other R2025 semesters & branches, inherit with 25-prefix codes for full 8-semester coverage
for (deg, dept, sem), subs in R2021_DATA.items():
    if (deg, dept, sem) not in R2025_DATA:
        r25_subs = []
        for s in subs:
            s_new = dict(s)
            s_new["subject_code"] = "25" + s["subject_code"][2:] if len(s["subject_code"]) >= 4 and s["subject_code"][:2].isalpha() else s["subject_code"]
            r25_subs.append(s_new)
        R2025_DATA[(deg, dept, sem)] = r25_subs

# Mirror both B.E. and B.Tech. for ALL 10 branches (CSE, IT, AIDS, ECE, EEE, MECH, CIVIL, CSBS, CYBER, BME)
# across all 8 semesters so any user selection under B.E. or B.Tech. resolves immediately.
for data_dict in (R2021_DATA, R2023_DATA, R2025_DATA):
    for (deg, dept, sem), subs in list(data_dict.items()):
        alt_deg = "B.Tech." if deg == "B.E." else "B.E."
        if (alt_deg, dept, sem) not in data_dict:
            data_dict[(alt_deg, dept, sem)] = subs


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC ACCESSORS & INDEX GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

DEPT_ALIASES = {
    "AI&DS": "AIDS",
    "AI & DS": "AIDS",
    "AI-DS": "AIDS",
    "ARTIFICIAL INTELLIGENCE": "AIDS",
    "CYBER SECURITY": "CYBER",
    "CYBERSECURITY": "CYBER",
    "CS & BS": "CSBS",
    "CS-BS": "CSBS",
    "BIO MEDICAL": "BME",
    "BIOMEDICAL": "BME",
    "MECHANICAL": "MECH",
    "CIVIL ENGINEERING": "CIVIL",
    "COMPUTER SCIENCE": "CSE"
}

def normalize_department(dept_str: str) -> str:
    """Normalize user or form department string to standard code."""
    d = (dept_str or "").strip().upper()
    if d in DEPT_ALIASES:
        return DEPT_ALIASES[d]
    for k, v in DEPT_ALIASES.items():
        if k in d:
            return v
    return d

def normalize_semester(sem_str: str) -> str:
    """Normalize various semester strings ('1', 'Sem 1', 'Semester 1 (1st Year)') to standard 'Semester X'."""
    s = (sem_str or "").strip()
    match = re.search(r'\d+', s)
    if match:
        return f"Semester {match.group(0)}"
    return s

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
    """Retrieve specific curriculum subjects for given parameters with instant O(1) lookup."""
    reg = (regulation or "R2021").upper().strip()
    norm_dept = normalize_department(department)
    norm_sem = normalize_semester(semester)
    norm_deg = "B.Tech." if "TECH" in (degree or "").upper() else "B.E."

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

    key = (norm_deg, norm_dept, norm_sem)
    if key in data_source:
        subjects = [dict(s) for s in data_source[key]]
        for s in subjects:
            s["department"] = norm_dept
        
        sem_num = norm_sem.split()[-1] if " " in norm_sem else norm_sem
        class_name = f"{norm_deg} {norm_dept} - Sem {sem_num} (Sec A)"
        
        return {
            "success": True,
            "regulation": reg_title,
            "degree": norm_deg,
            "department": norm_dept,
            "semester": norm_sem,
            "class_name": class_name,
            "subjects": subjects
        }
    
    # Fallback to general department and semester match
    for (d, dept, sem), subs in data_source.items():
        if dept == norm_dept and sem == norm_sem:
            subjects = [dict(s) for s in subs]
            for s in subjects:
                s["department"] = norm_dept
            sem_num = norm_sem.split()[-1] if " " in norm_sem else norm_sem
            return {
                "success": True,
                "regulation": reg_title,
                "degree": d,
                "department": norm_dept,
                "semester": norm_sem,
                "class_name": f"{d} {norm_dept} - Sem {sem_num} (Sec A)",
                "subjects": subjects
            }

    return None

