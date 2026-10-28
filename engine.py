"""
FKey Mapper - Keyboard hook & action execution engine
Requires administrator privileges on Windows to intercept keys.
"""
import keyboard
import threading
import time
import logging

logger = logging.getLogger(__name__)


class ActionEngine:
    """Manages global hotkeys and executes action sequences."""

    def __init__(self):
        self.config = {}
        self.enabled = True
        self._callbacks = {}          # fkey_str -> callback returned by add_hotkey
        self._lock = threading.Lock()
        self._executing = False
        self._exec_lock = threading.Lock()

    # ── public API ────────────────────────────────────

    def load_config(self, config):
        """Replace the current config and re-register all hotkeys."""
        with self._lock:
            self.config = {k: list(v) for k, v in config.items()}
            self._reregister()

    def set_enabled(self, flag: bool):
        self.enabled = flag

    def stop(self):
        """Unregister every hotkey."""
        with self._lock:
            self._unregister_all()

    def execute_now(self, actions):
        """Run an action sequence immediately (for testing)."""
        t = threading.Thread(target=self._execute, args=(actions,), daemon=True)
        t.start()

    # ── internal ──────────────────────────────────────

    def _unregister_all(self):
        for _fkey, cb in self._callbacks.items():
            try:
                keyboard.remove_hotkey(cb)
            except (KeyError, ValueError, TypeError):
                pass
        self._callbacks.clear()

    def _reregister(self):
        self._unregister_all()
        for fkey, actions in self.config.items():
            if not actions:
                continue
            key_name = fkey.lower()          # "F1" -> "f1"
            handler = self._make_handler(actions)
            try:
                cb = keyboard.add_hotkey(
                    key_name,
                    handler,
                    suppress=True,
                    trigger_on_release=False,
                )
                self._callbacks[fkey] = cb
                logger.info("Registered %s  (%d actions)", key_name, len(actions))
            except Exception as exc:
                logger.error("Failed to register %s: %s", key_name, exc)

    def _make_handler(self, actions):
        def handler():
            if not self.enabled:
                return
            with self._exec_lock:
                if self._executing:
                    return               # still running previous sequence – skip
                self._executing = True
            t = threading.Thread(
                target=self._run_and_release, args=(actions,), daemon=True
            )
            t.start()
        return handler

    def _run_and_release(self, actions):
        try:
            self._execute(actions)
        finally:
            with self._exec_lock:
                self._executing = False

    @staticmethod
    def _execute(actions):
        """Walk through the action list, sending keys / sleeping."""
        for idx, action in enumerate(actions):
            try:
                atype = action.get("type", "")

                if atype == "hotkey":
                    keys = action.get("keys", [])
                    if keys:
                        combo = "+".join(keys)
                        keyboard.send(combo)
                        logger.debug("Step %d: hotkey %s", idx, combo)

                elif atype == "key":
                    key = action.get("key", "")
                    if key:
                        keyboard.send(key)
                        logger.debug("Step %d: key %s", idx, key)

                elif atype == "write":
                    text = action.get("text", "")
                    if text:
                        keyboard.write(text)
                        logger.debug("Step %d: write %r", idx, text)

                elif atype == "delay":
                    ms = action.get("ms", 0)
                    if ms > 0:
                        time.sleep(ms / 1000.0)
                        logger.debug("Step %d: delay %d ms", idx, ms)

            except Exception as exc:
                logger.error("Step %d failed: %s", idx, exc)
