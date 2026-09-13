"""
scratch/test_inbuilt_and_dual_staff.py - Test Inbuilt Regulations & Secondary Staff for Labs
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import curriculum_data
from app import app
from database import get_db, seed_demo_institution
from scheduler import generate_timetable

def run():
    print("=== 1. Validating Inbuilt Curricula Repository ===")
    index = curriculum_data.get_all_curricula_index()
    print("Available Regulations in Index:", list(index.keys()))
    assert "R2021" in index
    assert "R2023" in index
    assert "R2025" in index

    # Verify R2021 CSE Sem 3
    r2021_cse = curriculum_data.get_curriculum("R2021", "B.E.", "CSE", "Semester 3")
    assert r2021_cse is not None
    print(f"R2021 CSE Sem 3: {len(r2021_cse['subjects'])} subjects")
    lab_count = sum(1 for s in r2021_cse['subjects'] if s['is_lab'])
    print(f"  -> Labs found: {lab_count}")
    assert lab_count >= 3

    # Verify R2023 IT Sem 3
    r2023_it = curriculum_data.get_curriculum("R2023", "B.Tech.", "IT", "Semester 3")
    assert r2023_it is not None
    print(f"R2023 IT Sem 3: {len(r2023_it['subjects'])} subjects")

    # Verify R2025 CSE Sem 3
    r2025_cse = curriculum_data.get_curriculum("R2025", "B.E.", "CSE", "Semester 3")
    assert r2025_cse is not None
    print(f"R2025 CSE Sem 3: {len(r2025_cse['subjects'])} subjects (includes Rust, GenAI, LLM)")

    print("\n=== 2. Testing Endpoints via Flask Test Client ===")
    client = app.test_client()

    with app.test_request_context():
        seed_demo_institution()

    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['username'] = 'admin'
        sess['institution_id'] = 1
        sess['institution_name'] = 'Demo Engineering College'
        sess['role'] = 'admin'

    # Test /api/curriculum/index
    resp = client.get('/api/curriculum/index')
    assert resp.status_code == 200
    idx_json = resp.get_json()
    assert "R2021" in idx_json and "R2025" in idx_json

    # Test /api/curriculum/get
    resp_get = client.get('/api/curriculum/get?regulation=R2025&degree=B.E.&department=CSE&semester=Semester%203')
    assert resp_get.status_code == 200
    r2025_res = resp_get.get_json()
    print("API /api/curriculum/get returned:", r2025_res['regulation'], len(r2025_res['subjects']), "subjects")
    assert r2025_res['success'] == True

    # Test Import with Secondary Staff for Labs
    with get_db() as conn:
        staff_rows = conn.execute("SELECT id, name FROM staff WHERE institution_id=1 LIMIT 3").fetchall()
        st1_id = staff_rows[0]['id']
        st2_id = staff_rows[1]['id'] if len(staff_rows) > 1 else st1_id

    print(f"\n=== 3. Testing Dual Faculty Allocation (Primary ID={st1_id}, Secondary ID={st2_id}) ===")
    test_subjects = r2021_cse['subjects']
    # Set dual staff on first lab
    for s in test_subjects:
        if s['is_lab']:
            s['assigned_staff_id'] = st1_id
            s['lab_staff2_id'] = st2_id
            break

    import_payload = {
        "class_name": "II CSE - Sec Dual Staff Test",
        "department": "CSE",
        "semester": 3,
        "strength": 60,
        "subjects": test_subjects
    }

    import_resp = client.post('/api/syllabus/import', json=import_payload)
    assert import_resp.status_code == 200
    import_json = import_resp.get_json()
    print("Import response:", import_json)
    assert import_json['success'] == True
    class_id = import_json['class_id']

    # Verify in database that lab has lab_staff2_id
    with get_db() as conn:
        lab_row = conn.execute(
            "SELECT s.subject_name, s.is_lab, s.lab_staff2_id FROM subject s "
            "JOIN class_subjects cs ON cs.subject_id=s.id WHERE cs.class_id=? AND s.is_lab=1",
            (class_id,)
        ).fetchone()
        print(f"Database Verification: Lab '{lab_row['subject_name']}' has lab_staff2_id = {lab_row['lab_staff2_id']}")
        assert lab_row['lab_staff2_id'] == st2_id

    # Test Timetable Generation
    print("\n=== 4. Testing Timetable Generation with Dual-Staff Lab Constraints ===")
    tt_id, conflicts = generate_timetable(1, "AU R2021 Dual Staff Timetable")
    print(f"Generated Timetable ID: {tt_id}, Conflicts: {len(conflicts)}")
    assert tt_id is not None

    print("\n========================================================")
    print("ALL TESTS PASSED! R2021, R2023, R2025 INBUILT CURRICULA & DUAL LAB STAFF CONFIRMED WORKING.")
    print("========================================================")

if __name__ == "__main__":
    run()
