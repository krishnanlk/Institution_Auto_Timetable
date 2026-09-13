"""
scratch/test_syllabus_pipeline.py - Comprehensive End-to-End Verification Test
"""
import io
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import syllabus_parser
from app import app
from database import get_db, seed_demo_institution


def generate_sample_anna_univ_pdf() -> bytes:
    """Generate a realistic Anna University Regulation 2021 PDF in memory."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=14,
        leading=18,
        alignment=1, # Center
        textColor=colors.HexColor("#1e1b4b")
    )
    sub_style = ParagraphStyle(
        'SubStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#4b5563")
    )

    story.append(Paragraph("<b>ANNA UNIVERSITY, CHENNAI</b>", title_style))
    story.append(Paragraph("<b>REGULATION 2021 - CHOICE BASED CREDIT SYSTEM</b>", sub_style))
    story.append(Paragraph("<b>B.E. COMPUTER SCIENCE AND ENGINEERING</b>", sub_style))
    story.append(Spacer(1, 15))

    story.append(Paragraph("<b>SEMESTER III (CURRICULUM)</b>", styles['Heading3']))
    story.append(Spacer(1, 8))

    table_data = [
        ["S.No", "Course Code", "Course Title", "Category", "Contact Periods", "L", "T", "P", "C"],
        ["1", "MA3354", "Discrete Mathematics", "BSC", "4", "3", "1", "0", "4"],
        ["2", "CS3351", "Digital Principles and Computer Organization", "ESC", "4", "3", "0", "2", "4"],
        ["3", "CS3352", "Foundations of Data Science", "PCC", "3", "3", "0", "0", "3"],
        ["4", "CS3301", "Data Structures", "PCC", "3", "3", "0", "0", "3"],
        ["5", "CS3391", "Object Oriented Programming", "PCC", "3", "3", "0", "0", "3"],
        ["6", "CS3381", "Data Structures Laboratory", "PCC", "4", "0", "0", "4", "2"],
        ["7", "CS3361", "Object Oriented Programming Laboratory", "PCC", "4", "0", "0", "4", "2"],
        ["8", "GE3361", "Professional Development", "EEC", "2", "0", "0", "2", "1"]
    ]

    t = Table(table_data, colWidths=[30, 70, 220, 50, 50, 25, 25, 25, 25])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (2,1), (2,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#f8fafc"), colors.white])
    ]))

    story.append(t)
    doc.build(story)
    buf.seek(0)
    return buf.read()

def run_tests():
    print("=== 1. Generating Sample Anna University Regulation PDF ===")
    pdf_bytes = generate_sample_anna_univ_pdf()
    print(f"Generated PDF size: {len(pdf_bytes)} bytes")

    print("\n=== 2. Testing syllabus_parser.parse_syllabus_pdf() ===")
    res = syllabus_parser.parse_syllabus_pdf(pdf_bytes)
    print("Parser Result:")
    print(f"  Success: {res.get('success')}")
    print(f"  Regulation: {res.get('regulation')}")
    print(f"  Department: {res.get('department')}")
    print(f"  Semesters parsed: {list(res.get('semesters', {}).keys())}")
    
    sem3_subs = res.get('semesters', {}).get('Semester 3', [])
    print(f"  Found {len(sem3_subs)} subjects in Semester 3:")
    for s in sem3_subs:
        print(f"    - [{s['subject_code']}] {s['subject_name']} (L={s['l']}, P={s['p']}, C={s['credits']}, is_lab={s['is_lab']}, Diff={s['difficulty_level']})")

    assert res.get('success') == True
    assert len(sem3_subs) >= 7

    print("\n=== 3. Testing Flask Endpoints with Test Client ===")
    client = app.test_client()

    # Login to demo institution
    with app.test_request_context():
        seed_demo_institution()

    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['username'] = 'admin'
        sess['institution_id'] = 1
        sess['institution_name'] = 'Demo Engineering College'
        sess['role'] = 'admin'

    # Test PDF Upload endpoint
    data = {
        'syllabus_pdf': (io.BytesIO(pdf_bytes), 'anna_univ_r2021_cse.pdf')
    }
    parse_resp = client.post('/api/syllabus/parse', data=data, content_type='multipart/form-data')
    print(f"POST /api/syllabus/parse Status: {parse_resp.status_code}")
    parse_json = parse_resp.get_json()
    assert parse_json['success'] == True

    # Test Import Endpoint
    import_payload = {
        "class_name": "II CSE - Sec A (Live Test)",
        "department": "CSE",
        "semester": 3,
        "strength": 60,
        "subjects": sem3_subs
    }
    import_resp = client.post('/api/syllabus/import', json=import_payload)
    print(f"POST /api/syllabus/import Status: {import_resp.status_code}")
    import_json = import_resp.get_json()
    print("Import Response:", import_json)
    assert import_json['success'] == True
    class_id = import_json['class_id']

    # Test Timetable Generation with newly imported Class
    from scheduler import generate_timetable
    print("\n=== 4. Testing Timetable Generation with Imported Curriculum ===")
    tt_id, conflicts = generate_timetable(1, "Live Anna Univ Test Timetable")
    print(f"Timetable Generated Successfully! Timetable ID={tt_id}, Total Conflicts={len(conflicts)}")
    assert tt_id is not None


    print("\n==========================================")
    print("ALL TESTS PASSED! PDF IMPORT & SCHEDULING WORK SEAMLESSLY IN REAL TIME.")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
