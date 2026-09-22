"""
realtime.py — In-Memory Pub/Sub & Cell Edit Locking Engine for SchedHub.
Provides thread-safe Server-Sent Events (SSE) broadcasting and collaborative lock management.
No external broker (Redis/RabbitMQ) required — works identically in local dev and cloud environments.
"""
import time
import json
import threading
import queue
from typing import Optional, Dict, Any, List

# ══════════════════════════════════════════════════════════════════════════════
# SSE Real-Time Pub/Sub Broadcaster
# ══════════════════════════════════════════════════════════════════════════════

class RealtimeBroadcaster:
    """Thread-safe multi-tenant pub/sub hub for Server-Sent Events."""
    def __init__(self):
        self._lock = threading.Lock()
        # Mapping: institution_id -> set of queue.Queue
        self._subscribers: Dict[int, List[queue.Queue]] = {}

    def subscribe(self, institution_id: int) -> queue.Queue:
        """Register a new client connection for SSE streaming."""
        q = queue.Queue(maxsize=100)
        with self._lock:
            if institution_id not in self._subscribers:
                self._subscribers[institution_id] = []
            self._subscribers[institution_id].append(q)
        return q

    def unsubscribe(self, institution_id: int, q: queue.Queue):
        """Cleanly unregister a disconnected client queue."""
        with self._lock:
            if institution_id in self._subscribers:
                try:
                    self._subscribers[institution_id].remove(q)
                except ValueError:
                    pass
                if not self._subscribers[institution_id]:
                    del self._subscribers[institution_id]

    def publish(self, institution_id: int, event_type: str, data: Any):
        """Broadcast an event payload to all active clients of an institution."""
        payload = {
            "event": event_type,
            "data": data,
            "timestamp": int(time.time())
        }
        with self._lock:
            queues = list(self._subscribers.get(institution_id, []))

        for q in queues:
            try:
                q.put_nowait(payload)
            except queue.Full:
                # Discard oldest message if queue is full
                try:
                    q.get_nowait()
                    q.put_nowait(payload)
                except Exception:
                    pass

    @staticmethod
    def format_sse(event_type: str, data: Any) -> str:
        """Format data into valid text/event-stream specification."""
        json_str = json.dumps(data) if not isinstance(data, str) else data
        return f"event: {event_type}\ndata: {json_str}\n\n"


realtime_hub = RealtimeBroadcaster()


# ══════════════════════════════════════════════════════════════════════════════
# Timetable Cell Edit Locking Manager
# ══════════════════════════════════════════════════════════════════════════════

class CellLockManager:
    """
    Manages temporary collaborative cell edit locks with automatic 60-second TTL.
    Prevents dual-coordinators from overwriting each other simultaneously while allowing
    Master Admin override and automatic expiry on tab disconnect.
    """
    DEFAULT_TTL = 60  # seconds

    def __init__(self):
        self._lock = threading.Lock()
        # Key: (institution_id, slot_id) -> dict(user_id, username, role, expires_at)
        self._locks: Dict[tuple, dict] = {}

    def _clean_expired(self):
        now = time.time()
        expired = [k for k, v in self._locks.items() if v["expires_at"] < now]
        for k in expired:
            del self._locks[k]

    def acquire(self, institution_id: int, slot_id: int, user_id: int, username: str, role: str) -> tuple[bool, dict]:
        """
        Attempt to acquire a cell lock. Returns (success, lock_info).
        If already locked by same user, renews TTL.
        If locked by another user, fails.
        """
        now = time.time()
        key = (institution_id, slot_id)
        with self._lock:
            self._clean_expired()
            existing = self._locks.get(key)
            if existing and existing["expires_at"] >= now:
                if existing["user_id"] == user_id:
                    # Renew lock
                    existing["expires_at"] = now + self.DEFAULT_TTL
                    return True, existing
                else:
                    return False, existing

            # Acquire new lock
            lock_info = {
                "slot_id": slot_id,
                "user_id": user_id,
                "username": username,
                "role": role,
                "expires_at": now + self.DEFAULT_TTL,
                "remaining_seconds": self.DEFAULT_TTL
            }
            self._locks[key] = lock_info
            return True, lock_info

    def release(self, institution_id: int, slot_id: int, user_id: int) -> bool:
        """Release lock held by user."""
        key = (institution_id, slot_id)
        with self._lock:
            self._clean_expired()
            existing = self._locks.get(key)
            if existing and (existing["user_id"] == user_id or existing["role"] == "admin"):
                del self._locks[key]
                return True
            return False

    def override(self, institution_id: int, slot_id: int, admin_id: int, admin_name: str) -> tuple[bool, Optional[dict]]:
        """Master Admin emergency lock override. Releases old lock and acquires new one."""
        now = time.time()
        key = (institution_id, slot_id)
        with self._lock:
            old_lock = self._locks.get(key)
            lock_info = {
                "slot_id": slot_id,
                "user_id": admin_id,
                "username": admin_name,
                "role": "admin",
                "expires_at": now + self.DEFAULT_TTL,
                "override_of": old_lock.get("username") if old_lock else None
            }
            self._locks[key] = lock_info
            return True, old_lock

    def get_active_locks(self, institution_id: int) -> Dict[int, dict]:
        """Return all active, non-expired locks for an institution."""
        now = time.time()
        with self._lock:
            self._clean_expired()
            res = {}
            for (iid, sid), v in self._locks.items():
                if iid == institution_id and v["expires_at"] >= now:
                    res[sid] = {
                        **v,
                        "remaining_seconds": max(0, int(v["expires_at"] - now))
                    }
            return res


cell_lock_manager = CellLockManager()
