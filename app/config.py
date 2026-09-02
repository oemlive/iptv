from dataclasses import dataclass
import json, os
from pathlib import Path

def _int(name, default, lo=0, hi=None):
    try: v=int(os.getenv(name, str(default)))
    except (ValueError, TypeError): v=default
    v=max(lo,v)
    return min(v,hi) if hi is not None else v

def _float(name, default, lo=0.1, hi=None):
    try: v=float(os.getenv(name, str(default)))
    except (ValueError, TypeError): v=default
    v=max(lo,v)
    return min(v,hi) if hi is not None else v

def _load_file():
    p=Path(os.getenv('CONFIG_FILE','config/settings.json'))
    if not p.exists(): return {}
    try: return json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError): return {}

_file=_load_file(); _val=_file.get('validation',{})

@dataclass(frozen=True)
class Settings:
    validate_timeout: float = _float('VALIDATE_TIMEOUT', _val.get('timeout',6), 2, 30)
    min_width: int = _int('MIN_WIDTH', _val.get('min_width',1280), 0, 7680)
    min_height: int = _int('MIN_HEIGHT', _val.get('min_height',720), 0, 4320)
    max_concurrency: int = _int('MAX_CONCURRENCY', _val.get('concurrency',12), 1, 64)
    max_repo_results: int = _int('MAX_REPO_RESULTS',20,1,100)
    max_files_per_repo: int = _int('MAX_FILES_PER_REPO',30,1,200)
    max_file_bytes: int = _int('MAX_FILE_BYTES',2_000_000,10_000,10_000_000)
    stability_seconds: int = _int('STABILITY_SECONDS', _val.get('stability_seconds',0), 0, 60)
    retry_count: int = _int('RETRY_COUNT', _val.get('retry_count',2), 0, 5)
    github_token: str = os.getenv('GITHUB_TOKEN','')
    gitee_token: str = os.getenv('GITEE_TOKEN','')
    database: str = os.getenv('DATABASE','data/live.db')
    data_dir: str = os.getenv('DATA_DIR','data')
    output_dir: str = os.getenv('OUTPUT_DIR','output')
    selected_file: str = os.getenv('SELECTED_FILE','config/selected-sources.json')
    settings_file: str = os.getenv('SETTINGS_FILE','config/settings.json')
settings=Settings()
