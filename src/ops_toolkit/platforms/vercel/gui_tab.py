"""Vercel 平台的 Tab。"""
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from ...ui.platform_tab import PlatformTab
from .client import VercelClient
from .actions import prune_deployments


class VercelTab(PlatformTab):
    title = "Vercel"
    token_label = "Vercel Token:"
    token_env = "VERCEL_TOKEN"

    def make_client(self, token):
        return VercelClient(token)

    def build_actions(self, parent):
        # ---- 功能区 1：清理部署 ----
        box = ttk.LabelFrame(parent, text="清理旧部署", padding="6")
        box.pack(fill=tk.X, pady=4)

        ttk.Label(box, text="每个项目保留最新:").grid(row=0, column=0, sticky=tk.W, padx=4)
        self.keep_entry = ttk.Entry(box, width=6)
        self.keep_entry.insert(0, "3")
        self.keep_entry.grid(row=0, column=1, sticky=tk.W)

        ttk.Label(box, text="并发:").grid(row=0, column=2, sticky=tk.W, padx=8)
        self.workers_entry = ttk.Entry(box, width=6)
        self.workers_entry.insert(0, "8")
        self.workers_entry.grid(row=0, column=3, sticky=tk.W)

        ttk.Button(box, text="执行", command=self._run_prune).grid(row=0, column=4, padx=12)

        # 未来加新功能：在这里再加一个 LabelFrame 和按钮即可

    def _run_prune(self):
        if not self.require_client():
            return
        try:
            keep = int(self.keep_entry.get() or 3)
            workers = int(self.workers_entry.get() or 8)
        except ValueError:
            messagebox.showerror("错误", "参数必须是整数")
            return

        def w():
            try:
                stats = prune_deployments.run(
                    self.client, keep, workers, self.bus.log,
                )
                self.bus.log(f"\n完成：保留 {stats['kept']}，"
                             f"删除 {stats['deleted']}，失败 {stats['failed']}")
            except Exception as e:
                self.bus.log(f"\n异常：{e}")
        threading.Thread(target=w, daemon=True).start()
