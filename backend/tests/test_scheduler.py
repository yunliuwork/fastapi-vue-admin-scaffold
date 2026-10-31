from datetime import timedelta

from sqlalchemy import select

from app.jobs.tasks import clear_expired_login_locks
from app.models.user import User, utcnow


def test_clear_expired_login_locks_resets_stale_lock(client):
    from app.db import session as db_session

    db = db_session.session_factory()
    try:
        user = db.scalar(select(User).where(User.username == "admin"))
        assert user is not None
        user.failed_login_count = 5
        user.locked_until = utcnow() - timedelta(minutes=1)
        db.commit()
    finally:
        db.close()

    clear_expired_login_locks()

    db = db_session.session_factory()
    try:
        user = db.scalar(select(User).where(User.username == "admin"))
        assert user is not None
        assert user.failed_login_count == 0
        assert user.locked_until is None
    finally:
        db.close()
