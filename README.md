# 🛸 MiFan-Console (MiFanCommander)

[![Version](https://img.shields.io/badge/version-v1.9.0426c-cyan.svg)](https://github.com/)

MiFan-Console 是一款專為「智米風扇」打造的高科技感、懸浮式桌上型控制器 (HUD)。它擁有流暢的形態變換動畫與極速的響應性能，讓您在 Windows 桌面上就能精準掌控涼風。

## 📥 下載與執行
若您只想直接使用工具，請至以下路徑下載已封裝好的執行檔：
- [MiFan-Console.exe](release/MiFan-Console.exe) (點擊進入後點 Download 即可)

## 📋 支援設備 (Supported Models)
本工具目前針對以下型號進行精調與適配：
- **智米直流變頻落地扇 1X** (型號識別碼：`dmaker.fan.p5`) —— **此型號為開發者測試基準 (Test Base)**
- **智米直流變頻落地扇 2 / 2L / 1C** (同屬 p5 協定系列)

> [!NOTE]
> 其他採用相同 dmaker 協定的風扇型號或許能部分相容，但我們僅保證在 `p5` 系列上的操控體驗。

## ⚙️ 設備設定 (獲取 IP 與 Token)
> [!IMPORTANT]
> **連線前提**：您的電腦與風扇必須連接在 **同一個區域網路 (相同 Wi-Fi 或路由器)** 下。本工具採用區域網路協定通訊，不支援跨網路遠端操控。

本工具需要您提供風扇的連線資訊，建議透過以下方式獲取：
1. 下載 [Xiaomi Cloud Tokens Extractor](https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor)。
2. 執行工具並登入您的小米帳號。
3. 複製對應風扇的 `IP` 與 `Token`。
4. 在 MiFan-Console 右鍵選單的「通訊設定」中填入。

## 🛠️ 開發者指南 (再製環境)
若您想要自行修改代碼或重新編譯，您的環境需要：
- **Python**: 3.13 或 3.14+
- **依賴套件**:
  ```bash
  pip install PyQt6 python-miio netifaces
  ```
- **核心架構**:
  - `main.py`: UI 邏輯與動畫系統。
  - `backend.py`: Miio 協定處理與異步通訊。
  - `build_with_hud.py`: 整合 [Build_HUD](https://github.com/poss40302/Build_HUD) 的視覺化編譯腳本。
  - `Resourse/`: UI 所需之科技感圖素資源。
  - `HandoverManual_V19.md`: 詳細的技術決策與維護手冊。

## ✨ 核心特色
- **Smart Ack 同步技術**：結合「物理按壓鎖定」與「狀態達標釋放」，徹底解決 UI 回彈問題。
- **模式專屬記憶 (Mode Memory)**：為「直吹風」與「自然風」分別記憶風速設定，切換模式時自動還原，無須重新調整。
- **動態旋轉回饋**：HUD 中心風扇圖示會根據實際風速實時調整旋轉速率，提供直觀的運作反饋。
- **雙層連線診斷**：精確辨識區域網路中斷與設備離線狀態。
- **滑動式啟動監控**：內建 `emergency_log` 系統，自動循環保留最後 5 次啟動紀錄，兼顧偵錯與輕量。
- **極速響應**：採用中斷驅動機制，指令發送近乎零延遲。

---
*Developed for Commanders who value both aesthetics and performance.*

---
> [!NOTE]
> 更多詳細資訊、操作指南與常見問題排除 (FAQ)，請參閱：[UserManual.md](UserManual.md)
