from __future__ import annotations
from pathlib import Path
import json
from app.parser import parse_subscription_catalog

CATALOG_VERSION = 1

def catalog_path(base: Path) -> Path:
    return base / 'output' / 'subscriptions.json'

def load_catalog(base: Path) -> dict:
    p = catalog_path(base)
    if not p.exists():
        return {'version': CATALOG_VERSION, 'sources': []}
    try:
        d = json.loads(p.read_text(encoding='utf-8'))
        d.setdefault('version', CATALOG_VERSION)
        d.setdefault('sources', [])
        return d
    except Exception:
        return {'version': CATALOG_VERSION, 'sources': []}

def save_catalog(base: Path, sources: list[dict]) -> dict:
    p = catalog_path(base)
    p.parent.mkdir(parents=True, exist_ok=True)
    clean=[]; seen=set()
    for s in sources:
        u=str(s.get('url') or '').strip()
        if not u or u in seen: continue
        seen.add(u)
        clean.append({
            'name': str(s.get('name') or u).strip(),
            'url': u,
            'enabled': bool(s.get('enabled', True)),
            'headers': s.get('headers') or {},
            'source_name': str(s.get('source_name') or '').strip(),
            'player_type': s.get('player_type'),
            'epg': s.get('epg') or '',
            'logo': s.get('logo') or '',
        })
    payload={'version':CATALOG_VERSION,'count':len(clean),'sources':clean}
    p.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    return payload
