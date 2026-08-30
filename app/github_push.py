import base64, os, httpx
from pathlib import Path

def push_dir(cfg):
    g=cfg.get('github',{}); token=os.getenv(g.get('token_env','GITHUB_TOKEN'))
    if not g.get('enabled') or not token:return {'ok':False,'skipped':True,'reason':'github disabled or token missing'}
    owner,repo,branch=g['owner'],g['repo'],g.get('branch','main'); prefix=g.get('remote_prefix','live').strip('/')
    headers={'Authorization':f'Bearer {token}','Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
    base=f'https://api.github.com/repos/{owner}/{repo}/contents'; results=[]
    with httpx.Client(timeout=30,headers=headers) as c:
        for p in Path(g.get('output_dir','output')).glob('channels.*'):
            path=f'{prefix}/{p.name}' if prefix else p.name; url=f'{base}/{path}'
            body={'message':f'auto update {p.name}','content':base64.b64encode(p.read_bytes()).decode(),'branch':branch}
            old=c.get(url)
            if old.status_code==200: body['sha']=old.json().get('sha')
            r=c.put(url,json=body); results.append({'file':path,'status':r.status_code,'ok':r.is_success,'message':r.text[:200]})
    return {'ok':all(x['ok'] for x in results),'files':results}
