import os
import sys
import platform
import tarfile
import zipfile
import shutil
import subprocess
import threading
import locale
import tkinter as tk
from tkinter import messagebox
from tkinter import font as tkfont

# ---------------------------------------------------------------------------
# Environment detection
# ---------------------------------------------------------------------------
IS_MAC = platform.system() == "Darwin"
IS_WIN = platform.system() == "Windows"
ARCH = platform.machine().lower()
IS_ARM = "arm" in ARCH or "aarch64" in ARCH


def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def add_to_path_win(target_dir):
    import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_ALL_ACCESS)
        current_path, _ = winreg.QueryValueEx(key, "PATH")
        if target_dir not in current_path:
            new_path = current_path + ";" + target_dir
            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
            subprocess.run(["setx", "PATH", new_path], shell=True, stdout=subprocess.DEVNULL)
    except Exception as e:
        print(f"Failed to update PATH: {e}")


def get_install_dirs():
    if IS_MAC:
        bin_dir = os.path.expanduser("~/.local/bin")
        app_dir = os.path.expanduser("~/.local/share/ai_tools_env")
    elif IS_WIN:
        bin_dir = os.path.join(os.environ["LOCALAPPDATA"], "Programs", "ai_tools_bin")
        app_dir = os.path.join(os.environ["LOCALAPPDATA"], "Programs", "ai_tools_env")
    else:
        raise Exception("Unsupported OS")

    os.makedirs(bin_dir, exist_ok=True)
    os.makedirs(app_dir, exist_ok=True)

    if IS_MAC:
        shell_rc = os.path.expanduser("~/.zshrc")
        if os.path.exists(shell_rc):
            with open(shell_rc, "r") as f:
                content = f.read()
            if "export PATH=\"$HOME/.local/bin:$PATH\"" not in content:
                with open(shell_rc, "a") as f:
                    f.write('\nexport PATH="$HOME/.local/bin:$PATH"\n')

    elif IS_WIN:
        add_to_path_win(bin_dir)

    return bin_dir, app_dir


def install_codex():
    bin_dir, _ = get_install_dirs()
    if IS_MAC:
        filename = "codex-mac-arm64.tar.gz" if IS_ARM else "codex-mac-x64.tar.gz"
        archive_path = get_resource_path(f"payload/{filename}")
        if not os.path.exists(archive_path):
            raise Exception(f"macOS Codex payload not found: {filename}")
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=bin_dir)
            for member in tar.getmembers():
                if member.isfile() and "codex" in member.name:
                    extracted_path = os.path.join(bin_dir, member.name)
                    final_path = os.path.join(bin_dir, "codex")
                    if extracted_path != final_path:
                        shutil.move(extracted_path, final_path)
                    os.chmod(final_path, 0o755)
    elif IS_WIN:
        archive_path = get_resource_path("payload/codex-win-x64.zip")
        if not os.path.exists(archive_path):
            raise Exception("Windows Codex payload not found.")
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(bin_dir)
            for root, dirs, files in os.walk(bin_dir):
                for file in files:
                    if "codex.exe" in file:
                        extracted_path = os.path.join(root, file)
                        final_path = os.path.join(bin_dir, "codex.exe")
                        if extracted_path != final_path:
                            shutil.move(extracted_path, final_path)


def install_claude_code():
    bin_dir, app_dir = get_install_dirs()
    node_dir = os.path.join(app_dir, "node")

    if IS_MAC:
        filename = "node-mac-arm64.tar.gz" if IS_ARM else "node-mac-x64.tar.gz"
        archive_path = get_resource_path(f"payload/{filename}")
        if not os.path.exists(archive_path):
            raise Exception(f"macOS Node payload not found: {filename}")
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=app_dir)
            extracted_folder = [m.name for m in tar.getmembers() if m.isdir()][0].split('/')[0]
            if os.path.exists(node_dir):
                shutil.rmtree(node_dir)
            shutil.move(os.path.join(app_dir, extracted_folder), node_dir)

        npm_bin = os.path.join(node_dir, "bin", "npm")
        claude_bin = os.path.join(node_dir, "bin", "claude")
    elif IS_WIN:
        archive_path = get_resource_path("payload/node-win-x64.zip")
        if not os.path.exists(archive_path):
            raise Exception("Windows Node payload not found.")
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(app_dir)
            extracted_folder = zip_ref.namelist()[0].split('/')[0]
            if os.path.exists(node_dir):
                shutil.rmtree(node_dir)
            shutil.move(os.path.join(app_dir, extracted_folder), node_dir)
        npm_bin = os.path.join(node_dir, "npm.cmd")
        claude_bin = os.path.join(node_dir, "claude.cmd")

    payload_dir = get_resource_path("payload")
    claude_tgz = None
    for f in os.listdir(payload_dir):
        if f.startswith("anthropic-ai-claude-code") and f.endswith(".tgz"):
            claude_tgz = os.path.join(payload_dir, f)
            break

    if not claude_tgz:
        raise Exception("Claude code npm package not found in payload.")

    subprocess.run([npm_bin, "install", "-g", claude_tgz], check=True, env=os.environ.copy())

    if IS_MAC:
        target_link = os.path.join(bin_dir, "claude")
        if os.path.exists(target_link) or os.path.islink(target_link):
            os.remove(target_link)
        os.symlink(claude_bin, target_link)
    elif IS_WIN:
        target_bat = os.path.join(bin_dir, "claude.cmd")
        with open(target_bat, "w") as f:
            f.write(f'@echo off\n"{claude_bin}" %*')


# ---------------------------------------------------------------------------
# Localization
# ---------------------------------------------------------------------------
LANGS = ["en", "zh-Hans", "zh-Hant"]
LANG_LABELS = {"en": "EN", "zh-Hans": "简", "zh-Hant": "繁"}

STRINGS = {
    "en": {
        "app_title": "AI Tools Installer",
        "app_subtitle": "Set up Codex CLI & Claude Code — fully offline",
        "codex_title": "Codex CLI",
        "codex_desc": "OpenAI's coding agent for your terminal",
        "claude_title": "Claude Code CLI",
        "claude_desc": "Anthropic's coding agent for your terminal",
        "install_button": "Install Now",
        "installing_button": "Installing…",
        "status_idle": "",
        "status_installing_codex": "Installing Codex CLI…",
        "status_installing_claude": "Installing Claude Code (Node.js)…",
        "status_done": "Installation complete",
        "status_failed": "Installation failed",
        "success_title": "Success",
        "success_body": "Installation successful!\n\nInstalled to:\n{path}\n\nRestart your terminal to use 'codex' and 'claude'.",
        "error_title": "Error",
        "error_body": "Something went wrong:\n{error}",
        "footer_hint": "Uncheck a tool to skip installing it.",
    },
    "zh-Hans": {
        "app_title": "AI 工具安装向导",
        "app_subtitle": "离线安装 Codex CLI 与 Claude Code",
        "codex_title": "Codex CLI",
        "codex_desc": "OpenAI 出品的终端编程助手",
        "claude_title": "Claude Code CLI",
        "claude_desc": "Anthropic 出品的终端编程助手",
        "install_button": "立即安装",
        "installing_button": "安装中…",
        "status_idle": "",
        "status_installing_codex": "正在安装 Codex CLI…",
        "status_installing_claude": "正在安装 Claude Code (Node.js)…",
        "status_done": "安装完成",
        "status_failed": "安装失败",
        "success_title": "安装成功",
        "success_body": "安装成功！\n\n已安装至：\n{path}\n\n请重启终端后使用 codex 和 claude 命令。",
        "error_title": "出错了",
        "error_body": "安装过程中出现错误：\n{error}",
        "footer_hint": "取消勾选可跳过对应工具的安装。",
    },
    "zh-Hant": {
        "app_title": "AI 工具安裝精靈",
        "app_subtitle": "離線安裝 Codex CLI 與 Claude Code",
        "codex_title": "Codex CLI",
        "codex_desc": "OpenAI 推出的終端機程式設計助手",
        "claude_title": "Claude Code CLI",
        "claude_desc": "Anthropic 推出的終端機程式設計助手",
        "install_button": "立即安裝",
        "installing_button": "安裝中…",
        "status_idle": "",
        "status_installing_codex": "正在安裝 Codex CLI…",
        "status_installing_claude": "正在安裝 Claude Code (Node.js)…",
        "status_done": "安裝完成",
        "status_failed": "安裝失敗",
        "success_title": "安裝成功",
        "success_body": "安裝成功！\n\n已安裝至：\n{path}\n\n請重新啟動終端機後使用 codex 和 claude 指令。",
        "error_title": "發生錯誤",
        "error_body": "安裝過程中發生錯誤：\n{error}",
        "footer_hint": "取消勾選可略過該工具的安裝。",
    },
}


def detect_language():
    try:
        loc = locale.getlocale()[0] or ""
    except Exception:
        loc = ""
    if not loc:
        for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
            loc = os.environ.get(var, "")
            if loc:
                break
    loc = loc.lower()
    if "zh" not in loc:
        return "en"
    if any(tag in loc for tag in ("tw", "hk", "mo", "hant")):
        return "zh-Hant"
    return "zh-Hans"


# ---------------------------------------------------------------------------
# Platform-aware design tokens
# ---------------------------------------------------------------------------
if IS_WIN:
    COLOR_BG = "#F3F3F3"
    COLOR_CARD = "#FFFFFF"
    COLOR_CARD_BORDER = "#E5E5E5"
    COLOR_SHADOW = "#E4E4E4"
    COLOR_TEXT = "#1A1A1A"
    COLOR_SUBTEXT = "#5C5C5C"
    COLOR_ACCENT = "#0067C0"
    COLOR_ACCENT_HOVER = "#005A9E"
    COLOR_TOGGLE_OFF = "#C7C7C7"
    COLOR_DIVIDER = "#EBEBEB"
    RADIUS_CARD = 8
    RADIUS_BTN = 6
    RADIUS_ICON = 8
    FONT_FAMILY = "Segoe UI"
    FONT_FAMILY_ZH = "Microsoft YaHei UI"
else:
    COLOR_BG = "#F5F5F7"
    COLOR_CARD = "#FFFFFF"
    COLOR_CARD_BORDER = "#E3E3E6"
    COLOR_SHADOW = "#E6E6EA"
    COLOR_TEXT = "#1D1D1F"
    COLOR_SUBTEXT = "#6E6E73"
    COLOR_ACCENT = "#007AFF"
    COLOR_ACCENT_HOVER = "#0066D6"
    COLOR_TOGGLE_OFF = "#D1D1D6"
    COLOR_DIVIDER = "#ECECEE"
    RADIUS_CARD = 16
    RADIUS_BTN = 10
    RADIUS_ICON = 12
    FONT_FAMILY = ".AppleSystemUIFont"
    FONT_FAMILY_ZH = "PingFang SC"

COLOR_SUCCESS = "#2E9B4E" if not IS_WIN else "#107C10"
COLOR_ERROR = "#D63A2E" if not IS_WIN else "#C42B1C"
COLOR_CODEX_ICON = "#3B82C4"
COLOR_CLAUDE_ICON = "#CC785C"


def family_for(lang):
    if lang == "zh-Hant":
        return "PingFang TC" if IS_MAC else FONT_FAMILY_ZH
    if lang == "zh-Hans":
        return FONT_FAMILY_ZH
    return FONT_FAMILY


# ---------------------------------------------------------------------------
# Canvas drawing helpers
# ---------------------------------------------------------------------------
def rounded_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def darken(hex_color, factor=0.85):
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r, g, b = int(r * factor), int(g * factor), int(b * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


class ToggleSwitch:
    def __init__(self, canvas, x, y, value=True, on_color=COLOR_ACCENT, off_color=COLOR_TOGGLE_OFF, command=None):
        self.canvas = canvas
        self.x, self.y = x, y
        self.w, self.h = 40, 22
        self.value = value
        self.on_color = on_color
        self.off_color = off_color
        self.command = command
        self.track_id = rounded_rect(canvas, x, y, x + self.w, y + self.h, self.h / 2,
                                      fill=self._track_color(), outline="")
        self.knob_id = canvas.create_oval(0, 0, 0, 0, fill="white", outline="")
        self._set_knob_pos(animate=False)
        for item in (self.track_id, self.knob_id):
            canvas.tag_bind(item, "<Button-1>", self._on_click)
            canvas.tag_bind(item, "<Enter>", lambda e: canvas.config(cursor="pointinghand" if IS_MAC else "hand2"))
            canvas.tag_bind(item, "<Leave>", lambda e: canvas.config(cursor=""))

    def _track_color(self):
        return self.on_color if self.value else self.off_color

    def _target_cx(self):
        pad = 2
        r = self.h / 2 - pad
        return (self.x + self.w - pad - r) if self.value else (self.x + pad + r)

    def _set_knob_pos(self, animate=True):
        pad = 2
        r = self.h / 2 - pad
        cy = self.y + self.h / 2
        target_cx = self._target_cx()
        if not animate:
            self.canvas.coords(self.knob_id, target_cx - r, cy - r, target_cx + r, cy + r)
            return
        coords = self.canvas.coords(self.knob_id)
        start_cx = (coords[0] + coords[2]) / 2 if coords else target_cx
        self._animate(target_cx, cy, r, start_cx, 0, 6)

    def _animate(self, target_cx, cy, r, start_cx, step, steps):
        if step > steps:
            self.canvas.coords(self.knob_id, target_cx - r, cy - r, target_cx + r, cy + r)
            return
        frac = step / steps
        cx = start_cx + (target_cx - start_cx) * frac
        self.canvas.coords(self.knob_id, cx - r, cy - r, cx + r, cy + r)
        self.canvas.after(9, lambda: self._animate(target_cx, cy, r, start_cx, step + 1, steps))

    def _on_click(self, event):
        self.set(not self.value)

    def set(self, value):
        self.value = value
        self.canvas.itemconfig(self.track_id, fill=self._track_color())
        self._set_knob_pos(animate=True)
        if self.command:
            self.command(self.value)

    def get(self):
        return self.value


class RoundedButton:
    def __init__(self, canvas, x, y, w, h, text, command, bg, fg="white", font=None, radius=RADIUS_BTN):
        self.canvas = canvas
        self.x, self.y, self.w, self.h = x, y, w, h
        self.command = command
        self.bg = bg
        self.hover_bg = darken(bg)
        self.disabled_bg = "#BFBFBF" if IS_WIN else "#C7C7CC"
        self.fg = fg
        self.enabled = True
        self.rect_id = rounded_rect(canvas, x, y, x + w, y + h, radius, fill=bg, outline="")
        self.text_id = canvas.create_text(x + w / 2, y + h / 2, text=text, fill=fg, font=font)
        for item in (self.rect_id, self.text_id):
            canvas.tag_bind(item, "<Enter>", self._on_enter)
            canvas.tag_bind(item, "<Leave>", self._on_leave)
            canvas.tag_bind(item, "<Button-1>", self._on_click)

    def _on_enter(self, event):
        if self.enabled:
            self.canvas.itemconfig(self.rect_id, fill=self.hover_bg)
            self.canvas.config(cursor="pointinghand" if IS_MAC else "hand2")

    def _on_leave(self, event):
        if self.enabled:
            self.canvas.itemconfig(self.rect_id, fill=self.bg)
        self.canvas.config(cursor="")

    def _on_click(self, event):
        if self.enabled and self.command:
            self.command()

    def set_text(self, text):
        self.canvas.itemconfig(self.text_id, text=text)

    def set_enabled(self, enabled):
        self.enabled = enabled
        self.canvas.itemconfig(self.rect_id, fill=self.bg if enabled else self.disabled_bg)


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------
WIN_W, WIN_H = 460, 410


class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.lang = detect_language()
        self.installing = False

        self.root.geometry(f"{WIN_W}x{WIN_H}")
        self.root.resizable(False, False)
        self.root.configure(bg=COLOR_BG)

        self.canvas = tk.Canvas(root, width=WIN_W, height=WIN_H, bg=COLOR_BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.lang_items = {}
        self.dynamic_texts = {}

        self._build_static_chrome()
        self._build_header()
        self._build_lang_switcher()
        self._build_card()
        self._build_button_and_status()
        self._build_footer()

        self.apply_language(self.lang)

    # -- fonts -------------------------------------------------------------
    def font(self, size, weight="normal"):
        return tkfont.Font(family=family_for(self.lang), size=size, weight=weight)

    # -- static chrome (things that never change with language) -----------
    def _build_static_chrome(self):
        c = self.canvas
        # icon badge
        rounded_rect(c, 28, 28, 28 + 44, 28 + 44, RADIUS_ICON, fill=COLOR_ACCENT, outline="")
        c.create_text(28 + 22, 28 + 23, text=">_", fill="white",
                       font=tkfont.Font(family="Menlo" if IS_MAC else "Consolas", size=15, weight="bold"))

    def _build_header(self):
        c = self.canvas
        self.dynamic_texts["app_title"] = c.create_text(
            86, 40, anchor="w", fill=COLOR_TEXT, text="")
        self.dynamic_texts["app_subtitle"] = c.create_text(
            86, 62, anchor="w", fill=COLOR_SUBTEXT, text="")

    def _build_lang_switcher(self):
        c = self.canvas
        x = WIN_W - 28
        self.lang_items = {}
        for code in reversed(LANGS):
            label = LANG_LABELS[code]
            item = c.create_text(x, 32, anchor="e", text=label)
            c.tag_bind(item, "<Button-1>", lambda e, code=code: self.apply_language(code))
            c.tag_bind(item, "<Enter>", lambda e: c.config(cursor="pointinghand" if IS_MAC else "hand2"))
            c.tag_bind(item, "<Leave>", lambda e: c.config(cursor=""))
            self.lang_items[code] = item
            bbox = c.bbox(item)
            x = bbox[0] - 12

    def _build_card(self):
        c = self.canvas
        self.card_y1, self.card_y2 = 100, 268
        x1, x2 = 28, WIN_W - 28
        rounded_rect(c, x1, self.card_y1 + 3, x2, self.card_y2 + 3, RADIUS_CARD, fill=COLOR_SHADOW, outline="")
        rounded_rect(c, x1, self.card_y1, x2, self.card_y2, RADIUS_CARD,
                     fill=COLOR_CARD, outline=COLOR_CARD_BORDER, width=1)

        row1_cy = self.card_y1 + 42
        row2_cy = self.card_y1 + 126
        divider_y = self.card_y1 + 84

        c.create_line(44, divider_y, x2 - 16, divider_y, fill=COLOR_DIVIDER)

        # row icons (monogram badges)
        rounded_rect(c, 44, row1_cy - 16, 44 + 32, row1_cy + 16, RADIUS_ICON - 2, fill=COLOR_CODEX_ICON, outline="")
        c.create_text(44 + 16, row1_cy, text="C", fill="white", font=tkfont.Font(size=13, weight="bold"))
        rounded_rect(c, 44, row2_cy - 16, 44 + 32, row2_cy + 16, RADIUS_ICON - 2, fill=COLOR_CLAUDE_ICON, outline="")
        c.create_text(44 + 16, row2_cy, text="A", fill="white", font=tkfont.Font(size=13, weight="bold"))

        text_x = 44 + 32 + 14
        self.dynamic_texts["codex_title"] = c.create_text(
            text_x, row1_cy - 10, anchor="w", fill=COLOR_TEXT, text="")
        self.dynamic_texts["codex_desc"] = c.create_text(
            text_x, row1_cy + 9, anchor="w", fill=COLOR_SUBTEXT, text="")
        self.dynamic_texts["claude_title"] = c.create_text(
            text_x, row2_cy - 10, anchor="w", fill=COLOR_TEXT, text="")
        self.dynamic_texts["claude_desc"] = c.create_text(
            text_x, row2_cy + 9, anchor="w", fill=COLOR_SUBTEXT, text="")

        toggle_x = x2 - 16 - 40
        self.toggle_codex = ToggleSwitch(c, toggle_x, row1_cy - 11, value=True)
        self.toggle_claude = ToggleSwitch(c, toggle_x, row2_cy - 11, value=True)

    def _build_button_and_status(self):
        c = self.canvas
        btn_y = self.card_y2 + 28
        self.btn = RoundedButton(
            c, 28, btn_y, WIN_W - 56, 46, "", self.start_install,
            bg=COLOR_ACCENT, font=None,
        )
        self.status_id = c.create_text(WIN_W / 2, btn_y + 46 + 22, fill=COLOR_SUBTEXT, text="")

    def _build_footer(self):
        c = self.canvas
        self.footer_id = c.create_text(WIN_W / 2, WIN_H - 22, fill=COLOR_SUBTEXT, text="")

    # -- language application ----------------------------------------------
    def apply_language(self, lang):
        self.lang = lang
        self.root.title(STRINGS[lang]["app_title"])

        f_title = self.font(17, "bold")
        f_sub = self.font(11)
        f_row_title = self.font(13, "bold")
        f_row_desc = self.font(10)
        f_btn = self.font(13, "bold")
        f_status = self.font(10)
        f_footer = self.font(9)
        f_lang = self.font(11, "bold")
        f_lang_inactive = self.font(11)

        c = self.canvas
        S = STRINGS[lang]
        c.itemconfig(self.dynamic_texts["app_title"], text=S["app_title"], font=f_title)
        c.itemconfig(self.dynamic_texts["app_subtitle"], text=S["app_subtitle"], font=f_sub)
        c.itemconfig(self.dynamic_texts["codex_title"], text=S["codex_title"], font=f_row_title)
        c.itemconfig(self.dynamic_texts["codex_desc"], text=S["codex_desc"], font=f_row_desc)
        c.itemconfig(self.dynamic_texts["claude_title"], text=S["claude_title"], font=f_row_title)
        c.itemconfig(self.dynamic_texts["claude_desc"], text=S["claude_desc"], font=f_row_desc)
        c.itemconfig(self.footer_id, text=S["footer_hint"], font=f_footer)

        if not self.installing:
            self.btn.set_text(S["install_button"])
        self.btn.canvas.itemconfig(self.btn.text_id, font=f_btn)
        c.itemconfig(self.status_id, text=STRINGS[lang]["status_idle"], font=f_status)

        for code, item in self.lang_items.items():
            active = code == lang
            c.itemconfig(item, fill=COLOR_ACCENT if active else COLOR_SUBTEXT,
                         font=f_lang if active else f_lang_inactive)

    # -- status helper -------------------------------------------------------
    def set_status(self, text, color):
        self.canvas.itemconfig(self.status_id, text=text, fill=color)

    # -- install lifecycle ---------------------------------------------------
    def start_install(self):
        if self.installing:
            return
        S = STRINGS[self.lang]
        do_codex = self.toggle_codex.get()
        do_claude = self.toggle_claude.get()
        if not do_codex and not do_claude:
            return

        self.installing = True
        self.btn.set_enabled(False)
        self.btn.set_text(S["installing_button"])
        self.set_status(S["status_installing_codex"] if do_codex else S["status_installing_claude"], COLOR_SUBTEXT)

        thread = threading.Thread(target=self._install_worker, args=(do_codex, do_claude), daemon=True)
        thread.start()

    def _install_worker(self, do_codex, do_claude):
        S = STRINGS[self.lang]
        try:
            if do_codex:
                self.root.after(0, lambda: self.set_status(S["status_installing_codex"], COLOR_SUBTEXT))
                install_codex()
            if do_claude:
                self.root.after(0, lambda: self.set_status(S["status_installing_claude"], COLOR_SUBTEXT))
                install_claude_code()
            self.root.after(0, self._on_install_success)
        except Exception as e:
            err = str(e)
            self.root.after(0, lambda: self._on_install_error(err))

    def _on_install_success(self):
        S = STRINGS[self.lang]
        self.installing = False
        self.btn.set_enabled(True)
        self.btn.set_text(S["install_button"])
        self.set_status(S["status_done"], COLOR_SUCCESS)
        bin_dir, _ = get_install_dirs()
        messagebox.showinfo(S["success_title"], S["success_body"].format(path=bin_dir))

    def _on_install_error(self, err):
        S = STRINGS[self.lang]
        self.installing = False
        self.btn.set_enabled(True)
        self.btn.set_text(S["install_button"])
        self.set_status(S["status_failed"], COLOR_ERROR)
        messagebox.showerror(S["error_title"], S["error_body"].format(error=err))


if __name__ == "__main__":
    root = tk.Tk()
    app = InstallerApp(root)
    root.mainloop()
