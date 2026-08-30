#!/usr/bin/env python3
"""Set the static admin password hash in admin/index.html."""
from pathlib import Path
import hashlib, getpass, re

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/'admin/index.html'
text=FILE.read_text(encoding='utf-8')
p1=getpass.getpass('New admin password: ')
p2=getpass.getpass('Repeat admin password: ')
if not p1 or p1 != p2:
    raise SystemExit('Password is empty or does not match.')
h=hashlib.sha256(p1.encode('utf-8')).hexdigest()
new,n=re.subn(r"DEFAULT_PASSWORD_HASH='[0-9a-f]{64}'", f"DEFAULT_PASSWORD_HASH='{h}'", text, count=1)
if n != 1: raise SystemExit('Password hash placeholder not found.')
FILE.write_text(new,encoding='utf-8')
print('Admin password hash updated.')
