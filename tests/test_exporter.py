from app.models import Source
from app.exporter import txt,m3u

def test_export():
    x=Source(id='1',name='CCTV-1',url='https://x/a.m3u8',group='央卫',subgroup='央视',valid=True)
    assert 'CCTV-1,https://x/a.m3u8' in txt([x])
    assert '#EXTM3U' in m3u([x]) and 'group-title="央卫/央视"' in m3u([x])


def test_limit_per_channel(tmp_path, monkeypatch):
    import json
    from app import exporter
    cfg = tmp_path / 'config'
    cfg.mkdir()
    (cfg / 'settings.json').write_text(json.dumps({'output': {'max_per_channel': 2}}), encoding='utf-8')
    monkeypatch.chdir(tmp_path)
    items = [Source(id=str(i), name='CCTV1', url=f'http://x/{i}', valid=True, score=10-i) for i in range(5)]
    result = exporter.limit_per_channel(items)
    assert len(result) == 2
    assert result[0].score == 10 and result[1].score == 9
