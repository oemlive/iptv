import httpx
from urllib.parse import quote
from .config import settings
from .parser import parse_text, dedupe

EXTS=(".m3u",".m3u8",".txt",".json")

async def github_repositories(query):
    headers={"Accept":"application/vnd.github+json"}
    if settings.github_token: headers["Authorization"]=f"Bearer {settings.github_token}"
    async with httpx.AsyncClient(timeout=20,follow_redirects=True) as c:
        r=await c.get("https://api.github.com/search/repositories",headers=headers,params={"q":query,"sort":"updated","per_page":settings.max_repo_results})
        r.raise_for_status(); return r.json().get("items",[])

async def gitee_repositories(query):
    headers={"Accept":"application/json"}
    if settings.gitee_token: headers["Authorization"]=f"token {settings.gitee_token}"
    async with httpx.AsyncClient(timeout=20,follow_redirects=True) as c:
        # Gitee v5 repository search is public for basic discovery; deployments can vary, so failures are isolated.
        r=await c.get("https://gitee.com/api/v5/search/repositories",headers=headers,params={"q":query,"page":1,"per_page":settings.max_repo_results})
        if r.status_code>=400: return []
        j=r.json(); return j if isinstance(j,list) else j.get("data",[]) if isinstance(j,dict) else []

async def repo_files(provider, repo):
    owner=repo.get("owner",{}).get("login") or repo.get("namespace",{}).get("path")
    name=repo.get("name") or repo.get("path","").split("/")[-1]
    if not owner or not name: return []
    if provider=="github":
        api=f"https://api.github.com/repos/{owner}/{name}/git/trees/{repo.get('default_branch','main')}"
        headers={"Accept":"application/vnd.github+json"}
        if settings.github_token: headers["Authorization"]=f"Bearer {settings.github_token}"
        async with httpx.AsyncClient(timeout=20,follow_redirects=True) as c:
            r=await c.get(api,headers=headers,params={"recursive":"1"})
            if r.status_code>=400: return []
            tree=r.json().get("tree",[]); return [x["path"] for x in tree if x.get("type")=="blob" and x.get("path","").lower().endswith(EXTS)][:settings.max_files_per_repo]
    owner=repo.get("owner",{}).get("login") or repo.get("namespace",{}).get("path") or repo.get("namespace",{}).get("name")
    name=repo.get("name") or repo.get("path","").split("/")[-1]
    branch=repo.get("default_branch") or repo.get("default_branch_name") or "master"
    if not owner or not name: return []
    async with httpx.AsyncClient(timeout=20,follow_redirects=True) as c:
        queue=[""]; paths=[]
        while queue and len(paths)<settings.max_files_per_repo:
            path=queue.pop(0)
            url=f"https://gitee.com/api/v5/repos/{quote(str(owner),safe='')}/{quote(str(name),safe='')}/contents/{quote(path,safe='/')}"
            try:
                r=await c.get(url,params={"ref":branch})
                if r.status_code>=400: break
                arr=r.json() if isinstance(r.json(),list) else [r.json()]
                for item in arr:
                    if item.get("type")=="dir": queue.append(item.get("path",""))
                    elif item.get("type") in ("file","blob") and item.get("path","").lower().endswith(EXTS): paths.append(item["path"])
            except Exception: break
        return paths[:settings.max_files_per_repo]

async def raw_file(provider, repo, path):
    owner=repo.get("owner",{}).get("login") or repo.get("namespace",{}).get("path") or repo.get("namespace",{}).get("name")
    name=repo.get("name") or repo.get("path","").split("/")[-1]
    branch=repo.get("default_branch") or repo.get("default_branch_name") or "master"
    if provider=="github": url=f"https://raw.githubusercontent.com/{owner}/{name}/{branch}/{path}"
    else: url=f"https://gitee.com/api/v5/repos/{quote(str(owner),safe='')}/{quote(str(name),safe='')}/raw/{quote(path,safe='/')}"
    async with httpx.AsyncClient(timeout=15,follow_redirects=True) as c:
        r=await c.get(url)
        if r.status_code!=200 or len(r.content)>settings.max_file_bytes: return []
        return parse_text(r.text,f"{provider}:{owner}/{name}/{path}")

async def search_public(queries,providers):
    out=[]
    for q in queries:
        for provider in providers:
            repos=await (github_repositories(q) if provider=="github" else gitee_repositories(q))
            for repo in repos:
                for path in await repo_files(provider,repo):
                    try: out.extend(await raw_file(provider,repo,path))
                    except Exception: pass
    return dedupe(out)
