"""
FKey Mapper - Configuration GUI (tkinter)
"""
import json
import os
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

logger = logging.getLogger(__name__)

# ── constants ─────────────────────────────────────────

COMMON_KEYS = [
    "enter", "tab", "escape", "space", "backspace", "delete",
    "up", "down", "left", "right",
    "home", "end", "pageup", "pagedown",
    "insert", "caps_lock", "num_lock",
    "print_screen", "scroll_lock", "pause",
]

HOTKEY_PRESETS = [
    ("复制",     "ctrl+c"),
    ("粘贴",     "ctrl+v"),
    ("剪切",     "ctrl+x"),
    ("撤销",     "ctrl+z"),
    ("重做",     "ctrl+y"),
    ("全选",     "ctrl+a"),
    ("保存",     "ctrl+s"),
    ("查找",     "ctrl+f"),
    ("关闭",     "alt+f4"),
    ("切换窗口", "alt+tab"),
]

TYPE_NAMES = {
    "hotkey": "组合键",
    "key":    "单键",
    "write":  "文本输入",
    "delay":  "延迟",
}


# ── main GUI class ────────────────────────────────────

class FKeyMapperGUI:

    def __init__(self, root, engine, config_path="fkey_config.json"):
        self.root = root
        self.engine = engine
        self.config_path = config_path
        self.config = {}
        self.selected_fkey = None

        self.root.title("FKey Mapper - F键自定义工具")
        self.root.geometry("880x620")
        self.root.minsize(760, 520)

        style = ttk.Style()
        style.theme_use("clam")

        self._load_config()
        self._build_ui()
        self._refresh_fkey_list()
        self.engine.load_config(self.config)

    # ── config I/O ────────────────────────────────────

    def _load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except Exception as exc:
                logger.error("加载配置失败: %s", exc)
                self.config = {}
        for i in range(1, 13):
            self.config.setdefault(f"F{i}", [])

    def _save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            self.status_label.config(text="配置已保存")
        except Exception as exc:
            messagebox.showerror("错误", f"保存配置失败:\n{exc}")

    # ── UI build ──────────────────────────────────────

    def _build_ui(self):
        # ── toolbar ──
        toolbar = ttk.Frame(self.root, padding=5)
        toolbar.pack(fill=tk.X)

        self.enable_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            toolbar, text="启用拦截", variable=self.enable_var,
            command=self._toggle_enable,
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(toolbar, text="保存", command=self._save_config).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="重载", command=self._reload_config).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)
        ttk.Button(toolbar, text="导入", command=self._import_config).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="导出", command=self._export_config).pack(side=tk.LEFT, padx=2)

        # ── main paned window ──
        pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ── left: F-key list ──
        left = ttk.LabelFrame(pane, text="功能键", padding=5)
        pane.add(left, weight=1)

        self.fkey_tree = ttk.Treeview(
            left, columns=("summary",), show="tree", selectmode="browse",
        )
        fkey_sb = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.fkey_tree.yview)
        self.fkey_tree.configure(yscrollcommand=fkey_sb.set)
        self.fkey_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        fkey_sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.fkey_tree.bind("<<TreeviewSelect>>", self._on_fkey_select)

        self.fkey_tree.tag_configure("set",   foreground="black")
        self.fkey_tree.tag_configure("unset", foreground="gray")

        # ── right: action editor ──
        right = ttk.Frame(pane, padding=5)
        pane.add(right, weight=2)

        self.detail_title = ttk.Label(
            right, text="请选择左侧的功能键", font=("Microsoft YaHei", 11, "bold"),
        )
        self.detail_title.pack(anchor=tk.W)

        # action list
        list_frame = ttk.Frame(right)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.action_tree = ttk.Treeview(
            list_frame,
            columns=("step", "type", "detail"),
            show="headings",
            height=14,
        )
        self.action_tree.heading("step",   text="#")
        self.action_tree.heading("type",   text="类型")
        self.action_tree.heading("detail", text="内容")
        self.action_tree.column("step",   width=40,  anchor=tk.CENTER, stretch=False)
        self.action_tree.column("type",   width=80,  anchor=tk.CENTER, stretch=False)
        self.action_tree.column("detail", width=400)

        action_sb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.action_tree.yview)
        self.action_tree.configure(yscrollcommand=action_sb.set)
        self.action_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        action_sb.pack(side=tk.RIGHT, fill=tk.Y)

        # right-click menu
        self.action_menu = tk.Menu(self.root, tearoff=0)
        self.action_menu.add_command(label="上移", command=self._move_up)
        self.action_menu.add_command(label="下移", command=self._move_down)
        self.action_menu.add_separator()
        self.action_menu.add_command(label="删除", command=self._delete_action)
        self.action_tree.bind("<Button-3>", self._show_action_menu)

        # action buttons
        btn_frame = ttk.Frame(right)
        btn_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(btn_frame, text="+ 组合键",  command=self._add_hotkey).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="+ 单键",    command=self._add_key).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="+ 文本",    command=self._add_write).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="+ 延迟",    command=self._add_delay).pack(side=tk.LEFT, padx=2)
        ttk.Separator(btn_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)
        ttk.Button(btn_frame, text="上移", width=4, command=self._move_up).pack(side=tk.LEFT, padx=1)
        ttk.Button(btn_frame, text="下移", width=4, command=self._move_down).pack(side=tk.LEFT, padx=1)
        ttk.Button(btn_frame, text="删除", width=4, command=self._delete_action).pack(side=tk.LEFT, padx=1)
        ttk.Separator(btn_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)
        ttk.Button(btn_frame, text="测试执行", command=self._test_run).pack(side=tk.LEFT, padx=2)

        # ── status bar ──
        status = ttk.Frame(self.root)
        status.pack(fill=tk.X, padx=5, pady=(0, 3))
        self.status_label = ttk.Label(status, text="就绪", foreground="gray")
        self.status_label.pack(side=tk.LEFT)

    # ── F-key list helpers ────────────────────────────

    def _refresh_fkey_list(self):
        self.fkey_tree.delete(*self.fkey_tree.get_children())
        for i in range(1, 13):
            key = f"F{i}"
            actions = self.config.get(key, [])
            summary = self._summarize(actions)
            tag = "set" if actions else "unset"
            self.fkey_tree.insert("", tk.END, iid=key, text=key,
                                  values=(summary,), tags=(tag,))

    @staticmethod
    def _summarize(actions):
        if not actions:
            return "(未设置)"
        parts = []
        for a in actions:
            t = a.get("type", "")
            if t == "hotkey":
                parts.append("+".join(k.capitalize() for k in a.get("keys", [])))
            elif t == "key":
                parts.append(a.get("key", "").capitalize())
            elif t == "write":
                txt = a.get("text", "")
                parts.append(f'"{txt[:8]}..."' if len(txt) > 8 else f'"{txt}"')
            elif t == "delay":
                parts.append(f"等待 {a.get('ms', 0)} ms")
        return " -> ".join(parts)

    def _on_fkey_select(self, _event=None):
        sel = self.fkey_tree.selection()
        if sel:
            self.selected_fkey = sel[0]
            self.detail_title.config(text=f"编辑 {self.selected_fkey} 的操作序列")
            self._refresh_action_list()

    # ── action list helpers ───────────────────────────

    def _refresh_action_list(self):
        self.action_tree.delete(*self.action_tree.get_children())
        if not self.selected_fkey:
            return
        for i, a in enumerate(self.config.get(self.selected_fkey, [])):
            t = a.get("type", "")
            type_name = TYPE_NAMES.get(t, t)
            if t == "hotkey":
                detail = "+".join(k.capitalize() for k in a.get("keys", []))
            elif t == "key":
                detail = a.get("key", "").capitalize()
            elif t == "write":
                detail = f'"{a.get("text", "")}"'
            elif t == "delay":
                detail = f'{a.get("ms", 0)} ms'
            else:
                detail = str(a)
            self.action_tree.insert("", tk.END, iid=str(i),
                                    values=(i + 1, type_name, detail))

    def _sel_idx(self):
        sel = self.action_tree.selection()
        return int(sel[0]) if sel else None

    def _delete_action(self):
        if not self.selected_fkey:
            return
        idx = self._sel_idx()
        if idx is None:
            return
        actions = self.config.get(self.selected_fkey, [])
        if 0 <= idx < len(actions):
            del actions[idx]
            self._refresh_action_list()
            self._refresh_fkey_list()
            self._apply()

    def _move_up(self):
        if not self.selected_fkey:
            return
        idx = self._sel_idx()
        if idx is None or idx == 0:
            return
        actions = self.config[self.selected_fkey]
        actions[idx - 1], actions[idx] = actions[idx], actions[idx - 1]
        self._refresh_action_list()
        self._apply()
        self.action_tree.selection_set(str(idx - 1))

    def _move_down(self):
        if not self.selected_fkey:
            return
        idx = self._sel_idx()
        actions = self.config.get(self.selected_fkey, [])
        if idx is None or idx >= len(actions) - 1:
            return
        actions[idx], actions[idx + 1] = actions[idx + 1], actions[idx]
        self._refresh_action_list()
        self._apply()
        self.action_tree.selection_set(str(idx + 1))

    def _show_action_menu(self, event):
        row = self.action_tree.identify_row(event.y)
        if row:
            self.action_tree.selection_set(row)
            self.action_menu.post(event.x_root, event.y_root)

    def _test_run(self):
        """Execute the selected F-key's actions immediately."""
        if not self.selected_fkey:
            return
        actions = self.config.get(self.selected_fkey, [])
        if not actions:
            messagebox.showinfo("提示", "该键未设置任何操作")
            return
        self.status_label.config(text=f"测试执行 {self.selected_fkey} ...")
        self.engine.execute_now(actions)

    # ── add-action dialogs ────────────────────────────

    def _ensure_fkey(self):
        if not self.selected_fkey:
            messagebox.showinfo("提示", "请先在左侧选择一个功能键 (F1-F12)")
            return False
        return True

    def _apply(self):
        self.engine.load_config(self.config)
        self.status_label.config(text=f"已更新 - {self.selected_fkey or ''}")

    # ─ add hotkey ─

    def _add_hotkey(self):
        if not self._ensure_fkey():
            return

        dlg = tk.Toplevel(self.root)
        dlg.title("添加组合键")
        dlg.geometry("440x340")
        dlg.transient(self.root)
        dlg.grab_set()

        ttk.Label(dlg, text="在下方区域按下组合键自动录入:", padding=(10, 10, 10, 0)).pack(anchor=tk.W)
        display_var = tk.StringVar(value="(等待按键...)")
        display = ttk.Label(dlg, textvariable=display_var,
                            font=("Consolas", 16), foreground="blue")
        display.pack(pady=8)

        key_result = [None]
        pressed_mods = set()

        def on_press(event):
            sym = event.keysym
            if sym in ("Control_L", "Control_R"):
                pressed_mods.add("ctrl")
            elif sym in ("Alt_L", "Alt_R"):
                pressed_mods.add("alt")
            elif sym in ("Shift_L", "Shift_R"):
                pressed_mods.add("shift")
            elif sym in ("Super_L", "Super_R"):
                pressed_mods.add("win")
            else:
                main_key = sym.lower()
                remap = {"return": "enter", "next": "pagedown", "prior": "pageup"}
                main_key = remap.get(main_key, main_key)
                parts = sorted(pressed_mods) + [main_key]
                combo = "+".join(parts)
                key_result[0] = combo
                display_var.set(combo)
                pressed_mods.clear()

        def on_release(event):
            mod_map = {
                "Control_L": "ctrl", "Control_R": "ctrl",
                "Alt_L": "alt",   "Alt_R": "alt",
                "Shift_L": "shift", "Shift_R": "shift",
                "Super_L": "win", "Super_R": "win",
            }
            if event.keysym in mod_map:
                pressed_mods.discard(mod_map[event.keysym])

        dlg.bind_all("<KeyPress>", on_press)
        dlg.bind_all("<KeyRelease>", on_release)

        # manual input
        manual_frame = ttk.Frame(dlg)
        manual_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(manual_frame, text="或手动输入:").pack(side=tk.LEFT)
        manual_var = tk.StringVar()
        ttk.Entry(manual_frame, textvariable=manual_var, width=20,
                  font=("Consolas", 11)).pack(side=tk.LEFT, padx=5)

        # presets
        preset_frame = ttk.LabelFrame(dlg, text="常用组合键", padding=5)
        preset_frame.pack(fill=tk.X, padx=10, pady=10)
        for i, (label, combo) in enumerate(HOTKEY_PRESETS):
            def _set(c=combo):
                key_result[0] = c
                display_var.set(c)
            ttk.Button(preset_frame, text=label, width=8, command=_set).grid(
                row=i // 5, column=i % 5, padx=2, pady=2)

        def confirm():
            manual = manual_var.get().strip().lower()
            if manual:
                key_result[0] = manual
            combo_str = key_result[0]
            if combo_str:
                keys = [k.strip() for k in combo_str.split("+")]
                actions = self.config.setdefault(self.selected_fkey, [])
                actions.append({"type": "hotkey", "keys": keys})
                self._refresh_action_list()
                self._refresh_fkey_list()
                self._apply()
            dlg.destroy()

        btn_frame = ttk.Frame(dlg)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="确定", command=confirm).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dlg.destroy).pack(side=tk.LEFT, padx=5)
        dlg.wait_window()

    # ─ add single key ─

    def _add_key(self):
        if not self._ensure_fkey():
            return

        dlg = tk.Toplevel(self.root)
        dlg.title("添加单键")
        dlg.geometry("320x160")
        dlg.transient(self.root)
        dlg.grab_set()

        ttk.Label(dlg, text="选择或输入按键名称:", padding=10).pack()
        key_var = tk.StringVar(value="enter")
        combo = ttk.Combobox(dlg, textvariable=key_var, values=COMMON_KEYS, width=20)
        combo.pack(pady=5)

        def confirm():
            key = key_var.get().strip().lower()
            if key:
                actions = self.config.setdefault(self.selected_fkey, [])
                actions.append({"type": "key", "key": key})
                self._refresh_action_list()
                self._refresh_fkey_list()
                self._apply()
            dlg.destroy()

        btn_frame = ttk.Frame(dlg)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="确定", command=confirm).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dlg.destroy).pack(side=tk.LEFT, padx=5)
        combo.bind("<Return>", lambda e: confirm())
        dlg.wait_window()

    # ─ add text input ─

    def _add_write(self):
        if not self._ensure_fkey():
            return

        dlg = tk.Toplevel(self.root)
        dlg.title("添加文本输入")
        dlg.geometry("420x160")
        dlg.transient(self.root)
        dlg.grab_set()

        ttk.Label(dlg, text="要自动输入的文本:", padding=10).pack()
        text_var = tk.StringVar()
        entry = ttk.Entry(dlg, textvariable=text_var, width=45)
        entry.pack(pady=5)
        entry.focus_set()

        def confirm():
            text = text_var.get()
            if text:
                actions = self.config.setdefault(self.selected_fkey, [])
                actions.append({"type": "write", "text": text})
                self._refresh_action_list()
                self._refresh_fkey_list()
                self._apply()
            dlg.destroy()

        btn_frame = ttk.Frame(dlg)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="确定", command=confirm).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dlg.destroy).pack(side=tk.LEFT, padx=5)
        entry.bind("<Return>", lambda e: confirm())
        dlg.wait_window()

    # ─ add delay ─

    def _add_delay(self):
        if not self._ensure_fkey():
            return

        dlg = tk.Toplevel(self.root)
        dlg.title("添加延迟")
        dlg.geometry("340x180")
        dlg.transient(self.root)
        dlg.grab_set()

        ttk.Label(dlg, text="延迟时间（毫秒）:", padding=10).pack()
        delay_var = tk.StringVar(value="1000")
        entry = ttk.Entry(dlg, textvariable=delay_var, width=15)
        entry.pack(pady=5)
        entry.focus_set()

        quick = ttk.Frame(dlg)
        quick.pack(pady=3)
        for ms in [100, 250, 500, 1000, 2000, 3000]:
            ttk.Button(quick, text=f"{ms}ms", width=5,
                       command=lambda m=ms: delay_var.set(str(m))).pack(side=tk.LEFT, padx=1)

        def confirm():
            try:
                ms = int(delay_var.get())
                if ms >= 0:
                    actions = self.config.setdefault(self.selected_fkey, [])
                    actions.append({"type": "delay", "ms": ms})
                    self._refresh_action_list()
                    self._refresh_fkey_list()
                    self._apply()
            except ValueError:
                messagebox.showerror("错误", "请输入有效的整数", parent=dlg)
            dlg.destroy()

        btn_frame = ttk.Frame(dlg)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="确定", command=confirm).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dlg.destroy).pack(side=tk.LEFT, padx=5)
        entry.bind("<Return>", lambda e: confirm())
        dlg.wait_window()

    # ── toolbar actions ───────────────────────────────

    def _toggle_enable(self):
        self.engine.set_enabled(self.enable_var.get())
        self.status_label.config(text="已启用" if self.enable_var.get() else "已禁用")

    def _reload_config(self):
        self._load_config()
        self._refresh_fkey_list()
        if self.selected_fkey:
            self._refresh_action_list()
        self.engine.load_config(self.config)
        self.status_label.config(text="配置已重载")

    def _import_config(self):
        path = filedialog.askopenfilename(
            title="导入配置",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.config = data
            for i in range(1, 13):
                self.config.setdefault(f"F{i}", [])
            self._refresh_fkey_list()
            self.engine.load_config(self.config)
            self._save_config()
            self.status_label.config(text="配置已导入")
        except Exception as exc:
            messagebox.showerror("导入失败", str(exc))

    def _export_config(self):
        path = filedialog.asksaveasfilename(
            title="导出配置",
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            self.status_label.config(text=f"已导出到 {os.path.basename(path)}")
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))
