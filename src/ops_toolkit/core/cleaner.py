"""通用清理调度：保留每组最新 N 个，其余并发删除。"""
from concurrent.futures import ThreadPoolExecutor, as_completed


class Cleaner:
    def __init__(self, adapter, keep_latest, max_workers, log):
        self.adapter = adapter
        self.keep_latest = keep_latest
        self.max_workers = max_workers
        self.log = log

    def run(self, only_group_ids=None):
        groups = self.adapter.list_groups()
        if only_group_ids:
            groups = [g for g in groups if g[0] in only_group_ids]

        to_delete = []
        kept = 0
        for gid, gname in groups:
            self.log(f"\n[{gname}] 拉取资源...")
            resources = self.adapter.list_resources(gid)
            resources.sort(key=lambda r: r.created_at, reverse=True)
            keep, delete = resources[: self.keep_latest], resources[self.keep_latest:]
            kept += len(keep)
            self.log(f"  共 {len(resources)}，保留 {len(keep)}，待删 {len(delete)}")
            to_delete.extend((gid, gname, r) for r in delete)

        if not to_delete:
            self.log("没有需要删除的资源。")
            return {"kept": kept, "deleted": 0, "failed": 0}

        self.log(f"\n开始删除（{self.max_workers} 线程）...")
        ok_n = fail_n = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            futures = {
                ex.submit(self.adapter.delete_resource, gid, r): (gname, r)
                for gid, gname, r in to_delete
            }
            for i, fut in enumerate(as_completed(futures), 1):
                gname, r = futures[fut]
                ok, err = fut.result()
                if ok and not err:
                    ok_n += 1
                    self.log(f"[{i}/{len(to_delete)}] ✓ [{gname}] {r.label}")
                elif ok and err:
                    ok_n += 1
                    self.log(f"[{i}/{len(to_delete)}] ⚠ [{gname}] {r.label} -> {err}")
                else:
                    fail_n += 1
                    self.log(f"[{i}/{len(to_delete)}] ✗ [{gname}] {r.label} -> {err}")
        return {"kept": kept, "deleted": ok_n, "failed": fail_n}
