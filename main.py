"""
FKey Mapper - F键自定义工具
将 F1-F12 映射为任意组合键 / 操作序列

Usage:
    python main.py

Requires administrator privileges on Windows.
"""
import sys
import os
import logging
import tkinter as tk

# ── logging ───────────────────────────────────────────

LOG_FILE = os.path.join(
    os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)),
    "fkey_mapper.log",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ── paths ─────────────────────────────────────────────

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "fkey_config.json")


# ── admin elevation (Windows) ─────────────────────────

def is_admin():
    if sys.platform != "win32":
        return True
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def elevate():
    try:
        import ctypes
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1,
        )
    except Exception:
        pass


# ── entry point ───────────────────────────────────────

def main():
    # Ask for admin on Windows
    if sys.platform == "win32" and not is_admin():
        root = tk.Tk()
        root.withdraw()
        result = tk.messagebox.askyesno(
            "需要管理员权限",
            "FKey Mapper 需要管理员权限来拦截键盘输入。\n是否以管理员身份重新启动？",
        )
        root.destroy()
        if result:
            elevate()
        sys.exit(0)

    from engine import ActionEngine
    from gui import FKeyMapperGUI

    engine = ActionEngine()
    root = tk.Tk()
    app = FKeyMapperGUI(root, engine, config_path=CONFIG_FILE)

    def on_closing():
        engine.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    logger.info("FKey Mapper started  (config: %s)", CONFIG_FILE)
    root.mainloop()


if __name__ == "__main__":
    main()
