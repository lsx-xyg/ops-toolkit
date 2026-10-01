"""功能：清理旧部署（每个项目保留最新 N 个）。"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..models import Deployment


def run(client, keep_latest, max_workers, log, only_project_ids=None):
    projects = client.list_projects()
    if only_project_ids:
        projects = [p for p in projects if p[0] in only_project_ids]

    to_delete = []
    kept = 0
    for pid, pname in projects:
        log(f"\n[{pname}] 拉取部署...")
        raw = client.list_deployments(pid)
        deps = [Deployment(
            id=d["uid"],
            url=d.get("url") or d["uid"],
            created_at=int(d.get("created") or 0) / 1000,
            raw=d,
        ) for d in raw]
        deps.sort(key=lambda d: d.created_at, reverse=True)
        keep, delete = deps[:keep_latest], deps[keep_latest:]
        kept += len(keep)
        log(f"  共 {len(deps)}，保留 {len(keep)}，待删 {len(delete)}")
        to_delete.extend((pname, d) for d in delete)

    if not to_delete:
        log("没有需要删除的部署。")
        return {"kept": kept, "deleted": 0, "failed": 0}

    log(f"\n开始删除（{max_workers} 线程）...")
    ok_n = fail_n = 0
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(client.delete_deployment, d.id): (pname, d) for pname, d in to_delete}
        for i, fut in enumerate(as_completed(futures), 1):
            pname, d = futures[fut]
            ok, err = fut.result()
            if ok:
                ok_n += 1
                log(f"[{i}/{len(to_delete)}] ✓ [{pname}] {d.url}")
            else:
                fail_n += 1
                log(f"[{i}/{len(to_delete)}] ✗ [{pname}] {d.url} -> {err}")
    return {"kept": kept, "deleted": ok_n, "failed": fail_n}
