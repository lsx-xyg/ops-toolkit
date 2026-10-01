"""所有平台 Tab 的基类：提供 Token 输入、列表刷新、日志面板。

子类只需：
  - 覆盖 title / token_env / token_label
  - 实现 build_actions(parent) —— 返回一个 Frame，里面放该平台所有功能区
  - 实现 make_client(token) —— 返回该平台的 client 实例
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

    def __init__(self, parent):
        super().__init__(parent, padding="10")
        self.bus = LogBus()
        self.client = None
        self._build()
        self.after(100, self._drain)

    # ---------- 子类必须实现 ----------
    def build_actions(self, parent):
        """在 parent 里构建该平台的功能区。子类覆盖。"""
        raise NotImplementedError

    def make_client(self, token):
        """返回该平台的 client 实例。子类覆盖。"""
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

        self.connect_btn = ttk.Button(top, text="连接", command=self._on_connect)
        self.connect_btn.grid(row=0, column=2, padx=5, pady=5)

        self.status_label = ttk.Label(top, text="未连接", foreground="gray")
        self.status_label.grid(row=1, column=1, sticky=tk.W, padx=5)

        # 功能容器（子类填充）
        actions_frame = ttk.LabelFrame(self, text="功能", padding="8")
        actions_frame.pack(fill=tk.X, pady=8)
        self.build_actions(actions_frame)

        # 日志
        log_frame = ttk.LabelFrame(self, text="运行日志", padding="8")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=16, font=LOG_FONT, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _on_connect(self):
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showerror("错误", "请填写 Token")
            return
        self.connect_btn.config(state=tk.DISABLED, text="连接中...")

        def w():
            try:
                self.client = self.make_client(token)
                self.bus.log(f"[{self.title}] 客户端已创建，可执行功能。")
                self.after(0, lambda: self.status_label.config(text="已连接", foreground="green"))
            except Exception as e:
                self.bus.log(f"[{self.title}] 连接失败: {e}")
            finally:
                self.after(0, lambda: self.connect_btn.config(state=tk.NORMAL, text="连接"))

        threading.Thread(target=w, daemon=True).start()

    def _drain(self):
        msgs, _ = self.bus.drain()
        for m in msgs:
            self.log_text.insert(tk.END, m + "\n")
            self.log_text.see(tk.END)
        self.after(100, self._drain)

    def require_client(self):
        if self.client is None:
            messagebox.showwarning("提示", "请先点击『连接』")
            return False
        return True
