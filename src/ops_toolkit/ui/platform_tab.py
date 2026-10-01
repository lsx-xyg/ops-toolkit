"""所有平台 Tab 的基类：Token + 目标选择 + 日志面板。

子类只需：
  - 覆盖 title / token_env / token_label
  - 实现 make_client(token)
  - 实现 list_groups(client) -> [(id, name), ...]
  - 实现 build_actions(parent)：画该平台的功能区
"""
import os
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

from ..core.logger import LogBus

UI_FONT = ("微软雅黑", 10)
LOG_FONT = ("Consolas", 9)


class PlatformTab(ttk.Frame):
    title = "Platform"
    token_label = "Token:"
    token_env = ""
    group_label = "选择目标:"       # "选择项目" / "选择仓库"

    def __init__(self, parent):
        super().__init__(parent, padding="10")
        self.bus = LogBus()
        self.client = None
        self._group_ids_by_name = {}   # name -> id
        self._build()
        self.after(100, self._drain)

    # ---------- 子类必须实现 ----------
    def make_client(self, token):
        raise NotImplementedError

    def list_groups(self, client):
        """返回 [(id, name), ...]"""
        raise NotImplementedError

    def build_actions(self, parent):
        """画功能区。子类覆盖。"""
        raise NotImplementedError

    # ---------- 骨架 ----------
    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X)

        ttk.Label(top, text=self.token_label).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.token_entry = ttk.Entry(top, width=52, show="*")
        self.token_entry.grid(row=0, column=1, padx=5, pady=5)
        env = os.environ.get(self.token_env, "")
        if env:
            self.token_entry.insert(0, env)

        self.connect_btn = ttk.Button(top, text="连接并拉取", command=self._on_connect)
        self.connect_btn.grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(top, text=self.group_label).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.group_combo = ttk.Combobox(top, width=49, state="readonly")
        self.group_combo.grid(row=1, column=1, padx=5, pady=5)
        self.group_combo["values"] = ["[全部]"]
        self.group_combo.current(0)

        self.refresh_btn = ttk.Button(top, text="刷新列表",
                                      command=self._on_refresh, state=tk.DISABLED)
        self.refresh_btn.grid(row=1, column=2, padx=5, pady=5)

        self.status_label = ttk.Label(top, text="未连接", foreground="gray")
        self.status_label.grid(row=2, column=1, sticky=tk.W, padx=5)

        # 功能区
        actions_frame = ttk.LabelFrame(self, text="功能", padding="8")
        actions_frame.pack(fill=tk.X, pady=8)
        self.build_actions(actions_frame)

        # 日志
        log_frame = ttk.LabelFrame(self, text="运行日志", padding="8")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=16, font=LOG_FONT, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    # ---------- 连接 / 拉列表 ----------
    def _on_connect(self):
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showerror("错误", "请填写 Token")
            return
        self.connect_btn.config(state=tk.DISABLED, text="连接中...")
        self.refresh_btn.config(state=tk.DISABLED)

        def w():
            try:
                self.client = self.make_client(token)
                self.after(0, lambda: self.status_label.config(
                    text="已连接", foreground="green"))
                self.after(0, lambda: self.refresh_btn.config(state=tk.NORMAL))
                self.bus.log(f"[{self.title}] 已连接，正在拉取列表...")
                self._load_groups()
            except Exception as e:
                self.bus.log(f"[{self.title}] 连接失败: {e}")
                self.after(0, lambda: messagebox.showerror("错误", str(e)))
            finally:
                self.after(0, lambda: self.connect_btn.config(state=tk.NORMAL, text="连接并拉取"))

        threading.Thread(target=w, daemon=True).start()

    def _on_refresh(self):
        if self.client is None:
            messagebox.showwarning("提示", "请先点击『连接并拉取』")
            return
        self.refresh_btn.config(state=tk.DISABLED, text="刷新中...")

        def w():
            try:
                self._load_groups()
            finally:
                self.after(0, lambda: self.refresh_btn.config(state=tk.NORMAL, text="刷新列表"))

        threading.Thread(target=w, daemon=True).start()

    def _load_groups(self):
        groups = self.list_groups(self.client)
        self._group_ids_by_name = {name: gid for gid, name in groups}
        names = ["[全部]"] + [name for _, name in groups]
        self.bus.log(f"[{self.title}] 共 {len(groups)} 个目标。")
        self.after(0, lambda: self._update_combo(names))

    def _update_combo(self, names):
        self.group_combo["values"] = names
        self.group_combo.current(0)

    # ---------- 供 action 调用 ----------
    def selected_group_ids(self):
        """返回 None（全部）或 [id]（单个）。"""
        name = self.group_combo.get().strip()
        if not name or name == "[全部]":
            return None
        gid = self._group_ids_by_name.get(name)
        return [gid] if gid else None

    def require_client(self):
        if self.client is None:
            messagebox.showwarning("提示", "请先点击『连接并拉取』")
            return False
        return True

    # ---------- 日志 ----------
    def _drain(self):
        msgs, _ = self.bus.drain()
        for m in msgs:
            self.log_text.insert(tk.END, m + "\n")
            self.log_text.see(tk.END)
        self.after(100, self._drain)
