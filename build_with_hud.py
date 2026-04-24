import subprocess
import os
import sys
import time

# --- MODULAR HUD FALLBACK SYSTEM ---
# 優先嘗試載入視覺化 HUD 模組
HAS_HUD = False
try:
    # 支援將 Build_HUD 放在專案根目錄或父目錄
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from Build_HUD.hud_api import BuildHUD_API
    HAS_HUD = True
except (ImportError, ModuleNotFoundError):
    # 如果找不到 HUD 模組，則定義一個偽類 (Mock) 降級為控制台輸出
    class BuildHUD_API:
        def __init__(self, *args, **kwargs):
            print(f"--- Starting Build: {kwargs.get('project_name', 'Unknown')} ---")
        def update(self, **kwargs):
            status = kwargs.get('status', '')
            progress = kwargs.get('progress', '')
            if status: print(f">> {status} {f'({progress}%)' if progress else ''}")
        def add_stage(self, *args, **kwargs): pass
        def update_stage(self, *args, **kwargs): pass

def run_build():
    json_path = os.path.abspath("build_status.json")
    hud_api = BuildHUD_API(json_path, project_name="MiFan Console")
    hud_api.update(version="v1.9.0426c", status="準備封裝...")
    
    # 清理舊的 build 目錄以防 AssertionError
    import shutil
    if os.path.exists("build"):
        try:
            shutil.rmtree("build")
            hud_api.update(status="已清理舊的 Build 目錄")
        except: pass

    # Nuitka 打包指令
    nuitka_cmd = [
        r".\.venv\Scripts\python.exe", "-m", "nuitka",
        "--onefile",
        "--windows-disable-console",
        "--enable-plugin=pyqt6",
        "--include-data-dir=Resourse=Resourse",
        "--windows-icon-from-ico=Resourse/mifan_app_icon.ico",
        "--output-dir=build",
        "--windows-uac-admin", # 如果需要管理員權限
        "main.py"
    ]

    hud_api.update(status="正在執行 Nuitka 編譯 (這可能需要幾分鐘)...", progress=10)
    
    process = subprocess.Popen(
        nuitka_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8"
    )

    # 監控日誌並簡單估算進度 (Nuitka 沒有標準進度輸出，我們用關鍵字粗略模擬)
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            # print(line.strip()) # 如果想看詳細日誌可以取消註釋
            if "Scons: Compiling" in line: hud_api.update(status="編譯 C 代碼...", progress=40)
            if "Creating single file" in line: hud_api.update(status="正在封裝單一執行檔...", progress=80)

    if process.returncode == 0:
        # 搬運產物到 release
        os.makedirs("release", exist_ok=True)
        target_exe = os.path.join("build", "MiFan-Console.exe")
        if os.path.exists(target_exe):
            shutil.copy(target_exe, os.path.join("release", "MiFan-Console.exe"))
            hud_api.update(progress=100, status="打包成功！產物已存至 release/", done=True)
        else:
            hud_api.update(status="錯誤：找不到產出的 .exe 檔案", progress=0)
    else:
        hud_api.update(status=f"編譯失敗，Exit Code: {process.returncode}", progress=0)

if __name__ == "__main__":
    run_build()
