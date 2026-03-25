import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, List, Optional

try:
    import ttkbootstrap as tb
except ImportError:
    tb = None

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui_state import LogBuffer, NavigationState, ThemeState
from main import LiveRecorderApp
from platform_parser import PlatformParser


class DashboardGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SocialMediaCut 控制台")
        self.root.geometry("1360x860")
        self.root.minsize(1180, 760)

        self.app = LiveRecorderApp()
        self.rooms_cache: Dict[str, Dict] = {}
        self.previous_room_states: Dict[str, Dict[str, bool]] = {}
        self.selected_room_key: Optional[str] = None
        self.refresh_timer = None

        self.theme_state = ThemeState(mode="dark", light_theme="flatly", dark_theme="cyborg")
        self.navigation_state = NavigationState(["overview", "rooms", "logs"], "overview")
        self.log_buffer = LogBuffer(max_events=1200)

        self.pages: Dict[str, ttk.Frame] = {}
        self.nav_buttons: Dict[str, tb.Button] = {}

        self._init_vars()
        self._setup_styles()
        self._build_shell()
        self._switch_page("overview")

        self._refresh_room_data(log_events=False)
        self._schedule_auto_refresh()
        self._schedule_log_drain()
        self._log("INFO", "控制台已启动", source="SYSTEM")

    def _init_vars(self):
        self.status_var = tk.StringVar(value="就绪")
        self.count_var = tk.StringVar(value="房间: 0 | 在线: 0 | 录制: 0")

        self.kpi_total_var = tk.StringVar(value="0")
        self.kpi_live_var = tk.StringVar(value="0")
        self.kpi_recording_var = tk.StringVar(value="0")
        self.kpi_monitor_var = tk.StringVar(value="未启动")

        self.filter_platform_var = tk.StringVar(value="全部")
        self.filter_status_var = tk.StringVar(value="全部")

        self.dark_mode_var = tk.BooleanVar(value=True)
        self.log_level_var = tk.StringVar(value="ALL")

        self.detail_vars = {
            "platform": tk.StringVar(value="-"),
            "room_id": tk.StringVar(value="-"),
            "name": tk.StringVar(value="-"),
            "streamer": tk.StringVar(value="-"),
            "live": tk.StringVar(value="-"),
            "recording": tk.StringVar(value="-"),
            "auto": tk.StringVar(value="-"),
            "title": tk.StringVar(value="-"),
        }

    def _setup_styles(self):
        style = tb.Style()
        style.theme_use(self.theme_state.current_theme)
        style.configure("Dashboard.Treeview", rowheight=30, font=("Microsoft YaHei UI", 10))
        style.configure("Dashboard.Treeview.Heading", font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 18, "bold"))
        style.configure("Subtitle.TLabel", font=("Microsoft YaHei UI", 10))
        style.configure("NavTitle.TLabel", font=("Microsoft YaHei UI", 11, "bold"))
        style.configure("CardTitle.TLabel", font=("Microsoft YaHei UI", 10))
        style.configure("CardValue.TLabel", font=("Microsoft YaHei UI", 24, "bold"))

    def _build_shell(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self._build_topbar()
        self._build_main()
        self._build_statusbar()

    def _build_topbar(self):
        top = ttk.Frame(self.root, padding=(14, 12))
        top.grid(row=0, column=0, sticky="ew")
        top.grid_columnconfigure(1, weight=1)

        title_box = ttk.Frame(top)
        title_box.grid(row=0, column=0, sticky="w")
        ttk.Label(title_box, text="SocialMediaCut 监控控制台", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(title_box, text="科技仪表盘 | 直播监控与录制", style="Subtitle.TLabel").grid(row=1, column=0, sticky="w")

        theme_box = ttk.Frame(top)
        theme_box.grid(row=0, column=2, sticky="e")
        ttk.Label(theme_box, text="主题").grid(row=0, column=0, padx=(0, 8))
        self.theme_switch = ttk.Checkbutton(
            theme_box,
            text="深色模式",
            variable=self.dark_mode_var,
            command=self._on_theme_toggle,
        )
        self.theme_switch.grid(row=0, column=1, sticky="e")

    def _build_main(self):
        main = ttk.Frame(self.root, padding=(14, 0, 14, 10))
        main.grid(row=1, column=0, sticky="nsew")
        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)

        self._build_sidebar(main)
        self._build_content_container(main)

    def _build_sidebar(self, parent):
        sidebar = ttk.Frame(parent, padding=(10, 12))
        sidebar.grid(row=0, column=0, sticky="nsw", padx=(0, 12))
        sidebar.grid_columnconfigure(0, weight=1)
        ttk.Label(sidebar, text="导航", style="NavTitle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))

        nav_items = [
            ("overview", "监控总览"),
            ("rooms", "房间管理"),
            ("logs", "系统日志"),
        ]
        for idx, (key, text) in enumerate(nav_items, start=1):
            button = tb.Button(
                sidebar,
                text=text,
                bootstyle="secondary-outline",
                command=lambda page=key: self._switch_page(page),
                width=16,
            )
            button.grid(row=idx, column=0, sticky="ew", pady=4)
            self.nav_buttons[key] = button

    def _build_content_container(self, parent):
        container = ttk.Frame(parent)
        container.grid(row=0, column=1, sticky="nsew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.pages["overview"] = self._build_overview_page(container)
        self.pages["rooms"] = self._build_rooms_page(container)
        self.pages["logs"] = self._build_logs_page(container)

        for frame in self.pages.values():
            frame.grid(row=0, column=0, sticky="nsew")

    def _build_overview_page(self, parent):
        page = ttk.Frame(parent)
        page.grid_rowconfigure(2, weight=1)
        page.grid_columnconfigure(0, weight=1)

        kpi = ttk.Frame(page)
        kpi.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        for col in range(4):
            kpi.grid_columnconfigure(col, weight=1)
        self._create_kpi_card(kpi, 0, "房间总数", "Rooms", self.kpi_total_var)
        self._create_kpi_card(kpi, 1, "在线数量", "Live", self.kpi_live_var)
        self._create_kpi_card(kpi, 2, "录制中", "Recording", self.kpi_recording_var)
        self._create_kpi_card(kpi, 3, "监控状态", "Monitor", self.kpi_monitor_var)

        quick = ttk.LabelFrame(page, text="快捷操作", padding=12)
        quick.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.btn_quick_monitor = tb.Button(quick, text="启动监控", bootstyle="warning", command=self._on_toggle_monitor)
        self.btn_quick_monitor.grid(row=0, column=0, padx=(0, 8))
        tb.Button(quick, text="刷新数据", bootstyle="secondary", command=self._refresh_room_data).grid(row=0, column=1, padx=(0, 8))
        tb.Button(quick, text="添加房间", bootstyle="primary", command=self._on_add_room).grid(row=0, column=2, padx=(0, 8))
        tb.Button(quick, text="名字/ID 添加", bootstyle="info", command=self._on_add_by_query).grid(row=0, column=3)

        recent = ttk.LabelFrame(page, text="最近事件", padding=10)
        recent.grid(row=2, column=0, sticky="nsew")
        recent.grid_rowconfigure(0, weight=1)
        recent.grid_columnconfigure(0, weight=1)
        self.recent_tree = ttk.Treeview(
            recent,
            columns=("time", "level", "source", "message"),
            show="headings",
            style="Dashboard.Treeview",
        )
        self.recent_tree.heading("time", text="时间")
        self.recent_tree.heading("level", text="级别")
        self.recent_tree.heading("source", text="来源")
        self.recent_tree.heading("message", text="消息")
        self.recent_tree.column("time", width=90, anchor="center")
        self.recent_tree.column("level", width=90, anchor="center")
        self.recent_tree.column("source", width=110, anchor="center")
        self.recent_tree.column("message", width=760, anchor="w")
        recent_scroll = ttk.Scrollbar(recent, orient="vertical", command=self.recent_tree.yview)
        self.recent_tree.configure(yscrollcommand=recent_scroll.set)
        self.recent_tree.grid(row=0, column=0, sticky="nsew")
        recent_scroll.grid(row=0, column=1, sticky="ns")
        return page

    def _create_kpi_card(self, parent, col: int, title: str, subtitle: str, var: tk.StringVar):
        card = ttk.LabelFrame(parent, text=subtitle, padding=10)
        card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 0))
        ttk.Label(card, text=title, style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(card, textvariable=var, style="CardValue.TLabel").grid(row=1, column=0, sticky="w", pady=(6, 0))

    def _build_rooms_page(self, parent):
        page = ttk.Frame(parent)
        page.grid_rowconfigure(2, weight=1)
        page.grid_columnconfigure(0, weight=1)

        action = ttk.LabelFrame(page, text="房间操作", padding=10)
        action.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        tb.Button(action, text="添加房间", bootstyle="primary", command=self._on_add_room).grid(row=0, column=0, padx=(0, 8))
        tb.Button(action, text="URL 添加", bootstyle="info", command=self._on_add_by_url).grid(row=0, column=1, padx=(0, 8))
        tb.Button(action, text="名字/ID 添加", bootstyle="info-outline", command=self._on_add_by_query).grid(row=0, column=2, padx=(0, 8))
        tb.Button(action, text="开始录制", bootstyle="success", command=self._on_start_selected).grid(row=0, column=3, padx=(0, 8))
        tb.Button(action, text="停止录制", bootstyle="danger", command=self._on_stop_selected).grid(row=0, column=4, padx=(0, 8))
        self.btn_rooms_monitor = tb.Button(action, text="启动监控", bootstyle="warning", command=self._on_toggle_monitor)
        self.btn_rooms_monitor.grid(row=0, column=5, padx=(0, 8))
        tb.Button(action, text="刷新", bootstyle="secondary", command=self._refresh_room_data).grid(row=0, column=6)

        filters = ttk.LabelFrame(page, text="筛选", padding=10)
        filters.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(filters, text="平台").grid(row=0, column=0, padx=(0, 6))
        platform_combo = ttk.Combobox(
            filters,
            textvariable=self.filter_platform_var,
            values=["全部", "DOUYIN", "BILIBILI", "DOUYU"],
            state="readonly",
            width=12,
        )
        platform_combo.grid(row=0, column=1, padx=(0, 16))
        platform_combo.bind("<<ComboboxSelected>>", lambda _e: self._render_room_table())
        ttk.Label(filters, text="状态").grid(row=0, column=2, padx=(0, 6))
        status_combo = ttk.Combobox(
            filters,
            textvariable=self.filter_status_var,
            values=["全部", "在线", "离线", "录制中"],
            state="readonly",
            width=12,
        )
        status_combo.grid(row=0, column=3, padx=(0, 16))
        status_combo.bind("<<ComboboxSelected>>", lambda _e: self._render_room_table())
        ttk.Label(filters, text="提示：可按平台和状态组合过滤").grid(row=0, column=4, sticky="w")

        content = ttk.Frame(page)
        content.grid(row=2, column=0, sticky="nsew")
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2)
        self._build_room_table(content)
        self._build_room_detail(content)
        return page

    def _build_room_table(self, parent):
        table_box = ttk.LabelFrame(parent, text="房间列表", padding=10)
        table_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        table_box.grid_rowconfigure(0, weight=1)
        table_box.grid_columnconfigure(0, weight=1)
        columns = ("platform", "room_id", "name", "live", "recording", "auto", "title")
        self.room_tree = ttk.Treeview(table_box, columns=columns, show="headings", style="Dashboard.Treeview")
        headers = {
            "platform": "平台",
            "room_id": "房间ID",
            "name": "名称",
            "live": "直播状态",
            "recording": "录制状态",
            "auto": "自动录制",
            "title": "标题",
        }
        widths = {"platform": 100, "room_id": 120, "name": 160, "live": 110, "recording": 110, "auto": 110, "title": 320}
        for key in columns:
            self.room_tree.heading(key, text=headers[key])
            self.room_tree.column(key, width=widths[key], anchor="center" if key != "title" else "w")
        scroll = ttk.Scrollbar(table_box, orient="vertical", command=self.room_tree.yview)
        self.room_tree.configure(yscrollcommand=scroll.set)
        self.room_tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.room_tree.bind("<<TreeviewSelect>>", self._on_select_room)

    def _build_room_detail(self, parent):
        detail = ttk.LabelFrame(parent, text="房间详情", padding=12)
        detail.grid(row=0, column=1, sticky="nsew")
        detail.grid_columnconfigure(1, weight=1)
        rows = [
            ("平台", "platform"),
            ("房间ID", "room_id"),
            ("名称", "name"),
            ("主播", "streamer"),
            ("直播状态", "live"),
            ("录制状态", "recording"),
            ("自动录制", "auto"),
            ("标题", "title"),
        ]
        for idx, (label, key) in enumerate(rows):
            ttk.Label(detail, text=label).grid(row=idx, column=0, sticky="nw", pady=4)
            ttk.Label(detail, textvariable=self.detail_vars[key], wraplength=330, justify="left").grid(row=idx, column=1, sticky="w", pady=4)
        actions = ttk.Frame(detail)
        actions.grid(row=len(rows), column=0, columnspan=2, sticky="ew", pady=(12, 0))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)
        actions.grid_columnconfigure(2, weight=1)
        tb.Button(actions, text="开始", bootstyle="success-outline", command=self._on_start_selected).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        tb.Button(actions, text="停止", bootstyle="danger-outline", command=self._on_stop_selected).grid(row=0, column=1, sticky="ew", padx=6)
        tb.Button(actions, text="删除", bootstyle="secondary-outline", command=self._on_delete_selected).grid(row=0, column=2, sticky="ew", padx=(6, 0))

    def _build_logs_page(self, parent):
        page = ttk.Frame(parent)
        page.grid_rowconfigure(1, weight=1)
        page.grid_columnconfigure(0, weight=1)
        tools = ttk.LabelFrame(page, text="日志工具", padding=10)
        tools.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(tools, text="级别").grid(row=0, column=0, padx=(0, 6))
        level_combo = ttk.Combobox(
            tools,
            textvariable=self.log_level_var,
            values=["ALL", "INFO", "ACTION", "WARN", "ERROR"],
            state="readonly",
            width=10,
        )
        level_combo.grid(row=0, column=1, padx=(0, 10))
        level_combo.bind("<<ComboboxSelected>>", lambda _e: self._render_logs())
        tb.Button(tools, text="清空日志", bootstyle="secondary", command=self._clear_logs).grid(row=0, column=2, padx=(0, 8))
        tb.Button(tools, text="复制日志", bootstyle="info", command=self._copy_logs).grid(row=0, column=3)
        panel = ttk.LabelFrame(page, text="实时日志", padding=8)
        panel.grid(row=1, column=0, sticky="nsew")
        panel.grid_rowconfigure(0, weight=1)
        panel.grid_columnconfigure(0, weight=1)
        self.log_text = tk.Text(panel, height=20, wrap="none", font=("Consolas", 10))
        self.log_text.grid(row=0, column=0, sticky="nsew")
        v_scroll = ttk.Scrollbar(panel, orient="vertical", command=self.log_text.yview)
        h_scroll = ttk.Scrollbar(panel, orient="horizontal", command=self.log_text.xview)
        self.log_text.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        return page

    def _build_statusbar(self):
        bar = ttk.Frame(self.root, padding=(14, 8))
        bar.grid(row=2, column=0, sticky="ew")
        bar.grid_columnconfigure(1, weight=1)
        ttk.Label(bar, textvariable=self.status_var).grid(row=0, column=0, sticky="w")
        ttk.Label(bar, textvariable=self.count_var).grid(row=0, column=2, sticky="e")

    def _switch_page(self, page: str):
        if not self.navigation_state.switch(page):
            return
        self.pages[page].tkraise()
        for key, button in self.nav_buttons.items():
            button.configure(bootstyle="primary" if key == page else "secondary-outline")
        if page == "logs":
            self._render_logs()

    def _on_theme_toggle(self):
        self.theme_state.set_mode("dark" if self.dark_mode_var.get() else "light")
        self._setup_styles()
        self._log("ACTION", f"切换主题: {self.theme_state.mode}", source="UI")

    def _set_status(self, message: str):
        self.status_var.set(message)

    def _format_live(self, is_live: bool) -> str:
        return "在线" if is_live else "离线"

    def _format_recording(self, is_recording: bool) -> str:
        return "录制中" if is_recording else "未录制"

    def _get_selected_room_key(self) -> Optional[str]:
        selected = self.room_tree.selection()
        return selected[0] if selected else None

    def _split_room_key(self, key: str):
        return key.split(":", 1)

    def _run_async(self, fn, on_done):
        def worker():
            ok = False
            err_msg = None
            try:
                ok = bool(fn())
            except Exception as exc:
                err_msg = str(exc)
            self.root.after(0, lambda: on_done(ok, err_msg))
        threading.Thread(target=worker, daemon=True).start()

    def _run_async_value(self, fn, on_done):
        def worker():
            value = None
            err_msg = None
            try:
                value = fn()
            except Exception as exc:
                err_msg = str(exc)
            self.root.after(0, lambda: on_done(value, err_msg))
        threading.Thread(target=worker, daemon=True).start()

    def _schedule_auto_refresh(self):
        self.refresh_timer = self.root.after(8000, self._auto_refresh_tick)

    def _auto_refresh_tick(self):
        self._refresh_room_data()
        self._schedule_auto_refresh()

    def _schedule_log_drain(self):
        self._drain_log_queue()
        self.root.after(250, self._schedule_log_drain)

    def _drain_log_queue(self):
        drained = self.log_buffer.drain()
        if not drained:
            return
        self._render_recent_events()
        if self.navigation_state.current == "logs":
            self._render_logs()

    def _log(self, level: str, message: str, source: str = "GUI"):
        self.log_buffer.emit(level, message, source)

    def _render_recent_events(self):
        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)
        for event in self.log_buffer.recent(12):
            self.recent_tree.insert("", "end", values=(event.timestamp, event.level, event.source, event.message))

    def _render_logs(self):
        level = self.log_level_var.get()
        events = self.log_buffer.filtered(level)
        self.log_text.delete("1.0", "end")
        for event in events:
            self.log_text.insert("end", f"[{event.timestamp}] [{event.level:<6}] [{event.source}] {event.message}\n")
        self.log_text.see("end")

    def _clear_logs(self):
        self.log_buffer.clear()
        self._render_logs()
        self._render_recent_events()
        self._log("ACTION", "日志已清空", source="UI")

    def _copy_logs(self):
        content = self.log_text.get("1.0", "end").strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self._set_status("日志已复制到剪贴板")
        self._log("ACTION", "复制日志到剪贴板", source="UI")

    def _refresh_room_data(self, log_events: bool = True):
        rooms = self.app.get_rooms()
        self.rooms_cache = {f"{room['platform']}:{room['room_id']}": room for room in rooms}
        total = len(rooms)
        live_count = sum(1 for room in rooms if room.get("is_live"))
        rec_count = sum(1 for room in rooms if room.get("is_recording"))
        monitor_running = self.app.room_manager.running
        self.kpi_total_var.set(str(total))
        self.kpi_live_var.set(str(live_count))
        self.kpi_recording_var.set(str(rec_count))
        self.kpi_monitor_var.set("运行中" if monitor_running else "已停止")
        self.count_var.set(f"房间: {total} | 在线: {live_count} | 录制: {rec_count}")
        self._update_monitor_buttons(monitor_running)
        self._render_room_table()
        if log_events:
            self._emit_room_state_events(rooms)
        self._set_status(f"已刷新 {total} 个房间")

    def _emit_room_state_events(self, rooms: List[Dict]):
        current_states: Dict[str, Dict[str, bool]] = {}
        for room in rooms:
            key = f"{room['platform']}:{room['room_id']}"
            state = {"is_live": bool(room.get("is_live", False)), "is_recording": bool(room.get("is_recording", False))}
            current_states[key] = state
            old_state = self.previous_room_states.get(key)
            if old_state is None:
                self._log("INFO", f"新增监控对象 {key}", source="ROOM")
                continue
            if not old_state["is_live"] and state["is_live"]:
                self._log("INFO", f"开播 {key}", source="MONITOR")
            if old_state["is_live"] and not state["is_live"]:
                self._log("WARN", f"下播 {key}", source="MONITOR")
            if not old_state["is_recording"] and state["is_recording"]:
                self._log("ACTION", f"开始录制 {key}", source="RECORDER")
            if old_state["is_recording"] and not state["is_recording"]:
                self._log("ACTION", f"停止录制 {key}", source="RECORDER")
        for key in self.previous_room_states.keys() - current_states.keys():
            self._log("WARN", f"移除监控对象 {key}", source="ROOM")
        self.previous_room_states = current_states

    def _filtered_rooms(self) -> List[Dict]:
        rooms = list(self.rooms_cache.values())
        platform_filter = self.filter_platform_var.get()
        status_filter = self.filter_status_var.get()
        if platform_filter != "全部":
            rooms = [room for room in rooms if room.get("platform", "").upper() == platform_filter]
        if status_filter == "在线":
            rooms = [room for room in rooms if room.get("is_live", False)]
        elif status_filter == "离线":
            rooms = [room for room in rooms if not room.get("is_live", False)]
        elif status_filter == "录制中":
            rooms = [room for room in rooms if room.get("is_recording", False)]
        return rooms

    def _render_room_table(self):
        old_selection = self._get_selected_room_key()
        for item in self.room_tree.get_children():
            self.room_tree.delete(item)
        for room in self._filtered_rooms():
            key = f"{room['platform']}:{room['room_id']}"
            self.room_tree.insert(
                "",
                "end",
                iid=key,
                values=(
                    room.get("platform", "").upper(),
                    room.get("room_id", ""),
                    room.get("name", "") or "-",
                    self._format_live(room.get("is_live", False)),
                    self._format_recording(room.get("is_recording", False)),
                    "是" if room.get("auto_record", True) else "否",
                    room.get("title", "") or "-",
                ),
            )
        if old_selection and old_selection in self.rooms_cache:
            self.room_tree.selection_set(old_selection)
            self.room_tree.focus(old_selection)
            self._render_room_details(old_selection)
        elif self.room_tree.get_children():
            first = self.room_tree.get_children()[0]
            self.room_tree.selection_set(first)
            self.room_tree.focus(first)
            self._render_room_details(first)
        else:
            self._clear_room_details()

    def _render_room_details(self, room_key: str):
        room = self.rooms_cache.get(room_key)
        if not room:
            self._clear_room_details()
            return
        self.selected_room_key = room_key
        self.detail_vars["platform"].set(room.get("platform", "-").upper())
        self.detail_vars["room_id"].set(room.get("room_id", "-"))
        self.detail_vars["name"].set(room.get("name", "") or "-")
        self.detail_vars["streamer"].set(room.get("streamer_name", "") or "-")
        self.detail_vars["live"].set(self._format_live(room.get("is_live", False)))
        self.detail_vars["recording"].set(self._format_recording(room.get("is_recording", False)))
        self.detail_vars["auto"].set("是" if room.get("auto_record", True) else "否")
        self.detail_vars["title"].set(room.get("title", "") or "-")

    def _clear_room_details(self):
        self.selected_room_key = None
        for value in self.detail_vars.values():
            value.set("-")

    def _on_select_room(self, _event=None):
        key = self._get_selected_room_key()
        if key:
            self._render_room_details(key)

    def _with_selected_room(self):
        key = self._get_selected_room_key() or self.selected_room_key
        if not key:
            messagebox.showinfo("提示", "请先选择房间")
            return None
        return self._split_room_key(key)

    def _update_monitor_buttons(self, monitor_running: bool):
        if monitor_running:
            self.btn_quick_monitor.configure(text="停止监控", bootstyle="danger")
            self.btn_rooms_monitor.configure(text="停止监控", bootstyle="danger")
        else:
            self.btn_quick_monitor.configure(text="启动监控", bootstyle="warning")
            self.btn_rooms_monitor.configure(text="启动监控", bootstyle="warning")

    def _on_toggle_monitor(self):
        if not self.app.room_manager.running:
            self.app.start_monitor()
            self._set_status("监控已启动")
            self._log("ACTION", "启动自动监控", source="MONITOR")
        else:
            self.app.stop_monitor()
            self._set_status("监控已停止")
            self._log("ACTION", "停止自动监控", source="MONITOR")
        self._refresh_room_data(log_events=False)

    def _on_start_selected(self):
        target = self._with_selected_room()
        if not target:
            return
        platform, room_id = target
        self._set_status(f"开始录制 {platform}/{room_id} ...")

        def done(ok: bool, err: Optional[str]):
            self._refresh_room_data(log_events=False)
            if ok:
                self._set_status(f"已开始录制 {platform}/{room_id}")
                self._log("ACTION", f"开始录制 {platform}/{room_id}", source="RECORDER")
            else:
                self._set_status(f"开始录制失败 {platform}/{room_id}")
                self._log("ERROR", f"开始录制失败 {platform}/{room_id}", source="RECORDER")
                if err:
                    messagebox.showerror("失败", err)
        self._run_async(lambda: self.app.start_recording(platform, room_id), done)

    def _on_stop_selected(self):
        target = self._with_selected_room()
        if not target:
            return
        platform, room_id = target
        self._set_status(f"停止录制 {platform}/{room_id} ...")

        def done(ok: bool, err: Optional[str]):
            self._refresh_room_data(log_events=False)
            if ok:
                self._set_status(f"已停止录制 {platform}/{room_id}")
                self._log("ACTION", f"停止录制 {platform}/{room_id}", source="RECORDER")
            else:
                self._set_status(f"停止录制失败 {platform}/{room_id}")
                self._log("ERROR", f"停止录制失败 {platform}/{room_id}", source="RECORDER")
                if err:
                    messagebox.showerror("失败", err)
        self._run_async(lambda: self.app.stop_recording(platform, room_id), done)

    def _on_delete_selected(self):
        target = self._with_selected_room()
        if not target:
            return
        platform, room_id = target
        if not messagebox.askyesno("确认", f"确认删除房间 {platform}/{room_id} ?"):
            return
        if self.app.remove_room(platform, room_id):
            self._refresh_room_data(log_events=False)
            self._set_status(f"已删除 {platform}/{room_id}")
            self._log("WARN", f"删除房间 {platform}/{room_id}", source="ROOM")
        else:
            messagebox.showerror("失败", "删除失败")

    def _on_add_room(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("添加房间")
        dialog.geometry("420x260")
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=14)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="平台").grid(row=0, column=0, sticky="w", pady=6)
        platform_var = tk.StringVar(value="douyin")
        ttk.Combobox(frame, textvariable=platform_var, values=PlatformParser.get_supported_platforms(), state="readonly").grid(row=0, column=1, sticky="ew", pady=6)
        ttk.Label(frame, text="房间ID").grid(row=1, column=0, sticky="w", pady=6)
        room_id_entry = ttk.Entry(frame)
        room_id_entry.grid(row=1, column=1, sticky="ew", pady=6)
        ttk.Label(frame, text="名称(可选)").grid(row=2, column=0, sticky="w", pady=6)
        name_entry = ttk.Entry(frame)
        name_entry.grid(row=2, column=1, sticky="ew", pady=6)
        auto_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="开播自动录制", variable=auto_var).grid(row=3, column=0, columnspan=2, sticky="w", pady=8)
        frame.grid_columnconfigure(1, weight=1)
        buttons = ttk.Frame(frame)
        buttons.grid(row=4, column=0, columnspan=2, sticky="e", pady=(16, 0))

        def do_add():
            platform = platform_var.get().strip()
            room_id = room_id_entry.get().strip()
            room_name = name_entry.get().strip()
            auto_record = auto_var.get()
            if not room_id:
                messagebox.showerror("错误", "请输入房间ID")
                return
            if self.app.add_room(platform, room_id, room_name, auto_record):
                dialog.destroy()
                self._refresh_room_data(log_events=False)
                self._set_status(f"已添加 {platform}/{room_id}")
                self._log("ACTION", f"添加房间 {platform}/{room_id}", source="ROOM")
            else:
                messagebox.showerror("失败", "房间已存在或添加失败")

        tb.Button(buttons, text="取消", bootstyle="secondary", command=dialog.destroy).pack(side="right", padx=(8, 0))
        tb.Button(buttons, text="添加", bootstyle="primary", command=do_add).pack(side="right")

    def _on_add_by_url(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("URL 添加")
        dialog.geometry("580x240")
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=14)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="直播间 URL").grid(row=0, column=0, sticky="w", pady=6)
        url_entry = ttk.Entry(frame)
        url_entry.grid(row=1, column=0, sticky="ew", pady=6)
        ttk.Label(frame, text="名称(可选)").grid(row=2, column=0, sticky="w", pady=6)
        name_entry = ttk.Entry(frame)
        name_entry.grid(row=3, column=0, sticky="ew", pady=6)
        auto_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="开播自动录制", variable=auto_var).grid(row=4, column=0, sticky="w", pady=6)
        ttk.Label(frame, text="支持：douyin.com, bilibili.com, douyu.com").grid(row=5, column=0, sticky="w", pady=4)
        frame.grid_columnconfigure(0, weight=1)
        buttons = ttk.Frame(frame)
        buttons.grid(row=6, column=0, sticky="e", pady=(10, 0))

        def do_add():
            url = url_entry.get().strip()
            room_name = name_entry.get().strip()
            auto_record = auto_var.get()
            if not url:
                messagebox.showerror("错误", "请输入 URL")
                return
            if self.app.add_room_by_url(url, name=room_name, auto_record=auto_record):
                dialog.destroy()
                self._refresh_room_data(log_events=False)
                self._set_status("URL 添加成功")
                self._log("ACTION", f"URL 添加成功: {url}", source="ROOM")
            else:
                messagebox.showerror("失败", "URL 解析失败或添加失败")

        tb.Button(buttons, text="取消", bootstyle="secondary", command=dialog.destroy).pack(side="right", padx=(8, 0))
        tb.Button(buttons, text="添加", bootstyle="primary", command=do_add).pack(side="right")

    def _on_add_by_query(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("名字/ID 添加")
        dialog.geometry("780x540")
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=14)
        frame.pack(fill="both", expand=True)
        frame.grid_rowconfigure(3, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        row = ttk.Frame(frame)
        row.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        row.grid_columnconfigure(3, weight=1)
        ttk.Label(row, text="平台").grid(row=0, column=0, padx=(0, 8))
        platform_var = tk.StringVar(value="douyin")
        ttk.Combobox(row, textvariable=platform_var, values=PlatformParser.get_supported_platforms(), state="readonly", width=12).grid(row=0, column=1, padx=(0, 8))
        ttk.Label(row, text="名字或ID").grid(row=0, column=2, padx=(0, 8))
        query_entry = ttk.Entry(row)
        query_entry.grid(row=0, column=3, sticky="ew", padx=(0, 8))

        row2 = ttk.Frame(frame)
        row2.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        row2.grid_columnconfigure(1, weight=1)
        ttk.Label(row2, text="房间名称(可选)").grid(row=0, column=0, padx=(0, 8))
        name_entry = ttk.Entry(row2)
        name_entry.grid(row=0, column=1, sticky="ew")
        auto_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="开播自动录制", variable=auto_var).grid(row=2, column=0, sticky="w", pady=(0, 8))

        status_var = tk.StringVar(value="输入名字、ID 或 URL 后点击搜索")
        columns = ("nickname", "room_id", "uid", "source")
        result_box = ttk.LabelFrame(frame, text="候选对象", padding=8)
        result_box.grid(row=3, column=0, sticky="nsew")
        result_box.grid_rowconfigure(0, weight=1)
        result_box.grid_columnconfigure(0, weight=1)
        result_tree = ttk.Treeview(result_box, columns=columns, show="headings", style="Dashboard.Treeview")
        result_tree.heading("nickname", text="昵称")
        result_tree.heading("room_id", text="房间ID")
        result_tree.heading("uid", text="UID")
        result_tree.heading("source", text="来源")
        result_tree.column("nickname", width=220, anchor="w")
        result_tree.column("room_id", width=160, anchor="center")
        result_tree.column("uid", width=160, anchor="center")
        result_tree.column("source", width=120, anchor="center")
        scroll = ttk.Scrollbar(result_box, orient="vertical", command=result_tree.yview)
        result_tree.configure(yscrollcommand=scroll.set)
        result_tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        footer = ttk.Frame(frame)
        footer.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        footer.grid_columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=status_var).grid(row=0, column=0, sticky="w")
        buttons = ttk.Frame(footer)
        buttons.grid(row=0, column=1, sticky="e")

        candidates_by_id: Dict[str, Dict] = {}

        def render_candidates(candidates: List[Dict]):
            candidates_by_id.clear()
            for item in result_tree.get_children():
                result_tree.delete(item)
            for idx, candidate in enumerate(candidates):
                iid = f"c_{idx}"
                candidates_by_id[iid] = candidate
                result_tree.insert(
                    "",
                    "end",
                    iid=iid,
                    values=(
                        candidate.get("nickname", "") or "-",
                        candidate.get("room_id", ""),
                        candidate.get("uid", "") or "-",
                        candidate.get("source", ""),
                    ),
                )

        def do_search():
            platform = platform_var.get().strip().lower()
            query = query_entry.get().strip()
            if not query:
                messagebox.showerror("错误", "请输入名字、ID或URL")
                return
            status_var.set("搜索中...")

            def on_done(value, err):
                if err:
                    status_var.set("搜索失败")
                    messagebox.showerror("失败", err)
                    return
                candidates = value or []
                render_candidates(candidates)
                if candidates:
                    first = result_tree.get_children()[0]
                    result_tree.selection_set(first)
                    status_var.set(f"找到 {len(candidates)} 个候选")
                else:
                    status_var.set("未找到候选对象")

            self._run_async_value(lambda: self.app.search_targets(platform, query, limit=20), on_done)

        def do_add_selected():
            selected = result_tree.selection()
            if not selected:
                messagebox.showinfo("提示", "请先选择候选对象")
                return
            candidate = candidates_by_id.get(selected[0])
            if not candidate:
                return
            platform = candidate.get("platform", "")
            room_id = candidate.get("room_id", "")
            room_name = name_entry.get().strip() or candidate.get("nickname", "")
            auto_record = auto_var.get()
            if self.app.add_room(platform, room_id, room_name, auto_record):
                dialog.destroy()
                self._refresh_room_data(log_events=False)
                self._set_status(f"已添加 {platform}/{room_id}")
                self._log("ACTION", f"名字/ID 添加成功 {platform}/{room_id}", source="ROOM")
            else:
                messagebox.showerror("失败", "房间已存在或添加失败")

        tb.Button(row, text="搜索", bootstyle="info", command=do_search).grid(row=0, column=4)
        tb.Button(buttons, text="取消", bootstyle="secondary", command=dialog.destroy).pack(side="right", padx=(8, 0))
        tb.Button(buttons, text="添加选中", bootstyle="primary", command=do_add_selected).pack(side="right")

    def on_close(self):
        if self.refresh_timer:
            self.root.after_cancel(self.refresh_timer)
        self.app.stop_all()
        self.root.destroy()


def main():
    if tb is None:
        print("Missing dependency: ttkbootstrap")
        print("Please run: pip install -r requirements.txt")
        raise SystemExit(1)

    root = tb.Window(themename="cyborg")
    app = DashboardGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
