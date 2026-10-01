"""OpsToolkit 主窗口。"""
import tkinter as tk
from tkinter import ttk

from .platforms.vercel.gui_tab import VercelTab
from .platforms.github.gui_tab import GitHubTab

UI_FONT = ("微软雅黑", 10)


def main():
    root = tk.Tk()
    root.title("OpsToolkit — 多平台运维工具箱")
    root.geometry("900x780")

    style = ttk.Style()
    style.configure("TLabel", font=UI_FONT)
    style.configure("TButton", font=UI_FONT)
    style.configure("TCheckbutton", font=UI_FONT)

    nb = ttk.Notebook(root)
    nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # 注册平台 Tab：加新平台就加一行
    nb.add(VercelTab(nb), text="Vercel")
    nb.add(GitHubTab(nb), text="GitHub")

    root.mainloop()


if __name__ == "__main__":
    main()
