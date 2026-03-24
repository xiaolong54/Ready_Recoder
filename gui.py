import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import LiveRecorderApp
from platform_parser import PlatformParser


class BililiveStyleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("直播录制工具 - Bililive Style")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)

        self.app = LiveRecorderApp()
        self.refresh_timer = None
        self.monitor_running = False

        self._setup_styles()
        self._setup_ui()
        self._refresh_room_list()
        self._start_auto_refresh()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Title.TLabel", font=("微软雅黑", 16, "bold"), foreground="#2c3e50")
        style.configure("Header.TLabel", font=("微软雅黑", 12), foreground="#34495e")
        style.configure("Status.TLabel", font=("微软雅黑", 10))
        style.configure("Info.TLabel", font=("微软雅黑", 9), foreground="#7f8c8d")

        style.configure("Live.TButton", font=("微软雅黑", 9), padding=5)
        style.configure("Action.TButton", font=("微软雅黑", 9), padding=3)

        style.configure("Card.TFrame", background="#ecf0f1", relief="raised", borderwidth=1)

    def _setup_ui(self):
        self._setup_header()
        self._setup_toolbar()
        self._setup_main_content()
        self._setup_statusbar()

    def _setup_header(self):
        header = tk.Frame(self.root, bg="#3498db", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        title = tk.Label(header, text="📺 直播录制工具", font=("微软雅黑", 20, "bold"),
                         fg="white", bg="#3498db")
        title.pack(side="left", padx=20, pady=15)

        version = tk.Label(header, text="v2.0 (参考bililive-go)", font=("微软雅黑", 9),
                           fg="#ecf0f1", bg="#3498db")
        version.pack(side="right", padx=20, pady=5)

    def _setup_toolbar(self):
        toolbar = tk.Frame(self.root, bg="#34495e", height=40)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        btn_add = tk.Button(toolbar, text="➕ 添加房间", font=("微软雅黑", 10),
                            command=self._on_add_room, bg="#27ae60", fg="white",
                            relief="flat", padx=15, cursor="hand2")
        btn_add.pack(side="left", padx=5, pady=5)

        btn_add_url = tk.Button(toolbar, text="🔗 URL添加", font=("微软雅黑", 10),
                                command=self._on_add_by_url, bg="#2980b9", fg="white",
                                relief="flat", padx=15, cursor="hand2")
        btn_add_url.pack(side="left", padx=5, pady=5)

        btn_start_all = tk.Button(toolbar, text="▶ 全部开始录制", font=("微软雅黑", 10),
                                   command=self._on_start_all, bg="#e67e22", fg="white",
                                   relief="flat", padx=15, cursor="hand2")
        btn_start_all.pack(side="left", padx=5, pady=5)

        btn_stop_all = tk.Button(toolbar, text="⏹ 全部停止", font=("微软雅黑", 10),
                                 command=self._on_stop_all, bg="#c0392b", fg="white",
                                 relief="flat", padx=15, cursor="hand2")
        btn_stop_all.pack(side="left", padx=5, pady=5)

        btn_monitor = tk.Button(toolbar, text="🔄 自动监控", font=("微软雅黑", 10),
                                command=self._on_toggle_monitor, bg="#8e44ad", fg="white",
                                relief="flat", padx=15, cursor="hand2")
        btn_monitor.pack(side="left", padx=5, pady=5)

        btn_refresh = tk.Button(toolbar, text="🔃 刷新", font=("微软雅黑", 10),
                                command=self._refresh_room_list, bg="#7f8c8d", fg="white",
                                relief="flat", padx=15, cursor="hand2")
        btn_refresh.pack(side="right", padx=5, pady=5)

    def _setup_main_content(self):
        self.main_frame = tk.Frame(self.root, bg="#bdc3c7")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(self.main_frame, bg="#bdc3c7", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)

        self.room_container = tk.Frame(self.canvas, bg="#bdc3c7")
        self.canvas.create_window((0, 0), window=self.room_container, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.room_container.bind("<Configure>",
                                lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def _setup_statusbar(self):
        statusbar = tk.Frame(self.root, bg="#2c3e50", height=30)
        statusbar.pack(fill="x", side="bottom")
        statusbar.pack_propagate(False)

        self.status_label = tk.Label(statusbar, text="就绪", font=("微软雅黑", 9),
                                     fg="#ecf0f1", bg="#2c3e50", anchor="w")
        self.status_label.pack(side="left", padx=10)

        self.room_count_label = tk.Label(statusbar, text="房间: 0 | 直播: 0 | 录制: 0",
                                          font=("微软雅黑", 9), fg="#ecf0f1", bg="#2c3e50")
        self.room_count_label.pack(side="right", padx=10)

    def _create_room_card(self, parent, room_data):
        platform = room_data.get("platform", "")
        room_id = room_data.get("room_id", "")
        name = room_data.get("name", f"{platform}/{room_id}")
        is_live = room_data.get("is_live", False)
        is_recording = room_data.get("is_recording", False)
        title = room_data.get("title", "")
        streamer = room_data.get("streamer_name", "")

        card = tk.Frame(parent, bg="#ecf0f1", relief="raised", borderwidth=2)
        card.pack(fill="x", padx=10, pady=5)

        platform_colors = {"douyin": "#fe2c55", "bilibili": "#00a1d6", "douyu": "#00be06"}
        platform_color = platform_colors.get(platform, "#95a5a6")

        status_frame = tk.Frame(card, bg=platform_color, width=8)
        status_frame.pack(side="left", fill="y")

        content = tk.Frame(card, bg="#ecf0f1")
        content.pack(side="left", fill="both", expand=True, padx=10, pady=8)

        top_row = tk.Frame(content, bg="#ecf0f1")
        top_row.pack(fill="x")

        name_label = tk.Label(top_row, text=name, font=("微软雅黑", 12, "bold"),
                              fg="#2c3e50", bg="#ecf0f1")
        name_label.pack(side="left")

        status_text = "🔴 未直播" if not is_live else ("🔴 直播中" if not is_recording else "⚫ 录制中")
        status_color = "#27ae60" if is_live else "#7f8c8d"
        if is_recording:
            status_text = "⚫ 录制中"
            status_color = "#e74c3c"

        status_label = tk.Label(top_row, text=status_text, font=("微软雅黑", 10, "bold"),
                                fg=status_color, bg="#ecf0f1")
        status_label.pack(side="right")

        if title:
            title_label = tk.Label(content, text=f"📌 {title}", font=("微软雅黑", 9),
                                   fg="#7f8c8d", bg="#ecf0f1", wraplength=600, justify="left")
            title_label.pack(fill="x", pady=(2, 0))

        platform_label = tk.Label(content, text=f"平台: {platform.upper()} | 主播: {streamer or '未知'}",
                                   font=("微软雅黑", 9), fg="#95a5a6", bg="#ecf0f1")
        platform_label.pack(fill="x")

        btn_frame = tk.Frame(card, bg="#ecf0f1")
        btn_frame.pack(side="right", padx=10)

        if is_recording:
            btn_rec = tk.Button(btn_frame, text="⏹ 停止", font=("微软雅黑", 9),
                                command=lambda: self._on_stop_recording(platform, room_id),
                                bg="#e74c3c", fg="white", relief="flat", padx=10, cursor="hand2")
        else:
            btn_rec = tk.Button(btn_frame, text="▶ 录制", font=("微软雅黑", 9),
                                command=lambda: self._on_start_recording(platform, room_id),
                                bg="#27ae60", fg="white", relief="flat", padx=10,
                                state="normal" if is_live else "disabled", cursor="hand2")

        btn_rec.pack(side="left", padx=2)

        btn_del = tk.Button(btn_frame, text="🗑️", font=("微软雅黑", 9),
                            command=lambda: self._on_delete_room(platform, room_id),
                            bg="#95a5a6", fg="white", relief="flat", padx=8, cursor="hand2")
        btn_del.pack(side="left", padx=2)

        return card

    def _refresh_room_list(self):
        for widget in self.room_container.winfo_children():
            widget.destroy()

        rooms = self.app.get_rooms()

        if not rooms:
            empty_label = tk.Label(self.room_container, text="📭 暂无监控的房间\n\n点击上方「添加房间」开始监控",
                                  font=("微软雅黑", 14), fg="#7f8c8d", bg="#bdc3c7")
            empty_label.pack(pady=100)
        else:
            live_count = sum(1 for r in rooms if r.get("is_live"))
            recording_count = sum(1 for r in rooms if r.get("is_recording"))

            for room in rooms:
                self._create_room_card(self.room_container, room)

            self.room_count_label.config(text=f"房间: {len(rooms)} | 直播: {live_count} | 录制: {recording_count}")

        self._set_status(f"已加载 {len(rooms)} 个房间")

    def _start_auto_refresh(self):
        self._refresh_room_list()
        self.refresh_timer = self.root.after(10000, self._start_auto_refresh)

    def _set_status(self, message):
        self.status_label.config(text=message)

    def _on_add_room(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("添加房间")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="平台:", font=("微软雅黑", 10)).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        platform_var = tk.StringVar(value="douyin")
        platform_combo = ttk.Combobox(dialog, textvariable=platform_var, width=20,
                                       values=["douyin", "bilibili", "douyu"], state="readonly")
        platform_combo.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(dialog, text="房间ID:", font=("微软雅黑", 10)).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        room_id_entry = ttk.Entry(dialog, width=25)
        room_id_entry.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(dialog, text="房间名称:", font=("微软雅黑", 10)).grid(row=2, column=0, padx=10, pady=10, sticky="w")
        name_entry = ttk.Entry(dialog, width=25)
        name_entry.grid(row=2, column=1, padx=10, pady=10)

        auto_var = tk.BooleanVar(value=True)
        tk.Checkbutton(dialog, text="开播自动录制", variable=auto_var).grid(row=3, column=1, padx=10, sticky="w")

        def do_add():
            platform = platform_var.get()
            room_id = room_id_entry.get().strip()
            name = name_entry.get().strip()
            auto_record = auto_var.get()

            if not room_id:
                messagebox.showerror("错误", "请输入房间ID")
                return

            if self.app.add_room(platform, room_id, name, auto_record):
                self._refresh_room_list()
                dialog.destroy()
                self._set_status(f"已添加房间: {platform}/{room_id}")
            else:
                messagebox.showerror("错误", "房间已存在或添加失败")

        btn_frame = tk.Frame(dialog)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)

        tk.Button(btn_frame, text="添加", command=do_add, font=("微软雅黑", 10),
                  bg="#27ae60", fg="white", relief="flat", padx=20).pack(side="left", padx=10)
        tk.Button(btn_frame, text="取消", command=dialog.destroy, font=("微软雅黑", 10),
                  bg="#95a5a6", fg="white", relief="flat", padx=20).pack(side="left", padx=10)

    def _on_add_by_url(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("URL添加房间")
        dialog.geometry("500x180")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="直播间URL:", font=("微软雅黑", 10)).pack(anchor="w", padx=20, pady=(20, 5))

        url_entry = ttk.Entry(dialog, width=50, font=("微软雅黑", 10))
        url_entry.pack(padx=20, pady=5)

        tk.Label(dialog, text="支持: douyin.com, bilibili.com, douyu.com", font=("微软雅黑", 9),
                 fg="#7f8c8d").pack(anchor="w", padx=20)

        auto_var = tk.BooleanVar(value=True)
        tk.Checkbutton(dialog, text="开播自动录制", variable=auto_var).pack(anchor="w", padx=20, pady=10)

        def do_add():
            url = url_entry.get().strip()
            if not url:
                messagebox.showerror("错误", "请输入直播间URL")
                return

            if self.app.add_room_by_url(url, auto_record=auto_var.get()):
                self._refresh_room_list()
                dialog.destroy()
                self._set_status("已添加房间")
            else:
                messagebox.showerror("错误", "URL解析失败，请检查格式")

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="添加", command=do_add, font=("微软雅黑", 10),
                  bg="#27ae60", fg="white", relief="flat", padx=20).pack(side="left", padx=10)
        tk.Button(btn_frame, text="取消", command=dialog.destroy, font=("微软雅黑", 10),
                  bg="#95a5a6", fg="white", relief="flat", padx=20).pack(side="left", padx=10)

    def _on_start_recording(self, platform, room_id):
        self._set_status(f"正在开始录制: {platform}/{room_id}")
        threading.Thread(target=self._start_recording_thread, args=(platform, room_id), daemon=True).start()

    def _start_recording_thread(self, platform, room_id):
        success = self.app.start_recording(platform, room_id)
        self.root.after(0, lambda: self._on_recording_result(success, platform, room_id))

    def _on_recording_result(self, success, platform, room_id):
        if success:
            self._set_status(f"已开始录制: {platform}/{room_id}")
            messagebox.showinfo("成功", f"已开始录制: {platform}/{room_id}")
        else:
            self._set_status(f"录制失败: {platform}/{room_id}")
            messagebox.showerror("失败", "无法开始录制，可能房间未开播或获取流地址失败")
        self._refresh_room_list()

    def _on_stop_recording(self, platform, room_id):
        self._set_status(f"正在停止录制: {platform}/{room_id}")
        threading.Thread(target=self._stop_recording_thread, args=(platform, room_id), daemon=True).start()

    def _stop_recording_thread(self, platform, room_id):
        success = self.app.stop_recording(platform, room_id)
        self.root.after(0, lambda: self._on_stop_result(success, platform, room_id))

    def _on_stop_result(self, success, platform, room_id):
        self._refresh_room_list()
        self._set_status(f"已停止录制: {platform}/{room_id}" if success else f"停止失败")

    def _on_delete_room(self, platform, room_id):
        if messagebox.askyesno("确认", f"确定要删除房间 {platform}/{room_id} 吗？"):
            if self.app.remove_room(platform, room_id):
                self._refresh_room_list()
                self._set_status(f"已删除房间: {platform}/{room_id}")

    def _on_start_all(self):
        rooms = self.app.get_rooms()
        count = 0
        for room in rooms:
            if room.get("is_live") and not room.get("is_recording"):
                if self.app.start_recording(room["platform"], room["room_id"]):
                    count += 1
        self._refresh_room_list()
        self._set_status(f"已批量开始 {count} 个录制")

    def _on_stop_all(self):
        rooms = self.app.get_rooms()
        count = 0
        for room in rooms:
            if room.get("is_recording"):
                if self.app.stop_recording(room["platform"], room["room_id"]):
                    count += 1
        self._refresh_room_list()
        self._set_status(f"已批量停止 {count} 个录制")

    def _on_toggle_monitor(self):
        if not self.monitor_running:
            self.app.start_monitor()
            self._monitor_running = True
            self._set_status("自动监控已开启")
            messagebox.showinfo("监控", "自动监控已开启，开播将自动录制")
        else:
            self.app.stop_monitor()
            self._monitor_running = False
            self._set_status("自动监控已关闭")

    def on_close(self):
        if self.refresh_timer:
            self.root.after_cancel(self.refresh_timer)
        self.app.stop_all()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = BililiveStyleGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
