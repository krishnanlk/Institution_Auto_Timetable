"""
scratch/test_security_passes.py — Automated verification of OWASP Top 10 security passes.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import hash_password, check_password, is_legacy_hash, get_db, init_db, seed_demo_institution
from auth import (
    auth_limiter, validate_csrf_token, is_safe_url, validate_password_strength,
    get_or_create_csrf_token
)
from app import app

def run_tests():
    print("=== [1] Testing Password Hashing & Legacy Compatibility ===")
    pw = "SecretTest123!"
    h_new = hash_password(pw)
    assert h_new.startswith("pbkdf2:sha256:"), f"Expected pbkdf2 hash, got: {h_new}"
    assert check_password(h_new, pw) is True, "PBKDF2 password check failed"
    assert check_password(h_new, "wrongpass") is False, "Wrong password check succeeded unexpectedly"
    assert is_legacy_hash(h_new) is False, "PBKDF2 identified as legacy"

    # Test legacy format: salt:sha256 (like DEMO college in db)
    legacy_hash = "f2236fe036eb6c8f533c2d7c817715dc:2ca6698c72adc1d1a7d7ac5d9f72df794b0a61bf1c177211cb8ffd32461b9d09"
    assert is_legacy_hash(legacy_hash) is True, "Legacy hash not identified"
    assert check_password(legacy_hash, "admin123") is True, "Legacy hash verification failed"
    assert check_password(legacy_hash, "wrong") is False, "Legacy hash wrong password verified"
    print("[OK] Password hashing & legacy backward-compatibility passed.")

    print("\n=== [2] Testing Open Redirect Defense ===")
    with app.test_request_context("/login", base_url="http://localhost:5000/"):
        assert is_safe_url("/dashboard") is True, "/dashboard should be safe"
        assert is_safe_url("/classes") is True, "/classes should be safe"
        assert is_safe_url("http://localhost:5000/settings") is True, "Same-origin should be safe"
        assert is_safe_url("//evil.com") is False, "Protocol-relative URL should be rejected"
        assert is_safe_url("https://malicious-site.com") is False, "External domain should be rejected"
        assert is_safe_url("javascript:alert(1)") is False, "Javascript scheme should be rejected"
    print("[OK] Open redirect protection passed.")

    print("\n=== [3] Testing Password Strength Policy ===")
    assert validate_password_strength("short")[0] is False, "Too short should fail"
    assert validate_password_strength("alllowercaseletters")[0] is False, "No numbers/symbols should fail"
    assert validate_password_strength("1234567890")[0] is False, "No letters should fail"
    assert validate_password_strength("StrongPass2026")[0] is True, "Valid password should pass"
    print("[OK] Password strength policy passed.")

    print("\n=== [4] Testing Rate Limiter & Lockout Mechanism ===")
    test_key = "test_ip_127.0.0.99"
    auth_limiter.reset(test_key)
    for i in range(4):
        locked, _ = auth_limiter.record_failure(test_key)
        assert not locked, f"Should not lock on attempt {i+1}"
    # 5th attempt triggers lockout
    locked, remaining = auth_limiter.record_failure(test_key)
    assert locked is True, "Should lock on 5th attempt"
    assert remaining > 0, "Remaining cooldown seconds should be > 0"
    is_locked, rem2 = auth_limiter.is_locked(test_key)
    assert is_locked is True, "is_locked should return True during cooldown"
    auth_limiter.reset(test_key)
    assert auth_limiter.is_locked(test_key)[0] is False, "Reset should clear lockout"
    print("[OK] Rate limiter & account lockout passed.")

    print("\n=== [5] Testing Flask HTTP Client: Headers & CSRF Defense ===")
    client = app.test_client()

    # GET /login: Check security headers and presence of CSRF token
    resp = client.get("/login")
    assert resp.status_code == 200
    assert resp.headers.get("X-Frame-Options") == "SAMEORIGIN", "Missing X-Frame-Options"
    assert resp.headers.get("X-Content-Type-Options") == "nosniff", "Missing X-Content-Type-Options"
    assert "Content-Security-Policy" in resp.headers, "Missing Content-Security-Policy"
    html = resp.get_data(as_text=True)
    assert 'name="csrf_token"' in html, "CSRF token missing in login form HTML"
    print("[OK] Security headers and CSRF token injected into login page.")

    # Unauthenticated /api/debug-db should be blocked
    resp_debug = client.get("/api/debug-db")
    assert resp_debug.status_code in (302, 401), f"Expected 302/401 for /api/debug-db, got {resp_debug.status_code}"
    print("[OK] /api/debug-db successfully secured against unauthenticated enumeration.")

    # POST /login without CSRF token should be rejected
    post_no_csrf = client.post("/login", data={
        "inst_code": "DEMO2024",
        "username": "admin",
        "password": "admin123"
    })
    assert "Security validation failed" in post_no_csrf.get_data(as_text=True)
    print("[OK] Missing CSRF token rejected successfully.")

    # POST /login with valid CSRF token & credentials
    with client.session_transaction() as sess:
        sess["_csrf_token"] = "valid_test_csrf_token_value_32chars"
        csrf_val = "valid_test_csrf_token_value_32chars"

    post_success = client.post("/login", data={
        "csrf_token": csrf_val,
        "inst_code": "DEMO2024",
        "username": "admin",
        "password": "admin123"
    }, follow_redirects=False)

    assert post_success.status_code == 302, f"Expected 302 redirect on login, got {post_success.status_code}"
    assert "/dashboard" in post_success.headers.get("Location", "")
    print("[OK] Valid login redirected cleanly to /dashboard.")

    # Verify session cookie properties
    cookies = post_success.headers.getlist("Set-Cookie")
    assert any("HttpOnly" in c for c in cookies), "Session cookie missing HttpOnly flag"
    assert any("SameSite=Lax" in c for c in cookies), "Session cookie missing SameSite flag"
    print("[OK] Session cookie security flags (HttpOnly, SameSite=Lax) verified.")

    print("\nALL SECURITY TESTS PASSED SUCCESSFULLY! 100% CLEAN.")

if __name__ == "__main__":
    init_db()
    seed_demo_institution()
    run_tests()
