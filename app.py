cat > src/ops_toolkit/app.py << 'EOF'
"""OpsToolkit 主窗口：多 Tab。"""
import os
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

from .core.logger import LogBus
from .core.cleaner import Cleaner
from .platforms.vercel.adapter import VercelAdapter
from .platforms.github.adapter import GitHubAdapter

UI_FONT = ("微软雅黑", 10)
LOG_FONT = ("Consolas", 9)


class PlatformTab(ttk.Frame):
    adapter_class = None
    token_label = "Token:"
    group_label = "选择:"
    keep_label = "保留最新数:"

    def __init__(self, parent):
        super().__init__(parent, padding="10")
        self.bus = LogBus()
        self._build()
        self.after(100, self._drain)

    def _build(self):
        frm = ttk.Frame(self); frm.pack(fill=tk.X)

        ttk.Label(frm, text=self.token_label).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.token_entry = ttk.Entry(frm, width=52, show="*")
        self.token_entry.grid(row=0, column=1, padx=5, pady=5)
        env = os.environ.get(getattr(self.adapter_class, "token_env", ""), "")
        if env:
            self.token_entry.insert(0, env)

        self.fetch_btn = ttk.Button(frm, text="获取列表", command=self._on_fetch)
        self.fetch_btn.grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(frm, text=self.group_label).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.group_combo = ttk.Combobox(frm, width=49, state="readonly")
        self.group_combo.grid(row=1, column=1, padx=5, pady=5)
        self.group_combo["values"] = ["[全部]"]
        self.group_combo.current(0)

        ttk.Label(frm, text=self.keep_label).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.keep_entry = ttk.Entry(frm, width=20)
        self.keep_entry.insert(0, "3")
        self.keep_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(frm, text="并发线程数:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.workers_entry = ttk.Entry(frm, width=20)
        self.workers_entry.insert(0, "8")
        self.workers_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

        self._extra_options(frm, row=4)

        btn = ttk.Frame(self); btn.pack(fill=tk.X, pady=5)
        self.start_btn = ttk.Button(btn, text="开始清理", command=self._on_start)
        self.start_btn.pack(side=tk.LEFT)

        log_frm = ttk.LabelFrame(self, text="运行日志", padding="8")
        log_frm.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frm, height=16, font=LOG_FONT, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _extra_options(self, parent, row):
        pass

    def _make_adapter(self, token):
        return self.adapter_class(token)

    def _drain(self):
        msgs, done = self.bus.drain()
        for m in msgs:
            self.log_text.insert(tk.END, m + "\n")
            self.log_text.see(tk.END)
        if done:
            self.start_btn.config(state=tk.NORMAL, text="开始清理")
        self.after(100, self._drain)

    def _on_fetch(self):
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showerror("错误", "请填写 Token"); return
        self.fetch_btn.config(state=tk.DISABLED, text="获取中...")

        def w():
            try:
                adapter = self._make_adapter(token)
                groups = adapter.list_groups()
                names = [g[1] for g in groups]
                self.bus.log(f"成功获取 {len(names)} 个条目。")
                self.after(0, lambda: self._update_groups(names))
            except Exception as e:
                self.bus.log(f"获取失败: {e}")
            finally:
                self.after(0, lambda: self.fetch_btn.config(state=tk.NORMAL, text="获取列表"))
        threading.Thread(target=w, daemon=True).start()

    def _update_groups(self, names):
        self.group_combo["values"] = ["[全部]"] + names
        self.group_combo.current(0)

    def _on_start(self):
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showerror("错误", "请提供 Token"); return
        selected = self.group_combo.get().strip()
        try:
            keep = int(self.keep_entry.get() or 3)
            workers = int(self.workers_entry.get() or 8)
        except ValueError:
            messagebox.showerror("错误", "参数必须是整数"); return

        self.log_text.delete(1.0, tk.END)
        self.start_btn.config(state=tk.DISABLED, text="清理中...")

        def w():
            try:
                adapter = self._make_adapter(token)
                cleaner = Cleaner(adapter, keep, workers, self.bus.log)
                target = None
                if selected and selected != "[全部]":
                    groups = adapter.list_groups()
                    target = [g[0] for g in groups if g[1] == selected]
                stats = cleaner.run(target)
                self.bus.log(f"\n完成：保留 {stats['kept']}，成功删除 {stats['deleted']}，失败 {stats['failed']}")
            except Exception as e:
                self.bus.log(f"\n异常：{e}")
            finally:
                self.bus.done()
        threading.Thread(target=w, daemon=True).start()


class VercelTab(PlatformTab):
    adapter_class = VercelAdapter
    token_label = "Vercel Token:"
    group_label = "选择项目:"
    keep_label = "每个项目保留最新部署数:"


class GitHubTab(PlatformTab):
    adapter_class = GitHubAdapter
    token_label = "GitHub Token:"
    group_label = "选择仓库:"
    keep_label = "每个仓库保留最新 Release 数:"

    def _extra_options(self, parent, row):
        self.delete_tag_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text="同时删除对应 Git tag（危险）",
                        variable=self.delete_tag_var).grid(
            row=row, column=1, sticky=tk.W, padx=5, pady=5)

    def _make_adapter(self, token):
        return GitHubAdapter(token, delete_tags=self.delete_tag_var.get())


def main():
    root = tk.Tk()
    root.title("OpsToolkit — 多平台运维工具箱")
    root.geometry("880x760")
    style = ttk.Style()
    style.configure("TLabel", font=UI_FONT)
    style.configure("TButton", font=UI_FONT)
    style.configure("TCheckbutton", font=UI_FONT)

    nb = ttk.Notebook(root)
    nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    nb.add(VercelTab(nb), text="Vercel 部署清理")
    nb.add(GitHubTab(nb), text="GitHub Release 清理")

    root.mainloop()


if __name__ == "__main__":
    main()