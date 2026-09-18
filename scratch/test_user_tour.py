"""
scratch/test_user_tour.py — Automated verification of the interactive user guide tour and trigger logic.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, seed_demo_institution, get_db
from app import app

def test_tour_triggers():
    client = app.test_client()

    print("=== [1] Testing Demo Credentials Login Triggers Interactive Tour ===")
    # Login with DEMO2024 credentials
    with client.session_transaction() as sess:
        sess["_csrf_token"] = "test_csrf_token_value_32chars_1"

    login_resp = client.post("/login", data={
        "csrf_token": "test_csrf_token_value_32chars_1",
        "inst_code": "DEMO2024",
        "username": "admin",
        "password": "admin123"
    }, follow_redirects=True)

    assert login_resp.status_code == 200
    html = login_resp.get_data(as_text=True)

    # Verify tour component and trigger flag
    assert 'data-show-tour="true"' in html, "data-show-tour should be 'true' on demo login"
    assert 'id="schedhubTourOverlay"' in html, "schedhubTourOverlay missing in HTML"
    assert 'id="tourSkipBtn"' in html, "tourSkipBtn missing in HTML"
    assert 'Skip for now' in html, "'Skip for now' button text missing"

    # Verify all 9 side dashboard navigation elements exist in the DOM
    expected_nav_ids = [
        'tour-nav-dashboard',
        'tour-nav-syllabus',
        'tour-nav-staff',
        'tour-nav-subjects',
        'tour-nav-classes',
        'tour-nav-rooms',
        'tour-nav-timetable',
        'tour-nav-analytics',
        'tour-nav-settings'
    ]
    for nav_id in expected_nav_ids:
        assert f'id="{nav_id}"' in html, f"Missing tour target ID: {nav_id}"

    print("[OK] Demo login properly renders interactive tour with all 9 side dashboard targets and 'Skip for now' button.")

    print("\n=== [2] Testing Subsequent Navigation Does Not Retrigger Tour ===")
    refresh_resp = client.get("/dashboard")
    assert refresh_resp.status_code == 200
    refresh_html = refresh_resp.get_data(as_text=True)
    assert 'data-show-tour="false"' in refresh_html, "data-show-tour should be 'false' after initial display"
    print("[OK] Tour is not retriggered on standard navigation/page refreshes.")

    print("\n=== [3] Testing New Institution Registration Triggers Tour ===")
    import time
    new_code = f"NEW{int(time.time()) % 100000}"
    with client.session_transaction() as sess:
        sess.clear()
        sess["_csrf_token"] = "test_csrf_token_value_32chars_2"

    reg_resp = client.post("/register", data={
        "csrf_token": "test_csrf_token_value_32chars_2",
        "inst_name": "Tour University",
        "inst_code": new_code,
        "inst_email": f"tour_{new_code}@college.edu",
        "username": "touradmin",
        "password": "TourPassword2026!",
        "confirm_password": "TourPassword2026!"
    }, follow_redirects=True)

    assert reg_resp.status_code == 200
    reg_html = reg_resp.get_data(as_text=True)
    assert 'data-show-tour="true"' in reg_html, "data-show-tour should be 'true' on new institution registration"
    print("[OK] New institution registration properly triggers the interactive user guide tour.")

    print("\n=== [4] Testing Non-Demo Existing Institution Login Does Not Auto-Trigger Tour ===")
    with client.session_transaction() as sess:
        sess.clear()
        sess["_csrf_token"] = "test_csrf_token_value_32chars_3"

    login_reg_user = client.post("/login", data={
        "csrf_token": "test_csrf_token_value_32chars_3",
        "inst_code": new_code,
        "username": "touradmin",
        "password": "TourPassword2026!"
    }, follow_redirects=True)

    assert login_reg_user.status_code == 200
    nondemo_html = login_reg_user.get_data(as_text=True)
    assert 'data-show-tour="false"' in nondemo_html, "Regular (non-demo) existing login should not trigger tour"
    print("[OK] Regular existing institution login does not auto-trigger tour.")

    print("\n=== [5] Testing Demo Login Triggers Tour Again on Next Login ===")
    with client.session_transaction() as sess:
        sess.clear()
        sess["_csrf_token"] = "test_csrf_token_value_32chars_4"

    login_demo_again = client.post("/login", data={
        "csrf_token": "test_csrf_token_value_32chars_4",
        "inst_code": "DEMO2024",
        "username": "admin",
        "password": "admin123"
    }, follow_redirects=True)

    assert login_demo_again.status_code == 200
    demo_again_html = login_demo_again.get_data(as_text=True)
    assert 'data-show-tour="true"' in demo_again_html, "Demo login MUST trigger tour every time as requested"
    print("[OK] Demo login triggers interactive tour every time.")

    print("\nALL INTERACTIVE USER GUIDE TESTS PASSED SUCCESSFULLY! 100% CLEAN.")

if __name__ == "__main__":
    init_db()
    seed_demo_institution()
    test_tour_triggers()
