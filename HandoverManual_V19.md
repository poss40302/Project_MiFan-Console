# MiFan-Console v1.9.0426c 開發交接手冊

## 1. 版本概覽
- **版本號**：v1.9.0426c (穩定修復版)
- **核心目標**：解決 UI 回彈與閃退問題、實作模式風速記憶、建立通用建置 HUD 工具。

## 2. 關鍵技術決策與實作

### A. 模式專屬風速記憶 (Mode-Specific Memory)
- **背景**：指揮官發現切換「直吹風」與「自然風」時，風速會互相干擾。
- **實作**：
    - 新增 `mem_normal_speed` 與 `mem_nature_speed` 變數（初始 25%）。
    - 在滑桿變動（含滾輪）與後台 Idle 狀態同步時，自動更新當前模式的記憶值。
    - `toggle_mode` 時，執行「模式切換 + 風速還原」的連動指令。

### B. 啟動閃退修復 (Path & Log Hardening)
- **問題**：Nuitka `onefile` 打包後，相對路徑失效且日誌寫入權限受限。
- **解決**：
    - **頂層日誌預熱**：在 `import` 之前即啟動 `emergency_log`，確保崩潰前能留下資訊。
    - **全絕對路徑化**：所有設定與日誌強制導向 `%APPDATA%\Project_MiFan_Console\`。
    - **資源定位器**：實作 `discover_res_dir()`，動態掃描臨時目錄與執行目錄。

### C. 啟動日誌旋轉 (Log Rotation)
- **實作**：`mifan_startup.log` 採用「滑動視窗」機制，透過識別 `Process started` 字串，永遠只保留最後 **5 次** 啟動紀錄，避免檔案無限生長。

### D. Build_HUD 監控模組
- **位置**：`F:\OtherProject\Build_HUD`
- **特性**：
    - 獨立於主專案，具備 `Single Instance` 鎖定機制（基於 JSON 路徑 Hash）。
    - 支援 `QLocalServer` 喚醒功能，若重複開啟打包工具，舊 HUD 會自動跳至最前方。

## 3. 環境與部署
- **Python 版本**：3.14 (Experimental)
- **封裝命令**：見 `build_with_hud.py`，已配置 `Resourse` 目錄嵌入與圖標設定。
- **依賴項**：`PyQt6`, `python-miio`, `netifaces`。

## 4. 維護者提醒
- **圖標更新**：若要修改 Toggle 選單圖標，需同步確認 `on_status_updated` 與 `toggle_mode` 中的邏輯映射。
- **日誌控制**：右鍵選單的「輸出偵錯日誌」為開關 `config.json` 中的 `log_enabled` 欄位，需重啟程式後後台執行緒才會根據此欄位決定是否寫入檔案。

---
*Last Updated: 2026-04-24 by Antigravity*
