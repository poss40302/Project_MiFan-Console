import sys
import os
import subprocess
import time

# 引入 HUD API
sys.path.append(r"F:\OtherProject\Build_HUD")
try:
    from hud_api import BuildHUD_API
except ImportError:
    print(r"Error: Could not find hud_api.py in F:\OtherProject\Build_HUD")
    sys.exit(1)

def run_build():
    json_path = os.path.abspath("build_status.json")
    hud_api = BuildHUD_API(json_path, project_name="MiFan Console")
    hud_api.update(version="v1.9.0426c", status="準備封裝...")
    
    # 清理舊的 build 目錄以防 AssertionError
    import shutil
    if os.path.exists("build"):
        try:
            shutil.rmtree("build")
            hud_api.update(last_log="已清理舊的 build 目錄")
        except Exception as e:
            hud_api.update(last_log=f"清理失敗: {e}")
    
    # 啟動 HUD 視窗 (背景)
    hud_script = r"F:\OtherProject\Build_HUD\build_hud.py"
    subprocess.Popen([sys.executable, hud_script, json_path])
    time.sleep(2)

    # 定義階段
    hud_api.add_stage("Env Check", "done")
    hud_api.add_stage("Sourcing", "pending")
    hud_api.add_stage("C-Gen", "pending")
    hud_api.add_stage("Compiling", "pending")
    hud_api.add_stage("Onefile", "pending")

    # --- Sourcing ---
    hud_api.update_stage("Sourcing", "running")
    hud_api.update(progress=15, status="分析依賴中...", last_log="Tracking imports for main.py...")
    
    nuitka_cmd = [
        r".\.venv\Scripts\python.exe", "-m", "nuitka",
        "--onefile",
        "--windows-disable-console",
        "--enable-plugin=pyqt6",
        "--include-data-dir=Resourse=Resourse",
        "--windows-icon-from-ico=Resourse/mifan_app_icon.ico",
        "--output-dir=build",
        "--output-filename=MiFan-Console.exe",
        "main.py"
    ]

    # 執行 Nuitka 並監控輸出
    process = subprocess.Popen(nuitka_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
    
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            clean_line = line.strip()
            print(clean_line) # Print for debugging
            hud_api.update(last_log=clean_line)
            
            # 根據輸出更新進度
            if "Completed Python level compilation" in clean_line:
                hud_api.update_stage("Sourcing", "done")
                hud_api.update_stage("C-Gen", "running")
                hud_api.update(progress=40, status="正在生成 C 代碼...")
            elif "Generating source code for C backend" in clean_line:
                hud_api.update(progress=50)
            elif "Running C compilation" in clean_line:
                hud_api.update_stage("C-Gen", "done")
                hud_api.update_stage("Compiling", "running")
                hud_api.update(progress=65, status="編譯二進位檔案...")
            elif "Creating single file" in clean_line:
                hud_api.update_stage("Compiling", "done")
                hud_api.update_stage("Onefile", "running")
                hud_api.update(progress=90, status="壓縮 Onefile 封裝...")

    if process.returncode == 0:
        hud_api.update_stage("Onefile", "done")
        hud_api.update(progress=100, status="✨ 打包完成 (Success)", last_log="Executable ready in build folder.")
        # Move to release
        try:
            if os.path.exists(r"release\MiFan-Console.exe"):
                os.remove(r"release\MiFan-Console.exe")
            os.rename(r"build\MiFan-Console.exe", r"release\MiFan-Console.exe")
            hud_api.update(last_log="Deployed to release folder.")
        except Exception as e:
            hud_api.update(last_log=f"Deploy error: {e}")
    else:
        hud_api.update(status="❌ 打包失敗 (Failed)", last_log=f"Exit code: {process.returncode}")

if __name__ == "__main__":
    run_build()
