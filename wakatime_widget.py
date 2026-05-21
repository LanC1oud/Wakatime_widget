#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WakaTime 桌面组件
支持今日/历史切换 + 展开收起 + 语言排行榜
"""

import tkinter as tk
from tkinter import font as tkfont
import requests
import base64
import configparser
import os
import threading
from datetime import datetime

# ============ 配置 ============
REFRESH_INTERVAL = 120
WAKATIME_CFG = os.path.expanduser("~/.wakatime.cfg")

BG_COLOR = "#1e1e2e"
FG_COLOR = "#cdd6f4"
ACCENT_COLOR = "#89b4fa"
SECONDARY_FG = "#6c7086"
BAR_BG = "#313244"

LANG_COLORS = {
    "Python": "#ffd43b",
    "JavaScript": "#f7df1e",
    "TypeScript": "#3178c6",
    "Java": "#b07219",
    "Go": "#00add8",
    "Rust": "#dea584",
    "C++": "#f34b7d",
    "C": "#555555",
    "C#": "#178600",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Vue": "#41b883",
    "React": "#61dafb",
    "SQL": "#e38c00",
    "Markdown": "#083fa1",
    "JSON": "#292929",
    "YAML": "#cb171e",
    "Bash": "#89e051",
    "Docker": "#384d54",
}
DEFAULT_BAR_COLOR = "#89b4fa"

# ============ API 工具 ============

def get_api_key():
    if not os.path.exists(WAKATIME_CFG):
        return None
    config = configparser.ConfigParser()
    config.read(WAKATIME_CFG)
    try:
        return config.get("settings", "api_key", fallback=None)
    except Exception:
        return None

def fetch_stats(api_key, range_):
    url = f"https://wakatime.com/api/v1/users/current/stats/{range_}"
    headers = {"Authorization": f"Basic {base64.b64encode(api_key.encode()).decode()}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[API Error] {e}")
        return None

def fetch_today(api_key):
    today = datetime.now().strftime("%Y-%m-%d")
    url = "https://wakatime.com/api/v1/users/current/summaries"
    params = {"start": today, "end": today}
    headers = {"Authorization": f"Basic {base64.b64encode(api_key.encode()).decode()}"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[API Error] {e}")
        return None

def format_duration(seconds):
    if not seconds:
        return "0m"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"

# ============ 小组件 ============

class WakaTimeWidget:
    RANGE_OPTIONS = {
        "今日": "today",
        "最近7天": "last_7_days",
        "最近30天": "last_30_days",
        "最近6个月": "last_6_months",
        "全部时间": "all_time",
    }

    COLLAPSED_H = 150
    EXPANDED_H = 460

    def __init__(self, root):
        self.root = root
        self.root.title("WakaTime")
        self.root.configure(bg=BG_COLOR)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)
        self.root.geometry(f"340x{self.EXPANDED_H}-20+20")

        self.drag_data = {"x": 0, "y": 0}
        self.current_range = "last_7_days"
        self.range_name = "最近7天"
        self.expanded = True

        self.font_title = tkfont.Font(family="Microsoft YaHei UI", size=12)
        self.font_large = tkfont.Font(family="Microsoft YaHei UI", size=26, weight="bold")
        self.font_small = tkfont.Font(family="Microsoft YaHei UI", size=10)
        self.font_tiny = tkfont.Font(family="Microsoft YaHei UI", size=9)
        self.font_range = tkfont.Font(family="Microsoft YaHei UI", size=9, underline=1)

        self._build_ui()
        self._bind_events()

        self.api_key = get_api_key()
        if not self.api_key:
            self.show_error("未找到 API Key")
        else:
            self.update_data()
            self.schedule_refresh()

    def _build_ui(self):
        self.frame = tk.Frame(self.root, bg=BG_COLOR, padx=16, pady=12)
        self.frame.pack(fill="both", expand=True)

        # 标题栏
        self.title_bar = tk.Frame(self.frame, bg=BG_COLOR)
        self.title_bar.pack(fill="x", pady=(0, 4))

        self.title_label = tk.Label(
            self.title_bar, text="WakaTime", font=self.font_title,
            bg=BG_COLOR, fg=SECONDARY_FG,
        )
        self.title_label.pack(side="left")

        self.range_btn = tk.Label(
            self.title_bar, text=self.range_name + " ▾",
            font=self.font_range, bg=BG_COLOR, fg=ACCENT_COLOR, cursor="hand2",
        )
        self.range_btn.pack(side="left", padx=(8, 0))
        self.range_btn.bind("<Button-1>", self.show_range_menu)

        # 收起/展开按钮
        self.toggle_btn = tk.Label(
            self.title_bar, text="▲", font=self.font_title,
            bg=BG_COLOR, fg=SECONDARY_FG, cursor="hand2", padx=4,
        )
        self.toggle_btn.pack(side="right")
        self.toggle_btn.bind("<Button-1>", self.toggle_expand)
        self.toggle_btn.bind("<Enter>", lambda e: self.toggle_btn.config(fg=ACCENT_COLOR))
        self.toggle_btn.bind("<Leave>", lambda e: self.toggle_btn.config(fg=SECONDARY_FG))

        self.close_btn = tk.Label(
            self.title_bar, text="×", font=self.font_title,
            bg=BG_COLOR, fg=SECONDARY_FG, cursor="hand2", padx=4,
        )
        self.close_btn.pack(side="right")
        self.close_btn.bind("<Button-1>", lambda e: (self.root.destroy(), "break")[1])
        self.close_btn.bind("<Enter>", lambda e: self.close_btn.config(fg="#f38ba8"))
        self.close_btn.bind("<Leave>", lambda e: self.close_btn.config(fg=SECONDARY_FG))

        # 总时长
        self.time_label = tk.Label(
            self.frame, text="--", font=self.font_large,
            bg=BG_COLOR, fg=ACCENT_COLOR,
        )
        self.time_label.pack(pady=(4, 8))

        # 语言列表容器（可隐藏）
        self.list_frame = tk.Frame(self.frame, bg=BG_COLOR)
        self.list_frame.pack(fill="both", expand=True)

        # 状态栏
        self.status_label = tk.Label(
            self.frame, text="初始化...", font=self.font_tiny,
            bg=BG_COLOR, fg=SECONDARY_FG,
        )
        self.status_label.pack(side="bottom", anchor="se", pady=(6, 0))

        # 范围菜单
        self.menu_frame = tk.Frame(self.root, bg="#313244", bd=0, highlightthickness=0)
        for name, val in self.RANGE_OPTIONS.items():
            lbl = tk.Label(
                self.menu_frame, text=name, font=self.font_small,
                bg="#313244", fg=FG_COLOR, padx=12, pady=6, cursor="hand2",
            )
            lbl.pack(fill="x")
            lbl.bind("<Enter>", lambda e, w=lbl: w.config(bg="#45475a"))
            lbl.bind("<Leave>", lambda e, w=lbl: w.config(bg="#313244"))
            lbl.bind("<Button-1>", lambda e, v=val, n=name: self.set_range(v, n))

    def toggle_expand(self, event=None):
        self.expanded = not self.expanded
        if self.expanded:
            self.toggle_btn.config(text="▲")
            self.list_frame.pack(fill="both", expand=True)
            h = self.EXPANDED_H
        else:
            self.toggle_btn.config(text="▼")
            self.list_frame.pack_forget()
            h = self.COLLAPSED_H
        self.root.geometry(f"340x{h}")

    def show_range_menu(self, event=None):
        if getattr(self, '_menu_visible', False):
            self._hide_menu()
            return "break"
        self.menu_frame.place(in_=self.frame, x=80, y=40)
        self.menu_frame.lift()
        self._menu_visible = True
        return "break"

    def _hide_menu(self):
        self._menu_visible = False
        self.menu_frame.place_forget()

    def set_range(self, val, name):
        self.current_range = val
        self.range_name = name
        self.range_btn.config(text=name + " ▾")
        self._hide_menu()
        self.update_data()

    def _bind_events(self):
        # 只在 root 绑定一次，避免事件冒泡导致重复触发
        self.root.bind("<Button-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.on_drag)

    def start_drag(self, event):
        w = event.widget
        # 点击功能按钮时不触发拖动/关闭菜单
        if w in (self.range_btn, self.toggle_btn, self.close_btn):
            return
        if getattr(self, '_menu_visible', False):
            try:
                if not str(w).startswith(str(self.menu_frame)):
                    self._hide_menu()
            except Exception:
                self._hide_menu()
        self.drag_data["x"] = event.x_root - self.root.winfo_x()
        self.drag_data["y"] = event.y_root - self.root.winfo_y()

    def on_drag(self, event):
        x = event.x_root - self.drag_data["x"]
        y = event.y_root - self.drag_data["y"]
        self.root.geometry(f"+{x}+{y}")

    def show_error(self, msg):
        self.time_label.config(text="Error", fg="#f38ba8")
        self.status_label.config(text=msg)

    def update_data(self):
        def fetch():
            if self.current_range == "today":
                data = fetch_today(self.api_key)
                self.root.after(0, lambda: self._render_today(data))
            else:
                data = fetch_stats(self.api_key, self.current_range)
                self.root.after(0, lambda: self._render_stats(data))
        threading.Thread(target=fetch, daemon=True).start()

    def _clear_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

    def _render_today(self, data):
        self._clear_list()
        if not data or "data" not in data or not data["data"]:
            self.status_label.config(text="暂无数据")
            return

        summary = data["data"][0]
        total_seconds = summary.get("grand_total", {}).get("total_seconds", 0)
        self.time_label.config(text=format_duration(total_seconds))

        languages = summary.get("languages", [])
        if not languages:
            tk.Label(
                self.list_frame, text="暂无语言数据", font=self.font_small,
                bg=BG_COLOR, fg=SECONDARY_FG,
            ).pack(pady=20)
            self.status_label.config(text="无记录")
            return

        self._draw_bars(languages, total_seconds)
        now = datetime.now().strftime("%H:%M:%S")
        self.status_label.config(text=f"更新于 {now} · {self.range_name}")

    def _render_stats(self, data):
        self._clear_list()
        if not data or "data" not in data or not data["data"]:
            self.status_label.config(text="暂无数据")
            return

        stats = data["data"]
        total_seconds = stats.get("total_seconds", 0)
        self.time_label.config(text=format_duration(total_seconds))

        languages = stats.get("languages", [])
        if not languages:
            tk.Label(
                self.list_frame, text="暂无语言数据", font=self.font_small,
                bg=BG_COLOR, fg=SECONDARY_FG,
            ).pack(pady=20)
            self.status_label.config(text="无记录")
            return

        self._draw_bars(languages, total_seconds)
        now = datetime.now().strftime("%H:%M:%S")
        self.status_label.config(text=f"更新于 {now} · {self.range_name}")

    def _draw_bars(self, languages, total_seconds):
        max_bar_width = 260
        for lang in languages[:8]:
            name = lang.get("name", "Unknown")
            secs = lang.get("total_seconds", 0)
            percent = (secs / total_seconds * 100) if total_seconds else 0
            color = LANG_COLORS.get(name, DEFAULT_BAR_COLOR)

            row = tk.Frame(self.list_frame, bg=BG_COLOR)
            row.pack(fill="x", pady=(0, 8))

            header = tk.Frame(row, bg=BG_COLOR)
            header.pack(fill="x")

            tk.Label(
                header, text=name, font=self.font_tiny,
                bg=BG_COLOR, fg=FG_COLOR,
            ).pack(side="left")

            tk.Label(
                header, text=format_duration(secs), font=self.font_tiny,
                bg=BG_COLOR, fg=SECONDARY_FG,
            ).pack(side="right")

            bar_container = tk.Frame(row, bg=BAR_BG, height=6)
            bar_container.pack(fill="x", pady=(2, 0))
            bar_container.pack_propagate(False)

            bar_width = int(max_bar_width * (percent / 100))
            if bar_width < 1:
                bar_width = 1
            bar = tk.Frame(bar_container, bg=color, height=6)
            bar.place(x=0, y=0, width=bar_width, height=6)

    def schedule_refresh(self):
        self.update_data()
        self.root.after(REFRESH_INTERVAL * 1000, self.schedule_refresh)

# ============ 启动 ============

def main():
    root = tk.Tk()
    app = WakaTimeWidget(root)
    root.mainloop()

if __name__ == "__main__":
    main()
