"""Process-wide SQLAlchemy pool ownership."""

import db


def test_engine_is_singleton_per_url(monkeypatch):
    created = []

    class FakeEngine:
        def dispose(self):
            pass

    def fake_create_engine(url, **kwargs):
        created.append((url, kwargs))
        return FakeEngine()

    db.dispose_database_pools()
    monkeypatch.setenv("DB_URL", "postgresql://unused/fastlms")
    monkeypatch.setattr(db.sa, "create_engine", fake_create_engine)

    assert db.get_engine() is db.get_engine()
    assert len(created) == 1
    assert created[0][1]["pool_size"] == 3
    assert created[0][1]["max_overflow"] == 2
    db.dispose_database_pools()
