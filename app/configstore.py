from pathlib import Path
import yaml

def load_subscriptions(path):
    p=Path(path)
    if not p.exists(): return []
    try:
        d=yaml.safe_load(p.read_text(encoding='utf-8')) or {}
        return [x for x in d.get('subscriptions',[]) if x.get('name') and x.get('url')]
    except Exception:
        return []

def save_subscriptions(path,items):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(yaml.safe_dump({'subscriptions':items},allow_unicode=True,sort_keys=False),encoding='utf-8')
