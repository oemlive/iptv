import json, sqlite3, hashlib
from pathlib import Path
from datetime import datetime, timezone

CATS = ['央视','卫视','港台','其他','网页']

def now(): return datetime.now(timezone.utc).isoformat()
def channel_key(name, group='', category=''):
    s='|'.join(str(x or '').strip().lower() for x in (name,group,category))
    return hashlib.sha1(s.encode('utf-8')).hexdigest()

class Store:
    def __init__(self, db_path, selection_path):
        self.db_path=str(db_path); self.selection_path=Path(selection_path)
        Path(self.db_path).parent.mkdir(parents=True,exist_ok=True)
        self.selection_path.parent.mkdir(parents=True,exist_ok=True)
        with self.conn() as c:
            c.executescript('''
            CREATE TABLE IF NOT EXISTS subscriptions(id INTEGER PRIMARY KEY,name TEXT NOT NULL,url TEXT UNIQUE NOT NULL,enabled INTEGER DEFAULT 1,last_fetch TEXT,last_error TEXT,created_at TEXT);
            CREATE TABLE IF NOT EXISTS sources(id INTEGER PRIMARY KEY,name TEXT,url TEXT UNIQUE,group_name TEXT,category TEXT,logo TEXT,tvg_id TEXT,subscription_id INTEGER,channel_key TEXT,created_at TEXT);
            CREATE TABLE IF NOT EXISTS scans(id INTEGER PRIMARY KEY,source_id INTEGER,name TEXT,url TEXT,category TEXT,status TEXT,http_status INTEGER,latency_ms REAL,probe_ms REAL,protocol TEXT,width INTEGER,height INTEGER,fps REAL,video_codec TEXT,audio_codec TEXT,score REAL,error TEXT,scanned_at TEXT);
            CREATE INDEX IF NOT EXISTS idx_scans_url ON scans(url); CREATE INDEX IF NOT EXISTS idx_sources_sub ON sources(subscription_id); CREATE INDEX IF NOT EXISTS idx_sources_key ON sources(channel_key);
            ''')
            # Safe migration for databases created by earlier FINAL builds.
            cols={r[1] for r in c.execute('PRAGMA table_info(subscriptions)')}
            if 'created_at' not in cols: c.execute('ALTER TABLE subscriptions ADD COLUMN created_at TEXT')
            cols={r[1] for r in c.execute('PRAGMA table_info(sources)')}
            if 'channel_key' not in cols: c.execute('ALTER TABLE sources ADD COLUMN channel_key TEXT')
            cols={r[1] for r in c.execute('PRAGMA table_info(scans)')}
            if 'stability_pct' not in cols: c.execute('ALTER TABLE scans ADD COLUMN stability_pct REAL')
    def conn(self):
        c=sqlite3.connect(self.db_path); c.execute('PRAGMA journal_mode=WAL'); return c
    def add_sub(self,name,url,enabled=True):
        t=now()
        with self.conn() as c:
            c.execute('''INSERT INTO subscriptions(name,url,enabled,created_at) VALUES(?,?,?,?)
                         ON CONFLICT(url) DO UPDATE SET name=excluded.name,enabled=excluded.enabled''',(name,url,1 if enabled else 0,t))
    def remove_sub(self,sub_id):
        with self.conn() as c:
            c.execute('DELETE FROM sources WHERE subscription_id=?',(sub_id,)); c.execute('DELETE FROM subscriptions WHERE id=?',(sub_id,))
    def set_sub_enabled(self,sub_id,enabled):
        with self.conn() as c:c.execute('UPDATE subscriptions SET enabled=? WHERE id=?',(1 if enabled else 0,sub_id))
    def touch_fetch(self,sub_id,error=None):
        with self.conn() as c:c.execute('UPDATE subscriptions SET last_fetch=?,last_error=? WHERE id=?',(now(),error,sub_id))
    def subs(self):
        with self.conn() as c:
            c.row_factory=sqlite3.Row; return [dict(x) for x in c.execute('SELECT * FROM subscriptions ORDER BY id')]
    def import_sources(self,items,subscription_id=None):
        t=now(); n=0
        with self.conn() as c:
            for s in items:
                cat=s.category if hasattr(s,'category') else ''
                key=channel_key(s.name,s.group,cat)
                try:
                    c.execute('''INSERT INTO sources(name,url,group_name,category,logo,tvg_id,subscription_id,channel_key,created_at)
                                 VALUES(?,?,?,?,?,?,?,?,?)''',(s.name,s.url,s.group,cat,s.logo,s.tvg_id,subscription_id,key,t)); n+=1
                except sqlite3.IntegrityError:
                    c.execute('''UPDATE sources SET name=?,group_name=?,logo=?,tvg_id=?,subscription_id=?,channel_key=? WHERE url=?''',(s.name,s.group,s.logo,s.tvg_id,subscription_id,key,s.url))
        return n
    def clear_subscription_sources(self,sub_id):
        with self.conn() as c:c.execute('DELETE FROM sources WHERE subscription_id=?',(sub_id,))
    def set_categories(self,mapping):
        with self.conn() as c:
            for url,cat in mapping.items(): c.execute('UPDATE sources SET category=?,channel_key=? WHERE url=?',(cat,channel_key(self._name(c,url),self._group(c,url),cat),url))
    def _name(self,c,url):
        x=c.execute('SELECT name FROM sources WHERE url=?',(url,)).fetchone(); return x[0] if x else ''
    def _group(self,c,url):
        x=c.execute('SELECT group_name FROM sources WHERE url=?',(url,)).fetchone(); return x[0] if x else ''
    def sources(self,sub_ids=None):
        q='SELECT * FROM sources'; args=[]
        if sub_ids:
            q+=' WHERE subscription_id IN ('+','.join('?'*len(sub_ids))+')'; args=list(sub_ids)
        q+=' ORDER BY CASE category WHEN "央视" THEN 1 WHEN "卫视" THEN 2 WHEN "港台" THEN 3 WHEN "其他" THEN 4 WHEN "网页" THEN 5 ELSE 9 END,name,url'
        with self.conn() as c:
            c.row_factory=sqlite3.Row; return [dict(x) for x in c.execute(q,args)]
    def save_scan(self,r):
        with self.conn() as c:
            keys=list(r.keys()); c.execute('INSERT INTO scans('+','.join(keys)+') VALUES('+','.join('?'*len(keys))+')',[r[k] for k in keys])
    def latest_all(self,sub_ids=None):
        q='''SELECT s.* FROM scans s JOIN (SELECT url,MAX(id) id FROM scans GROUP BY url) x ON x.id=s.id'''; args=[]
        if sub_ids:
            q+=' AND s.source_id IN (SELECT id FROM sources WHERE subscription_id IN ('+','.join('?'*len(sub_ids))+'))'; args=list(sub_ids)
        q+=' ORDER BY CASE s.category WHEN "央视" THEN 1 WHEN "卫视" THEN 2 WHEN "港台" THEN 3 WHEN "其他" THEN 4 WHEN "网页" THEN 5 ELSE 9 END,s.name'
        with self.conn() as c:
            c.row_factory=sqlite3.Row; return [dict(x) for x in c.execute(q,args)]
    def latest(self,sub_ids=None): return [r for r in self.latest_all(sub_ids) if r['status']=='alive']
    def stats(self):
        with self.conn() as c:
            subs=c.execute('SELECT COUNT(*) FROM subscriptions WHERE enabled=1').fetchone()[0]
            src=c.execute('SELECT COUNT(*) FROM sources').fetchone()[0]
            scans=self.latest_all(); alive=sum(r['status']=='alive' for r in scans); dead=len(scans)-alive
            return {'subscriptions':subs,'sources':src,'scanned':len(scans),'alive':alive,'dead':dead}
    def load_selection(self):
        if not self.selection_path.exists(): return {'version':2,'selected_subscriptions':[],'selected_subscription_urls':[],'selected_channels':{},'excluded_channels':{},'default_selected':True,'updated_at':None}
        try:
            d=json.loads(self.selection_path.read_text(encoding='utf-8'))
            d.setdefault('version',2); d.setdefault('selected_subscriptions',[]); d.setdefault('selected_subscription_urls',[]); d.setdefault('selected_channels',{}); d.setdefault('excluded_channels',{}); d.setdefault('default_selected',True); return d
        except Exception:return {'version':2,'selected_subscriptions':[],'selected_subscription_urls':[],'selected_channels':{},'excluded_channels':{},'default_selected':True,'updated_at':None}
    def save_selection(self,data):
        data=dict(data); data['version']=2; data['updated_at']=now()
        tmp=self.selection_path.with_suffix('.tmp'); tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8'); tmp.replace(self.selection_path); return data
