"""功能：清理旧 Release（每个仓库保留最新 N 个，可选删 tag）。"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..models import Release


def run(client, keep_latest, max_workers, log,
        only_repo_ids=None, delete_tags=False):
    repos = client.list_repos()
    if only_repo_ids:
        repos = [r for r in repos if r[0] in only_repo_ids]

    to_delete = []
    kept = 0
    for full_name, _ in repos:
        log(f"\n[{full_name}] 拉取 Release...")
        raw = client.list_releases(full_name)
        rels = [Release(
            id=str(r["id"]),
            tag=r.get("tag_name") or "",
            name=r.get("name") or "",
            created_at=r.get("created_at") or "",
            raw=r,
        ) for r in raw]
        rels.sort(key=lambda r: r.created_at, reverse=True)
        keep, delete = rels[:keep_latest], rels[keep_latest:]
        kept += len(keep)
        log(f"  共 {len(rels)}，保留 {len(keep)}，待删 {len(delete)}")
        to_delete.extend((full_name, r) for r in delete)

    if not to_delete:
        log("没有需要删除的 Release。")
        return {"kept": kept, "deleted": 0, "failed": 0}

    log(f"\n开始删除（{max_workers} 线程）...")
    ok_n = fail_n = 0
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_delete_one, client, fn, r, delete_tags): (fn, r)
                   for fn, r in to_delete}
        for i, fut in enumerate(as_completed(futures), 1):
            fn, r = futures[fut]
            ok, err = fut.result()
            if ok and not err:
                ok_n += 1
                log(f"[{i}/{len(to_delete)}] ✓ [{fn}] {r.label}")
            elif ok and err:
                ok_n += 1
                log(f"[{i}/{len(to_delete)}] ⚠ [{fn}] {r.label} -> {err}")
            else:
                fail_n += 1
                log(f"[{i}/{len(to_delete)}] ✗ [{fn}] {r.label} -> {err}")
    return {"kept": kept, "deleted": ok_n, "failed": fail_n}


def _delete_one(client, full_name, release, delete_tags):
    ok, err = client.delete_release(full_name, release.id)
    if not ok:
        return False, err
    if delete_tags and release.tag:
        ok2, err2 = client.delete_tag(full_name, release.tag)
        if not ok2:
            return True, f"release 已删, tag 失败: {err2}"
    return True, None
