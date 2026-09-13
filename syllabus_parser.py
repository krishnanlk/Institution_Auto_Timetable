"""
syllabus_parser.py - Intelligent Curriculum & Syllabus PDF Extractor for Anna University & Autonomous Colleges
"""
import re
import io
import math
from typing import List, Dict, Any, Optional

# Standard abbreviation generation rules for engineering courses
COMMON_ABBR_MAP = {
    "data structures": "DS",
    "data structures and algorithms": "DSA",
    "design and analysis of algorithms": "DAA",
    "database management systems": "DBMS",
    "object oriented programming": "OOP",
    "operating systems": "OS",
    "computer networks": "CN",
    "software engineering": "SE",
    "artificial intelligence": "AI",
    "machine learning": "ML",
    "deep learning": "DL",
    "discrete mathematics": "DM",
    "engineering mathematics": "EM",
    "digital principles and system design": "DPSD",
    "digital principles and computer organization": "DPCO",
    "computer architecture": "CA",
    "theory of computation": "TOC",
    "compiler design": "CD",
    "cloud computing": "CC",
    "cyber security": "CS",
    "internet of things": "IOT",
    "python programming": "PYTHON",
    "c programming": "C PROG",
    "java programming": "JAVA",
    "web technology": "WT",
    "professional ethics in engineering": "ETHICS",
    "total quality management": "TQM",
    "environmental sciences and sustainability": "EVS",
}

def generate_abbreviation(title: str, is_lab: bool = False) -> str:
    """Generate concise 2-6 letter abbreviation from subject title."""
    clean_title = re.sub(r'[^a-zA-Z0-9\s]', ' ', title).strip().lower()
    
    # Check exact/partial mapping
    for key, abbr in COMMON_ABBR_MAP.items():
        if key in clean_title:
            if is_lab and not abbr.endswith("LAB"):
                return f"{abbr} LAB"
            return abbr
            
    # Heuristic: First letters of major words (skip stopwords)
    stopwords = {"and", "of", "in", "to", "for", "the", "a", "an", "with", "on", "using"}
    words = [w for w in clean_title.split() if w and w not in stopwords]
    
    if not words:
        return title[:5].upper()
        
    if len(words) == 1:
        abbr = words[0][:5].upper()
    elif len(words) == 2:
        abbr = (words[0][:2] + words[1][:2]).upper()
    else:
        abbr = "".join(w[0] for w in words[:5]).upper()
        
    if is_lab and "LAB" not in abbr:
        abbr = f"{abbr} LAB" if len(abbr) <= 4 else f"{abbr[:3]} LAB"
        
    return abbr[:8].strip()


def calculate_difficulty(category: str, title: str, credits: float, is_lab: bool) -> int:
    """
    Calculate 1-5 difficulty level based on Anna University / AICTE curriculum rules:
    - Core Maths / Physics (BSC) & Heavy Theory Core (PCC): 4 or 5
    - Standard Core (PCC) / Engineering Science (ESC): 3 or 4
    - Labs (Practical): 3
    - Electives (PEC / OEC): 3
    - Humanities, Soft Skills, Constitution, EVS (HSMC / MC): 2
    """
    cat = (category or "").upper().strip()
    title_lower = title.lower()
    
    # Special title cues
    if any(k in title_lower for k in ["mathematics", "calculus", "linear algebra", "discrete math", "probability", "statistics", "theory of computation", "compiler design"]):
        return 5 if credits >= 4 else 4
        
    if is_lab:
        return 3
        
    if any(k in title_lower for k in ["english", "communication", "heritage", "tamils", "constitution", "environmental", "values", "ethics", "soft skills", "personality"]):
        return 2
        
    if "BSC" in cat:
        return 5 if credits >= 4 else 4
    elif "PCC" in cat:
        return 4 if credits >= 3 else 3
    elif "ESC" in cat:
        return 3
    elif "PEC" in cat or "OEC" in cat:
        return 3
    elif "HSMC" in cat or "MC" in cat:
        return 2
        
    # Default based on credits
    if credits >= 4:
        return 4
    elif credits >= 3:
        return 3
    else:
        return 2


def extract_department_and_semesters_from_text(full_text: str) -> Dict[str, Any]:
    """Scan full document text to identify Department / Degree and available Semesters."""
    dept = "CSE"
    dept_patterns = [
        (r"(?:COMPUTER SCIENCE AND ENGINEERING|B\.?E\.?\s+CSE|DEPARTMENT OF CSE)", "CSE"),
        (r"(?:ELECTRONICS AND COMMUNICATION|B\.?E\.?\s+ECE|DEPARTMENT OF ECE)", "ECE"),
        (r"(?:ELECTRICAL AND ELECTRONICS|B\.?E\.?\s+EEE|DEPARTMENT OF EEE)", "EEE"),
        (r"(?:MECHANICAL ENGINEERING|B\.?E\.?\s+MECH)", "MECH"),
        (r"(?:CIVIL ENGINEERING|B\.?E\.?\s+CIVIL)", "CIVIL"),
        (r"(?:INFORMATION TECHNOLOGY|B\.?TECH\.?\s+IT)", "IT"),
        (r"(?:ARTIFICIAL INTELLIGENCE AND DATA SCIENCE|B\.?TECH\.?\s+AI&DS|AI\s*&\s*DS)", "AIDS"),
        (r"(?:BIOMEDICAL ENGINEERING|B\.?E\.?\s+BME)", "BME"),
    ]
    for pattern, d_code in dept_patterns:
        if re.search(pattern, full_text, re.IGNORECASE):
            dept = d_code
            break
            
    # Detect Regulation (e.g. R-2021, R2017, Regulation 2021)
    regulation = "R2021"
    reg_match = re.search(r"(?:REGULATION|REGULATIONS|R)[\s\-\:]*([12]\d{3})", full_text, re.IGNORECASE)
    if reg_match:
        regulation = f"R{reg_match.group(1)}"
        
    return {"department": dept, "regulation": regulation}


def parse_syllabus_pdf(file_bytes: bytes) -> Dict[str, Any]:
    """
    Parse uploaded syllabus / regulation PDF and return structured semester curriculums.
    Returns:
    {
        "success": bool,
        "regulation": str,
        "department": str,
        "semesters": {
            "Semester 3": [ {subject_dict}, ... ],
            "Semester 4": [ ... ]
        },
        "all_subjects": [ ... ],
        "raw_text_length": int
    }
    """
    import pdfplumber
    import pypdf

    full_text = ""
    tables_extracted = []
    
    # 1. Extract text and tables via pdfplumber
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                p_text = page.extract_text() or ""
                full_text += f"\n--- PAGE {page_idx + 1} ---\n" + p_text
                
                # Extract tables
                page_tables = page.extract_tables()
                if page_tables:
                    for t in page_tables:
                        tables_extracted.append({"page": page_idx + 1, "table": t, "page_text": p_text})
    except Exception as e:
        # Fallback to pypdf for text
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            for page_idx, page in enumerate(reader.pages):
                full_text += f"\n--- PAGE {page_idx + 1} ---\n" + (page.extract_text() or "")
        except Exception as e2:
            return {"success": False, "error": f"Failed to read PDF file: {str(e2)}"}

    if not full_text.strip():
        return {"success": False, "error": "PDF is empty or could not extract readable text."}

    meta = extract_department_and_semesters_from_text(full_text)
    
    semesters: Dict[str, List[Dict[str, Any]]] = {}
    
    # Strategy A: Parse through detected tabular structures
    if tables_extracted:
        for t_info in tables_extracted:
            table = t_info["table"]
            page_text = t_info["page_text"]
            
            # Identify current semester for this table
            sem_name = detect_semester_heading(page_text, table)
            if not sem_name:
                sem_name = "General / Elective"
                
            parsed_rows = parse_table_curriculum(table, meta["department"])
            if parsed_rows:
                if sem_name not in semesters:
                    semesters[sem_name] = []
                # Avoid duplicates
                existing_codes = {s["subject_code"] for s in semesters[sem_name]}
                for r in parsed_rows:
                    if r["subject_code"] not in existing_codes:
                        semesters[sem_name].append(r)
                        existing_codes.add(r["subject_code"])
                        
    # Strategy B: If no tables or empty, parse via regex line scanning
    if not any(semesters.values()):
        regex_semesters = parse_text_with_regex(full_text, meta["department"])
        if regex_semesters:
            semesters = regex_semesters

    # Build flat list of all subjects
    all_subjects = []
    for sem, subs in semesters.items():
        for s in subs:
            s_copy = dict(s)
            s_copy["semester"] = sem
            all_subjects.append(s_copy)

    return {
        "success": True,
        "department": meta["department"],
        "regulation": meta["regulation"],
        "semesters": semesters,
        "all_subjects": all_subjects,
        "total_subjects": len(all_subjects),
        "raw_text_length": len(full_text)
    }


def detect_semester_heading(page_text: str, table: Optional[List[List[str]]] = None) -> Optional[str]:
    """Detect 'SEMESTER I', 'SEMESTER 3', 'SEMESTER - IV', etc."""
    roman_map = {
        "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8,
        "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8
    }
    
    # Check in table headers first
    if table:
        for row in table[:3]:
            for cell in (row or []):
                if cell:
                    m = re.search(r"SEMESTER\s*[\-\:\–]?\s*([IVXivx1-8]+)", str(cell), re.IGNORECASE)
                    if m:
                        num = m.group(1).upper()
                        if num in roman_map:
                            return f"Semester {roman_map[num]}"
                            
    # Check page text
    matches = re.findall(r"SEMESTER\s*[\-\:\–]?\s*([IVXivx1-8]+)", page_text, re.IGNORECASE)
    if matches:
        num = matches[0].upper()
        if num in roman_map:
            return f"Semester {roman_map[num]}"
            
    return None


def parse_table_curriculum(table: List[List[Any]], dept: str) -> List[Dict[str, Any]]:
    """Parse extracted table rows into subject dicts."""
    subjects = []
    if not table or len(table) < 2:
        return subjects

    # Find header row index
    header_idx = -1
    col_map = {}
    
    for idx, row in enumerate(table[:5]):
        row_str = " ".join([str(c or "").lower() for c in row])
        if any(kw in row_str for kw in ["course code", "sub code", "course title", "subject name", "l", "t", "p", "c", "credits", "contact"]):
            header_idx = idx
            # Map columns
            for c_idx, cell in enumerate(row):
                cell_clean = str(cell or "").strip().lower().replace("\n", " ")
                if any(x in cell_clean for x in ["course code", "sub code", "subject code", "code"]):
                    col_map["code"] = c_idx
                elif any(x in cell_clean for x in ["course title", "subject name", "title", "subject"]):
                    col_map["title"] = c_idx
                elif any(x in cell_clean for x in ["cat", "category"]):
                    col_map["category"] = c_idx
                elif cell_clean == "l" or "lecture" in cell_clean:
                    col_map["l"] = c_idx
                elif cell_clean == "t" or "tutorial" in cell_clean:
                    col_map["t"] = c_idx
                elif cell_clean == "p" or "practical" in cell_clean:
                    col_map["p"] = c_idx
                elif cell_clean == "c" or "credits" in cell_clean:
                    col_map["c"] = c_idx
                elif any(x in cell_clean for x in ["contact", "periods", "total"]):
                    col_map["contact"] = c_idx
            break

    if header_idx == -1:
        return subjects

    # Parse rows following header
    for row in table[header_idx + 1:]:
        if not row or len(row) < 2:
            continue
            
        row_str = " ".join([str(c or "") for c in row]).strip()
        if not row_str or any(kw in row_str.lower() for kw in ["total credits", "total", "theory", "practical", "mandatory"]):
            continue

        # Extract values
        code = str(row[col_map["code"]]).strip() if "code" in col_map and col_map["code"] < len(row) and row[col_map["code"]] else ""
        title = str(row[col_map["title"]]).strip() if "title" in col_map and col_map["title"] < len(row) and row[col_map["title"]] else ""
        
        # Clean title & code from newlines
        code = re.sub(r'\s+', ' ', code).strip()
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Verify valid course code (e.g. CS3351, MA3354, GE3151, IT8501, or 3-4 letters + 3-4 digits)
        code_match = re.search(r"([A-Z]{2,5}\s*\d{3,5}[A-Z]?)", code)
        if not code_match:
            # Maybe code is embedded in title or 1st column
            code_match = re.search(r"([A-Z]{2,5}\s*\d{3,5}[A-Z]?)", row_str)
            if code_match:
                code = code_match.group(1).replace(" ", "")
            else:
                continue
        else:
            code = code_match.group(1).replace(" ", "")

        if not title or len(title) < 3 or title == code:
            # Fallback: extract title from row
            for c in row:
                c_str = str(c or "").strip()
                if len(c_str) > 5 and not re.match(r"^[0-9\.\s]+$", c_str) and c_str != code:
                    title = c_str
                    break

        # Extract numerical L, T, P, C
        def get_num(key: str, default: int = 0) -> int:
            if key in col_map and col_map[key] < len(row) and row[col_map[key]]:
                val_str = str(row[col_map[key]]).strip()
                m = re.search(r"(\d+(?:\.\d+)?)", val_str)
                if m:
                    try:
                        return int(float(m.group(1)))
                    except:
                        pass
            return default

        l_val = get_num("l", 3)
        t_val = get_num("t", 0)
        p_val = get_num("p", 0)
        c_val = get_num("c", 3)
        contact_val = get_num("contact", l_val + t_val + p_val)

        category = str(row[col_map["category"]]).strip() if "category" in col_map and col_map["category"] < len(row) and row[col_map["category"]] else ""
        
        # Determine if Lab
        is_lab = False
        lab_duration = 0
        
        if p_val >= 2 or any(kw in title.lower() for kw in ["laboratory", "lab", "practical", "workshop", "studio"]):
            is_lab = True
            lab_duration = min(max(p_val, 2), 3) if p_val > 0 else 2

        # Periods per week calculation:
        if is_lab:
            periods_per_week = max(p_val, 2)
        else:
            periods_per_week = max(l_val + t_val, 3)

        abbr = generate_abbreviation(title, is_lab)
        difficulty = calculate_difficulty(category, title, float(c_val), is_lab)

        subjects.append({
            "subject_code": code,
            "subject_name": title,
            "abbreviation": abbr,
            "department": dept,
            "category": category,
            "l": l_val,
            "t": t_val,
            "p": p_val,
            "credits": c_val,
            "periods_per_week": periods_per_week,
            "is_lab": is_lab,
            "lab_duration": lab_duration,
            "difficulty_level": difficulty
        })

    return subjects


def parse_text_with_regex(text: str, dept: str) -> Dict[str, List[Dict[str, Any]]]:
    """Fallback parser scanning line-by-line using regular expressions."""
    semesters: Dict[str, List[Dict[str, Any]]] = {}
    current_sem = "Semester 3"
    
    roman_map = {
        "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8,
        "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8
    }

    lines = text.split("\n")
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        # Check semester header
        sem_m = re.search(r"SEMESTER\s*[\-\:\–]?\s*([IVXivx1-8]+)", line_clean, re.IGNORECASE)
        if sem_m:
            num = sem_m.group(1).upper()
            if num in roman_map:
                current_sem = f"Semester {roman_map[num]}"
                if current_sem not in semesters:
                    semesters[current_sem] = []
            continue

        # Check subject line pattern:
        # e.g. "1. CS3351 Digital Principles and Computer Organization PCC 3 0 2 5 4"
        # or "CS3352 Data Structures and Algorithms PCC 3 0 0 3 3"
        m = re.search(r"(?:^\d+[\.\s]+)?([A-Z]{2,5}\s*\d{3,5}[A-Z]?)\s+([A-Za-z0-9\s&,\-\(\)]+?)\s+(BSC|ESC|PCC|PEC|OEC|MC|HSMC|EEC|PW|THEORY|PRACTICAL)?\s*(\d)\s*(\d)\s*(\d)\s*(?:\d+)?\s*(\d)", line_clean, re.IGNORECASE)
        if m:
            code = m.group(1).replace(" ", "")
            title = m.group(2).strip()
            cat = (m.group(3) or "").upper()
            l_val = int(m.group(4))
            t_val = int(m.group(5))
            p_val = int(m.group(6))
            c_val = int(m.group(7))
            
            is_lab = p_val >= 2 or "lab" in title.lower() or "laboratory" in title.lower()
            lab_dur = min(max(p_val, 2), 3) if is_lab else 0
            periods = max(p_val if is_lab else (l_val + t_val), 3)
            
            if current_sem not in semesters:
                semesters[current_sem] = []
                
            # Check duplicate
            if not any(s["subject_code"] == code for s in semesters[current_sem]):
                semesters[current_sem].append({
                    "subject_code": code,
                    "subject_name": title,
                    "abbreviation": generate_abbreviation(title, is_lab),
                    "department": dept,
                    "category": cat,
                    "l": l_val,
                    "t": t_val,
                    "p": p_val,
                    "credits": c_val,
                    "periods_per_week": periods,
                    "is_lab": is_lab,
                    "lab_duration": lab_dur,
                    "difficulty_level": calculate_difficulty(cat, title, float(c_val), is_lab)
                })

    return semesters


def get_regulation_presets() -> Dict[str, Any]:
    """Pre-loaded standard Anna University Curricula across R2021, R2023, R2025."""
    try:
        import curriculum_data
        presets = {}
        # Populate key highlighted presets from R2021, R2023, and R2025
        # R2021
        for key in [
            ("B.E.", "CSE", "Semester 1"),
            ("B.E.", "CSE", "Semester 3"),
            ("B.E.", "CSE", "Semester 4"),
            ("B.E.", "CSE", "Semester 5"),
            ("B.Tech.", "IT", "Semester 3"),
            ("B.Tech.", "AIDS", "Semester 3"),
            ("B.E.", "ECE", "Semester 3"),
            ("B.E.", "EEE", "Semester 3"),
            ("B.E.", "MECH", "Semester 3"),
            ("B.E.", "CIVIL", "Semester 3"),
            ("B.Tech.", "CSBS", "Semester 3"),
            ("B.E.", "CYBER", "Semester 3"),
            ("B.E.", "BME", "Semester 3"),
        ]:
            c = curriculum_data.get_curriculum("R2021", key[0], key[1], key[2])
            if c:
                presets[f"AU R2021 - {key[1]} ({key[2]})"] = c

        # R2023
        for key in [
            ("B.E.", "CSE", "Semester 3"),
            ("B.E.", "CSE", "Semester 4"),
            ("B.Tech.", "IT", "Semester 3"),
            ("B.Tech.", "AIDS", "Semester 3"),
            ("B.E.", "ECE", "Semester 3"),
            ("B.E.", "MECH", "Semester 3"),
        ]:
            c = curriculum_data.get_curriculum("R2023", key[0], key[1], key[2])
            if c:
                presets[f"AU R2023 (Autonomous) - {key[1]} ({key[2]})"] = c

        # R2025
        for key in [
            ("B.E.", "CSE", "Semester 3"),
            ("B.E.", "CSE", "Semester 4"),
            ("B.Tech.", "AIDS", "Semester 3"),
            ("B.E.", "ECE", "Semester 3"),
            ("B.E.", "MECH", "Semester 3"),
        ]:
            c = curriculum_data.get_curriculum("R2025", key[0], key[1], key[2])
            if c:
                presets[f"AU R2025 (AI & Industry 5.0) - {key[1]} ({key[2]})"] = c

        return presets
    except Exception as e:
        return {}
