"""功能：清理旧 Release（每个仓库保留最新 N 个，可选删 tag）。"""
from concurrent.futures import ThreadPoolExecutor, as_completed


def run(client, keep_latest, max_workers, log,
        only_repo_ids=None, delete_tags=False):
    repos = client.list_repos()
    if only_repo_ids:
        repos = [r for r in repos if r[0] in only_repo_ids]

    to_delete = []          # [(full_name, release_obj)]
    kept = 0

    for full_name, _ in repos:
        log(f"\n[{full_name}] 拉取 Release...")
        try:
            releases = client.list_releases(full_name)
        except Exception as e:
            log(f"  ✗ 拉取失败，跳过：{e}")
            continue

        if not releases:
            log("  该仓库没有 Release，跳过。")
            continue

        # PyGithub 已经按创建时间倒序返回，但保险起见再排一次
        releases.sort(key=lambda r: r.created_at, reverse=True)
        keep, delete = releases[:keep_latest], releases[keep_latest:]
        kept += len(keep)

        log(f"  共 {len(releases)}，保留 {len(keep)}，待删 {len(delete)}")
        for r in keep:
            ts = r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "未知"
            log(f"    [保留] {r.tag_name} ({r.title})  ({ts})")

        to_delete.extend((full_name, r) for r in delete)

    if not to_delete:
        log("\n没有需要删除的 Release。")
        return {"kept": kept, "deleted": 0, "failed": 0}

    log(f"\n开始删除（{max_workers} 线程）...")
    ok_n = fail_n = 0
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {
            ex.submit(_delete_one, client, fn, rel, delete_tags): (fn, rel)
            for fn, rel in to_delete
        }
        for i, fut in enumerate(as_completed(futures), 1):
            fn, rel = futures[fut]
            ok, err = fut.result()
            label = f"{rel.tag_name} ({rel.title})"
            if ok and not err:
                ok_n += 1
                log(f"[{i}/{len(to_delete)}] ✓ [{fn}] {label}")
            elif ok and err:
                ok_n += 1
                log(f"[{i}/{len(to_delete)}] ⚠ [{fn}] {label} -> {err}")
            else:
                fail_n += 1
                log(f"[{i}/{len(to_delete)}] ✗ [{fn}] {label} -> {err}")

    return {"kept": kept, "deleted": ok_n, "failed": fail_n}


def _delete_one(client, full_name, release_obj, delete_tags):
    ok, err = client.delete_release(release_obj)
    if not ok:
        return False, err
    if delete_tags and release_obj.tag_name:
        ok2, err2 = client.delete_tag(full_name, release_obj.tag_name)
        if not ok2:
            return True, f"release 已删, tag 删除失败: {err2}"
    return True, None
