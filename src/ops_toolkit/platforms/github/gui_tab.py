"""GitHub 平台的 Tab。每个 action 一个功能区。"""
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from ...ui.platform_tab import PlatformTab
from .client import GitHubClient
from .actions import prune_releases


class GitHubTab(PlatformTab):
    title = "GitHub"
    token_label = "GitHub Token:"
    token_env = "GITHUB_TOKEN"
    group_label = "选择仓库:"

    def make_client(self, token):
        return GitHubClient(token)

    def list_groups(self, client):
        return client.list_repos()      # [(full_name, full_name), ...]

    def build_actions(self, parent):
        # 功能区 1：清理 Release
        self._build_prune_releases(parent)
        # 未来加：self._build_prune_workflow_runs(parent)

    def _build_prune_releases(self, parent):
        box = ttk.LabelFrame(parent, text="清理旧 Release", padding="6")
        box.pack(fill=tk.X, pady=4)

        ttk.Label(box, text="每个仓库保留最新:").grid(row=0, column=0, sticky=tk.W, padx=4)
        self.keep_entry = ttk.Entry(box, width=6)
        self.keep_entry.insert(0, "3")
        self.keep_entry.grid(row=0, column=1, sticky=tk.W)

        ttk.Label(box, text="并发:").grid(row=0, column=2, sticky=tk.W, padx=8)
        self.workers_entry = ttk.Entry(box, width=6)
        self.workers_entry.insert(0, "8")
        self.workers_entry.grid(row=0, column=3, sticky=tk.W)

        self.delete_tag_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(box, text="同时删除 Git tag",
                        variable=self.delete_tag_var).grid(row=0, column=4, padx=12)

        ttk.Button(box, text="执行", command=self._run_prune_releases)\
            .grid(row=0, column=5, padx=8)

    def _run_prune_releases(self):
        if not self.require_client():
            return
        try:
            keep = int(self.keep_entry.get() or 3)
            workers = int(self.workers_entry.get() or 8)
        except ValueError:
            messagebox.showerror("错误", "参数必须是整数")
            return
        delete_tags = self.delete_tag_var.get()

        target_ids = self.selected_group_ids()   # None 或 [full_name]
        if target_ids is not None:
            self.bus.log(f"仅处理选中的仓库。")

        def w():
            try:
                stats = prune_releases.run(
                    self.client, keep, workers, self.bus.log,
                    only_repo_ids=target_ids,
                    delete_tags=delete_tags,
                )
                self.bus.log(f"\n完成：保留 {stats['kept']}，"
                             f"删除 {stats['deleted']}，失败 {stats['failed']}")
            except Exception as e:
                self.bus.log(f"\n异常：{e}")
        threading.Thread(target=w, daemon=True).start()
