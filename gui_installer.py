import os
import sys
import platform
import tarfile
import zipfile
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

# Detect environment
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

class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Tools Offline Installer")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        style = ttk.Style()
        style.theme_use('clam')
        
        title = ttk.Label(root, text="AI Tools One-Click Installer", font=("Helvetica", 16, "bold"))
        title.pack(pady=20)
        
        self.var_codex = tk.BooleanVar(value=True)
        self.var_claude = tk.BooleanVar(value=True)
        
        cb_codex = ttk.Checkbutton(root, text="Install Codex CLI", variable=self.var_codex)
        cb_codex.pack(anchor="w", padx=50, pady=10)
        
        cb_claude = ttk.Checkbutton(root, text="Install Claude Code CLI", variable=self.var_claude)
        cb_claude.pack(anchor="w", padx=50, pady=10)
        
        self.btn_install = ttk.Button(root, text="Install Now", command=self.run_install)
        self.btn_install.pack(pady=30)
        
        self.lbl_status = ttk.Label(root, text="", foreground="gray")
        self.lbl_status.pack()

    def run_install(self):
        self.btn_install.config(state="disabled")
        self.lbl_status.config(text="Installing... Please wait.")
        self.root.update()
        
        try:
            if self.var_codex.get():
                self.lbl_status.config(text="Installing Codex...")
                self.root.update()
                install_codex()
                
            if self.var_claude.get():
                self.lbl_status.config(text="Installing Claude Code (Node.js)...")
                self.root.update()
                install_claude_code()
                
            self.lbl_status.config(text="Installation Complete!", foreground="green")
            msg = "Installation successful!\n\n"
            if IS_MAC:
                msg += "Binaries are installed to ~/.local/bin.\n"
                msg += "Please restart your terminal to use 'codex' and 'claude'."
            else:
                msg += "Binaries are installed to %LOCALAPPDATA%\\Programs\\ai_tools_bin.\n"
                msg += "PATH has been updated. Please restart your terminal."
                
            messagebox.showinfo("Success", msg)
        except Exception as e:
            self.lbl_status.config(text="Installation Failed!", foreground="red")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        finally:
            self.btn_install.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = InstallerApp(root)
    root.mainloop()
