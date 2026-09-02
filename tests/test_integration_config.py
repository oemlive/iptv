import json
from pathlib import Path
import re


def test_schedule_is_5_minute_compatible():
    workflow=Path('.github/workflows/crawl.yml').read_text(encoding='utf-8')
    assert "cron: '*/5 * * * *'" in workflow
    cfg=json.loads(Path('config/settings.json').read_text(encoding='utf-8'))
    for t in cfg['schedule']['times']:
        assert re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', t)
        assert int(t[3:]) % 5 == 0


def test_no_nested_pages_directory():
    workflow=Path('.github/workflows/pages.yml').read_text(encoding='utf-8')
    assert 'cp -r web/. _site/' in workflow
    assert '_site/iptv' not in workflow


def test_frontend_never_persists_github_token():
    js=Path('web/app.js').read_text(encoding='utf-8')
    assert 'localStorage.setItem' in js
    assert "localStorage.setItem('iptv-token'" not in js
    assert 'sessionStorage.setItem' not in js
