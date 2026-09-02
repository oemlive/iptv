import json
from pathlib import Path
from scripts.run_crawler import scheduled_due

def test_schedule_disabled():
    assert scheduled_due({"schedule":{"enabled":False,"times":["00:00"]}}) is False

def test_schedule_bad_timezone_falls_back_to_utc(monkeypatch):
    from datetime import datetime, timezone
    class FakeDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026,9,1,2,17,tzinfo=timezone.utc)
    import scripts.run_crawler as rc
    monkeypatch.setattr(rc, 'datetime', FakeDateTime)
    cfg={"schedule":{"enabled":True,"timezone":"Not/AZone","times":["02:17"],"weekdays":[1]}}
    assert scheduled_due(cfg) is True
