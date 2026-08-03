# KIAUH - Klipper 安裝與更新助手

<p align="center">
  <a>
    <img src="docs/assets/logo-large.png" alt="KIAUH logo" height="181">
    <h1 align="center">Klipper Installation And Update Helper</h1>
  </a>
</p>

<p align="center">
  一個方便的安裝腳本，讓安裝 Klipper（以及更多元件）變得輕鬆！
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README_zh.md">简体中文</a> ·
  <a href="README_zh_Hant.md">繁體中文</a>
</p>

<p align="center">
  <a><img src="https://img.shields.io/github/license/dw-0/kiauh"></a>
  <a><img src="https://img.shields.io/github/stars/dw-0/kiauh"></a>
  <a><img src="https://img.shields.io/github/forks/dw-0/kiauh"></a>
  <a><img src="https://img.shields.io/github/languages/top/dw-0/kiauh?logo=gnubash&logoColor=white"></a>
  <a><img src="https://img.shields.io/github/v/tag/dw-0/kiauh"></a>
  <br />
  <a><img src="https://img.shields.io/github/last-commit/dw-0/kiauh"></a>
  <a><img src="https://img.shields.io/github/contributors/dw-0/kiauh"></a>
</p>

## 📄 使用說明

### 📋 系統需求

KIAUH 是一個協助你在 Linux 系統上安裝 Klipper 的腳本工具。它需要一個已經寫入到樹莓派（或其他 SBC）SD 卡中的可用 Linux 系統。

若你使用樹莓派，推薦使用 `Raspberry Pi OS Lite (32-bit 或 64-bit)`。
[官方 Raspberry Pi Imager](https://www.raspberrypi.com/software/) 是最簡單的寫入方式。

### 💾 下載並使用 KIAUH

使用此腳本需自行承擔風險。

1. 安裝 git：

```shell
sudo apt-get update && sudo apt-get install git -y
```

2. 下載到 home 目錄：

```shell
cd ~ && git clone https://github.com/dw-0/kiauh.git
```

3. 啟動：

```shell
./kiauh/kiauh.sh
```

4. 在主選單中，輸入對應的選項並按 ENTER。

### 🌐 語言 / 在地化

KIAUH 內建語言選擇器：

- 在主選單按 `L` 開啟語言清單（English / 简体中文 / 繁體中文）
- 或進入 `S) [設定]` → 選項 `6) 語言`

KIAUH 使用 Python 標準函式庫 `gettext`。若某些字串尚未翻譯，會安全回退顯示英文（不會造成程式崩潰）。

## ❗ 注意事項

### 📋 請查看 [更新日誌](docs/changelog.md) 以了解可能的重要變更！

- 主要在 Raspberry Pi OS Lite（Debian 10 Buster / Debian 11 Bullseye）上測試
  - 其他基於 Debian 的發行版（例如 Ubuntu 20 到 22）通常也可運作
  - Armbian 也有回報可用，但未詳細測試
- 使用過程會要求輸入 sudo 密碼，因為部分功能需要 sudo 權限

如需完整元件清單與更多說明，請參考英文版 [README.md](README.md)。

