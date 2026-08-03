#!/usr/bin/env python3
"""
Generate zh_CN.po (Simplified Chinese / 简体中文) and zh_TW.po
(Traditional Chinese / 繁體中文) translation catalogs from messages.pot.

Usage
-----
  1. Full build from existing .pot (default — no subprocess):
         python3 build_translations.py

  2. After merging upstream into your soft fork — refresh the transcript:
         python3 build_translations.py --rebase

     --rebase runs:
       a) xgettext to extract a fresh kiauh/locale/messages.pot
          (picks up any NEW English strings upstream added in new code)
       b) msgmerge --previous --update for zh_CN.po AND zh_TW.po
          (fuzzy-matches existing translations, new strings are empty/fuzzy)
       c) prints a summary of newly-fuzzy / still-untranslated entries
          for you to hand-edit in Poedit / vim / gtranslator
       d) re-rules our zh_CN/zh_TW translator over the newly untranslated
          entries (the rule-based step), overwriting empty msgstrs

  3. Just re-run msgmerge step with existing .pot + .po (no rebuild):
         python3 build_translations.py --merge

  4. Just extract .pot (for translators / review):
         python3 build_translations.py --extract

Design principles
-----------------
- Keep ALL proper nouns in EN: Klipper, Klippy, Moonraker, Mainsail, Fluidd,
  KlipperScreen, Crowsnest, OctoPrint, OctoEverywhere, OctoApp, Obico,
  Mobileraker, Moongate, DroidKlipp, PrettyGCode, SimplyPrint, Spoolman,
  Telegram, TMC, BTT, LDO, Raspberry Pi, Python, GitHub, Git, Nginx,
  Systemd, Debian, Ubuntu, Docker, Docker-compose, Node.js, NPM, ADB, APK,
  Polkit, Ko-fi, HomeKit, etc.
- Brand/model names also stay EN where they are identifiers (BTT GTR, etc.)
- Shell commands, paths, URLs stay EN
- UI chrome: (Y/n) → (是/否) style if appropriate, but keep the letter choices
  Q) / B) / H) intact as they map to keyboard keys
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

LOCALE_DIR = Path(__file__).resolve().parent / "kiauh" / "locale"
POT_FILE = LOCALE_DIR / "messages.pot"
ZH_CN_PO = LOCALE_DIR / "zh_CN" / "LC_MESSAGES" / "messages.po"
ZH_TW_PO = LOCALE_DIR / "zh_TW" / "LC_MESSAGES" / "messages.po"


# ---------------------------------------------------------------------------
# Glossary: source substring -> (zh_CN translation, zh_TW translation)
# Order matters. Longer/more specific patterns first.
# ---------------------------------------------------------------------------
GLOSSARY: List[Tuple[re.Pattern, Tuple[str, str]]] = [
    #
    # Titles / top-level concepts
    #
    (re.compile(r"\[ KIAUH \]"), ("[ KIAUH ]", "[ KIAUH ]")),
    (re.compile(r"Klipper Installation And Update Helper"),
     ("Klipper 安装与更新助手", "Klipper 安裝與更新助手")),
    (re.compile(r"Main Menu"), ("主菜单", "主選單")),
    (re.compile(r"Installation Menu"), ("安装菜单", "安裝選單")),
    (re.compile(r"Update Menu"), ("更新菜单", "更新選單")),
    (re.compile(r"Remove Menu"), ("移除菜单", "移除選單")),
    (re.compile(r"Advanced Menu"), ("高级菜单", "進階選單")),
    (re.compile(r"Backup Menu"), ("备份菜单", "備份選單")),
    (re.compile(r"Settings Menu"), ("设置菜单", "設定選單")),
    (re.compile(r"Extensions Menu"), ("扩展菜单", "擴充選單")),
    (re.compile(r"Log-Upload Menu"), ("日志上传菜单", "日誌上傳選單")),
    (re.compile(r"Repo Select Menu"), ("仓库选择菜单", "倉庫選擇選單")),
    (re.compile(r"Firmware"), ("固件", "韌體")),

    #
    # Navigation chrome – keep key letters, translate the description
    #
    (re.compile(r"Q\) Quit"), ("Q) 退出", "Q) 退出")),
    (re.compile(r"B\) « Back"), ("B) « 返回", "B) « 返回")),
    (re.compile(r"H\) Help \[\?\]"), ("H) 帮助 [?]", "H) 說明 [?]")),
    (re.compile(r"Perform action"), ("请选择操作", "請選擇操作")),

    #
    # Menu section labels (used in ASCII-art menu boxes)
    #
    (re.compile(r"Firmware & API:"), ("固件与 API:", "韌體與 API:")),
    (re.compile(r"Touchscreen GUI:"), ("触摸屏界面:", "觸控螢幕介面:")),
    (re.compile(r"Webinterface:"), ("网页界面:", "網頁介面:")),
    (re.compile(r"Client-Config:"), ("客户端配置:", "客戶端設定:")),
    (re.compile(r"Webcam Streamer:"), ("摄像头串流:", "攝影機串流:")),
    (re.compile(r"Install unstable releases:"), ("安装不稳定版本:", "安裝不穩定版本:")),
    (re.compile(r"Auto-Backup:"), ("自动备份:", "自動備份:")),
    (re.compile(r"Language:"), ("语言:", "語言:")),
    (re.compile(r"Community:"), ("社区扩展:", "社群擴充:")),
    (re.compile(r"Changelog:"), ("更新日志:", "更新日誌:")),
    (re.compile(r"Current repository:"), ("当前仓库:", "目前倉庫:")),
    (re.compile(r"Repo:"), ("仓库:", "倉庫:")),
    (re.compile(r"Branch:"), ("分支:", "分支:")),
    (re.compile(r"Owner:"), ("所有者:", "擁有者:")),

    #
    # Menu action labels (format: number/letter) [Action]
    #
    (re.compile(r"Log-Upload"), ("日志上传", "日誌上傳")),
    (re.compile(r"Install"), ("安装", "安裝")),
    (re.compile(r"Update"), ("更新", "更新")),
    (re.compile(r"Remove"), ("移除", "移除")),
    (re.compile(r"Advanced"), ("高级", "進階")),
    (re.compile(r"Backup"), ("备份", "備份")),
    (re.compile(r"Settings"), ("设置", "設定")),
    (re.compile(r"Extensions"), ("扩展", "擴充")),
    (re.compile(r"Not available!"), ("不可用！", "無法使用！")),

    #
    # DialogType labels (Logger dialog titles)
    #
    (re.compile(r"^INFO$"), ("信息", "資訊")),
    (re.compile(r"^SUCCESS$"), ("成功", "成功")),
    (re.compile(r"^ATTENTION$"), ("注意", "注意")),
    (re.compile(r"^WARNING$"), ("警告", "警告")),
    (re.compile(r"^ERROR$"), ("错误", "錯誤")),

    #
    # Component statuses
    #
    (re.compile(r"^Not installed$"), ("未安装", "未安裝")),
    (re.compile(r"^Incomplete$"), ("不完整", "不完整")),
    (re.compile(r"^Installed$"), ("已安装", "已安裝")),

    #
    # Common short strings / answers
    #
    (re.compile(r"\(Y/n\)"), ("(是/否，默认是)", "(是/否，預設是)")),
    (re.compile(r"\(y/N\)"), ("(是/否，默认否)", "(是/否，預設否)")),
    (re.compile(r"\bdefault\b"), ("默认值", "預設值")),
    (re.compile(r"Happy printing!"), ("打印愉快！", "列印愉快！")),
    (re.compile(r"Exiting Klipper setup \.\.\."), ("正在退出 Klipper 安装程序 ...", "正在退出 Klipper 安裝程序 ...")),
    (re.compile(r"Exiting Moonraker setup \.\.\."), ("正在退出 Moonraker 安装程序 ...", "正在退出 Moonraker 安裝程序 ...")),
    (re.compile(r"Invalid choice\. Please select a valid value\."),
     ("选择无效。请输入一个有效数值。", "選擇無效。請輸入一個有效數值。")),
    (re.compile(r"Invalid option! Please select a valid option\."),
     ("选项无效！请选择一个有效选项。", "選項無效！請選擇一個有效選項。")),
    (re.compile(r"Input must not be empty!"), ("输入不能为空！", "輸入不可為空！")),
    (re.compile(r"This value is already in use/reserved\."),
     ("该值已被占用或保留。", "該值已被使用或保留。")),
    (re.compile(r"Invalid option_list type"),
     ("option_list 类型无效", "option_list 型別無效")),

    #
    # Verbs (passive / active)
    #
    (re.compile(r"Switch Klipper source repository"),
     ("切换 Klipper 源码仓库", "切換 Klipper 原始碼倉庫")),
    (re.compile(r"Switch Moonraker source repository"),
     ("切换 Moonraker 源码仓库", "切換 Moonraker 原始碼倉庫")),
    (re.compile(r"Backup before update"), ("更新前备份", "更新前備份")),
    (re.compile(r"Create example printer\.cfg\?"), ("是否创建示例 printer.cfg？", "是否建立範例 printer.cfg？")),
    (re.compile(r"Select Klipper instance to setup Moonraker for"),
     ("选择要为其设置 Moonraker 的 Klipper 实例",
      "選擇要為其設定 Moonraker 的 Klipper 執行個體")),

    #
    # Prefix-style statuses used in Logger.print_status
    #
    (re.compile(r"Launching crowsnest's install configurator \.\.\."),
     ("正在启动 crowsnest 安装配置工具 ...", "正在啟動 crowsnest 安裝設定工具 ...")),
    (re.compile(r"Launching crowsnest installer \.\.\."),
     ("正在启动 crowsnest 安装程序 ...", "正在啟動 crowsnest 安裝程式 ...")),
    (re.compile(r"Installer will prompt you for sudo password!"),
     ("安装程序接下来将要求输入 sudo 密码！", "安裝程式接下來將要求輸入 sudo 密碼！")),
    (re.compile(r"Multi instance install detected!"),
     ("检测到多实例安装！", "偵測到多重執行個體安裝！")),
    (re.compile(r"The following instances were found:"),
     ("发现以下实例：", "找到以下執行個體：")),
    (re.compile(r"Updating Crowsnest \.\.\."), ("正在更新 Crowsnest ...", "正在更新 Crowsnest ...")),
    (re.compile(r"Generating \.config failed, installation aborted"),
     ("生成 .config 失败，已中止安装", "產生 .config 失敗，已中止安裝")),
    (re.compile(r"Do you want to continue with the installation\?"),
     ("是否继续进行安装？", "是否繼續進行安裝？")),
    (re.compile(r"Crowsnest installation aborted!"),
     ("Crowsnest 安装已中止！", "Crowsnest 安裝已中止！")),
    (re.compile(r"Something went wrong! Please try again\.\.\.\n\{\}"),
     ("出现错误！请重试...\n{}", "發生錯誤！請重試...\n{}")),

    #
    # Broad catch-all phrases
    #
    (re.compile(r"aborted"), ("已中止", "已中止")),
    (re.compile(r"failed"), ("失败", "失敗")),
    (re.compile(r"succeeded"), ("成功", "成功")),
    (re.compile(r"successfully"), ("成功", "成功")),
    (re.compile(r"Finished"), ("完成", "完成")),
    (re.compile(r"Instance"), ("实例", "執行個體")),
    (re.compile(r"instances"), ("实例", "執行個體")),
    (re.compile(r"installation"), ("安装", "安裝")),
    (re.compile(r"Installation"), ("安装", "安裝")),
    (re.compile(r"removal"), ("移除", "移除")),
    (re.compile(r"Removal"), ("移除", "移除")),
    (re.compile(r"configuration"), ("配置", "設定")),
    (re.compile(r"Configuration"), ("配置", "設定")),
    (re.compile(r"repositories"), ("仓库", "倉庫")),
    (re.compile(r"Repository"), ("仓库", "倉庫")),
    (re.compile(r"repository"), ("仓库", "倉庫")),
    (re.compile(r"directory"), ("目录", "目錄")),
    (re.compile(r"Directory"), ("目录", "目錄")),
    (re.compile(r"download"), ("下载", "下載")),
    (re.compile(r"Download"), ("下载", "下載")),
    (re.compile(r"update"), ("更新", "更新")),
    (re.compile(r"backup"), ("备份", "備份")),
    (re.compile(r"Backup"), ("备份", "備份")),
    (re.compile(r"restore"), ("恢复", "還原")),
    (re.compile(r"Restore"), ("恢复", "還原")),
    (re.compile(r"password"), ("密码", "密碼")),
    (re.compile(r"Password"), ("密码", "密碼")),
    (re.compile(r"hostname"), ("主机名", "主機名稱")),
    (re.compile(r"Hostname"), ("主机名", "主機名稱")),
    (re.compile(r"printer"), ("打印机", "印表機")),
    (re.compile(r"Printer"), ("打印机", "印表機")),
    (re.compile(r"firmware"), ("固件", "韌體")),
    (re.compile(r"Firmware"), ("固件", "韌體")),
    (re.compile(r"build"), ("构建", "建置")),
    (re.compile(r"Build"), ("构建", "建置")),
    (re.compile(r"flash"), ("烧录", "燒錄")),
    (re.compile(r"Flash"), ("烧录", "燒錄")),
    (re.compile(r"upload"), ("上传", "上傳")),
    (re.compile(r"Upload"), ("上传", "上傳")),
    (re.compile(r"log"), ("日志", "日誌")),
    (re.compile(r"Log"), ("日志", "日誌")),
    (re.compile(r"port"), ("端口", "連接埠")),
    (re.compile(r"Port"), ("端口", "連接埠")),
    (re.compile(r"language"), ("语言", "語言")),
    (re.compile(r"Language"), ("语言", "語言")),
    (re.compile(r"question"), ("问题", "問題")),
    (re.compile(r"Question"), ("问题", "問題")),
    (re.compile(r"confirm"), ("确认", "確認")),
    (re.compile(r"Confirm"), ("确认", "確認")),
    (re.compile(r"cancel"), ("取消", "取消")),
    (re.compile(r"Cancel"), ("取消", "取消")),
    (re.compile(r"enabled"), ("已启用", "已啟用")),
    (re.compile(r"Enabled"), ("已启用", "已啟用")),
    (re.compile(r"disabled"), ("已禁用", "已停用")),
    (re.compile(r"Disabled"), ("已禁用", "已停用")),
    (re.compile(r"complete"), ("完成", "完成")),
    (re.compile(r"Complete"), ("完成", "完成")),
    (re.compile(r"available"), ("可用", "可用")),
    (re.compile(r"Available"), ("可用", "可用")),
    (re.compile(r"custom"), ("自定义", "自訂")),
    (re.compile(r"Custom"), ("自定义", "自訂")),
    (re.compile(r"option"), ("选项", "選項")),
    (re.compile(r"Option"), ("选项", "選項")),
    (re.compile(r"system"), ("系统", "系統")),
    (re.compile(r"System"), ("系统", "系統")),
    (re.compile(r"service"), ("服务", "服務")),
    (re.compile(r"Service"), ("服务", "服務")),
    (re.compile(r"migration"), ("迁移", "遷移")),
    (re.compile(r"Migration"), ("迁移", "遷移")),
    (re.compile(r"deprecated"), ("已弃用", "已棄用")),
    (re.compile(r"Deprecated"), ("已弃用", "已棄用")),

    #
    # Short catch-all words used in menu options
    #
    (re.compile(r"boards?"), ("主板", "主板")),
    (re.compile(r"Boards?"), ("主板", "主板")),
    (re.compile(r"microcontroller|MCU"), ("MCU", "MCU")),
    (re.compile(r"controller board"), ("控制主板", "控制主板")),
    (re.compile(r"baud ?rate"), ("波特率", "鮑率")),
    (re.compile(r"Baudrate|Baud rate"), ("波特率", "鮑率")),
    (re.compile(r"USB"), ("USB", "USB")),
    (re.compile(r"UART"), ("UART", "UART")),
    (re.compile(r"DFU"), ("DFU", "DFU")),
    (re.compile(r"RP2040|RP2 ?Boot"), ("RP2040", "RP2040")),
    (re.compile(r"serial"), ("串口", "序列埠")),
    (re.compile(r"Serial"), ("串口", "序列埠")),
    (re.compile(r"dependencies"), ("依赖项", "相依套件")),
    (re.compile(r"Dependencies"), ("依赖项", "相依套件")),
    (re.compile(r"packages?"), ("包", "套件")),
    (re.compile(r"Packages?"), ("包", "套件")),
    (re.compile(r"symlink"), ("符号链接", "符號連結")),
    (re.compile(r"Symlink"), ("符号链接", "符號連結")),
    (re.compile(r"linking"), ("链接", "連結")),
    (re.compile(r"Linking"), ("链接", "連結")),
    (re.compile(r"matching"), ("匹配", "比對")),
    (re.compile(r"Matching"), ("匹配", "比對")),
    (re.compile(r"scanning|scan"), ("扫描", "掃描")),
    (re.compile(r"Scanning|Scan"), ("扫描", "掃描")),
    (re.compile(r"assign"), ("分配", "指派")),
    (re.compile(r"Assign"), ("分配", "指派")),
    (re.compile(r"assigned"), ("已分配", "已指派")),
    (re.compile(r"overview"), ("概览", "總覽")),
    (re.compile(r"Overview"), ("概览", "總覽")),
    (re.compile(r"enter|input"), ("输入", "輸入")),
    (re.compile(r"Enter|Input"), ("输入", "輸入")),
    (re.compile(r"selected"), ("已选择", "已選取")),
    (re.compile(r"Selected"), ("已选择", "已選取")),
    (re.compile(r"select"), ("选择", "選取")),
    (re.compile(r"Select"), ("选择", "選取")),
    (re.compile(r"continue"), ("继续", "繼續")),
    (re.compile(r"Continue"), ("继续", "繼續")),
    (re.compile(r"running"), ("运行中", "執行中")),
    (re.compile(r"Running"), ("运行中", "執行中")),
    (re.compile(r"runs?"), ("运行", "執行")),
    (re.compile(r"Runs?"), ("运行", "執行")),
    (re.compile(r"missing"), ("缺失", "遺失")),
    (re.compile(r"Missing"), ("缺失", "遺失")),
    (re.compile(r"installed"), ("已安装", "已安裝")),
    (re.compile(r"Installed"), ("已安装", "已安裝")),
    (re.compile(r"additional"), ("额外的", "額外的")),
    (re.compile(r"Additional"), ("额外的", "額外的")),
    (re.compile(r"instance"), ("实例", "執行個體")),
    (re.compile(r"Instance"), ("实例", "執行個體")),
    (re.compile(r"required"), ("必需的", "必要的")),
    (re.compile(r"Required"), ("必需的", "必要的")),
    (re.compile(r"please"), ("请", "請")),
    (re.compile(r"Please"), ("请", "請")),
    (re.compile(r"nothing"), ("任何内容", "任何內容")),
    (re.compile(r"Nothing"), ("任何内容", "任何內容")),
    (re.compile(r"abort"), ("中止", "中止")),
    (re.compile(r"Abort"), ("中止", "中止")),
    (re.compile(r"start"), ("开始", "開始")),
    (re.compile(r"Start"), ("开始", "開始")),
    (re.compile(r"started"), ("已启动", "已啟動")),
    (re.compile(r"Started"), ("已启动", "已啟動")),
    (re.compile(r"correct"), ("正确", "正確")),
    (re.compile(r"Correct"), ("正确", "正確")),
    (re.compile(r"created"), ("已创建", "已建立")),
    (re.compile(r"Created"), ("已创建", "已建立")),
    (re.compile(r"create"), ("创建", "建立")),
    (re.compile(r"Create"), ("创建", "建立")),
    (re.compile(r"found"), ("找到", "找到")),
    (re.compile(r"Found"), ("找到", "找到")),
    (re.compile(r"find"), ("查找", "尋找")),
    (re.compile(r"Find"), ("查找", "尋找")),
    (re.compile(r"exist"), ("存在", "存在")),
    (re.compile(r"Exist"), ("存在", "存在")),
    (re.compile(r"exists"), ("存在", "存在")),
    (re.compile(r"Exists"), ("存在", "存在")),
    (re.compile(r"corrupted|currupted"), ("损坏", "損毀")),
    (re.compile(r"Corrupted|Currupted"), ("损坏", "損毀")),
    (re.compile(r"detect"), ("检测", "偵測")),
    (re.compile(r"Detect"), ("检测", "偵測")),
    (re.compile(r"detected"), ("已检测到", "已偵測到")),
    (re.compile(r"Detected"), ("已检测到", "已偵測到")),
    (re.compile(r"connected"), ("已连接", "已連接")),
    (re.compile(r"Connected"), ("已连接", "已連接")),
    (re.compile(r"connected"), ("已连接", "已連線")),
    (re.compile(r"connection"), ("连接", "連線")),
    (re.compile(r"Connection"), ("连接", "連線")),
    (re.compile(r"parameters?"), ("参数", "參數")),
    (re.compile(r"Parameters?"), ("参数", "參數")),
    (re.compile(r"configurations?"), ("配置", "設定")),
    (re.compile(r"Configurations?"), ("配置", "設定")),
    (re.compile(r"file"), ("文件", "檔案")),
    (re.compile(r"File"), ("文件", "檔案")),
    (re.compile(r"folder|directory"), ("文件夹", "資料夾")),
    (re.compile(r"Folder|Directory"), ("文件夹", "資料夾")),
    (re.compile(r"section"), ("节", "區段")),
    (re.compile(r"Section"), ("节", "區段")),
    (re.compile(r"output"), ("输出", "輸出")),
    (re.compile(r"Output"), ("输出", "輸出")),
    (re.compile(r"console"), ("控制台", "主控台")),
    (re.compile(r"Console"), ("控制台", "主控台")),
    (re.compile(r"macros?"), ("宏", "巨集")),
    (re.compile(r"Macros?"), ("宏", "巨集")),
    (re.compile(r"boot(loader)?"), ("引导(bootloader)", "開機(bootloader)")),
    (re.compile(r"Boot(loader)?"), ("引导(bootloader)", "開機(bootloader)")),
    (re.compile(r"powering? up"), ("上电", "上電")),
    (re.compile(r"Powering? up"), ("上电", "上電")),
    (re.compile(r"method"), ("方法", "方法")),
    (re.compile(r"Method"), ("方法", "方法")),
    (re.compile(r"baudrate|baud rate"), ("波特率", "鮑率")),
    (re.compile(r"access"), ("访问", "存取")),
    (re.compile(r"Access"), ("访问", "存取")),
    (re.compile(r"group"), ("用户组", "群組")),
    (re.compile(r"Group"), ("用户组", "群組")),
    (re.compile(r"user"), ("用户", "使用者")),
    (re.compile(r"User"), ("用户", "使用者")),
    (re.compile(r"alphanumeric"), ("字母数字", "英數字")),
    (re.compile(r"Alphanumeric"), ("字母数字", "英數字")),
    (re.compile(r"characters?"), ("字符", "字元")),
    (re.compile(r"Characters?"), ("字符", "字元")),
    (re.compile(r"allowed"), ("允许", "允許")),
    (re.compile(r"Allowed"), ("允许", "允許")),
    (re.compile(r"special"), ("特殊", "特殊")),
    (re.compile(r"Special"), ("特殊", "特殊")),
    (re.compile(r"index"), ("索引", "索引")),
    (re.compile(r"Index"), ("索引", "索引")),
    (re.compile(r"ascending"), ("递增", "遞增")),
    (re.compile(r"Ascending"), ("递增", "遞增")),
    (re.compile(r"order"), ("顺序", "順序")),
    (re.compile(r"Order"), ("顺序", "順序")),
    (re.compile(r"starting"), ("起始", "起始")),
    (re.compile(r"Starting"), ("起始", "起始")),
    (re.compile(r"press"), ("按", "按")),
    (re.compile(r"Press"), ("按", "按")),
    (re.compile(r"extracting"), ("正在解压", "正在解壓縮")),
    (re.compile(r"Extracting"), ("正在解压", "正在解壓縮")),
    (re.compile(r"holding down"), ("按住", "按住")),
    (re.compile(r"Holding down"), ("按住", "按住")),
    (re.compile(r"button"), ("按钮", "按鈕")),
    (re.compile(r"Button"), ("按钮", "按鈕")),
    (re.compile(r"jumper"), ("跳线帽", "跳線帽")),
    (re.compile(r"Jumper"), ("跳线帽", "跳線帽")),
    (re.compile(r"policykit|polkit"), ("polkit 权限", "polkit 權限")),
    (re.compile(r"Policykit|Polkit"), ("Polkit 权限", "Polkit 權限")),
    (re.compile(r"rules?"), ("规则", "規則")),
    (re.compile(r"Rules?"), ("规则", "規則")),
    (re.compile(r"python"), ("Python", "Python")),
    (re.compile(r"Python"), ("Python", "Python")),
    (re.compile(r"environment"), ("环境", "環境")),
    (re.compile(r"Environment"), ("环境", "環境")),
    (re.compile(r"ongoing"), ("正在进行的", "進行中的")),
    (re.compile(r"Ongoing"), ("正在进行的", "進行中的")),
    (re.compile(r"prints?"), ("打印任务", "列印任務")),
    (re.compile(r"Prints?"), ("打印任务", "列印任務")),
    (re.compile(r"host"), ("主机", "主機")),
    (re.compile(r"Host"), ("主机", "主機")),
    (re.compile(r"ID"), ("ID", "ID")),
    (re.compile(r"names?"), ("名称", "名稱")),
    (re.compile(r"Names?"), ("名称", "名稱")),
    (re.compile(r"value"), ("值", "值")),
    (re.compile(r"Value"), ("值", "值")),
    (re.compile(r"type"), ("类型", "型別")),
    (re.compile(r"Type"), ("类型", "型別")),
    (re.compile(r"actions?"), ("操作", "動作")),
    (re.compile(r"Actions?"), ("操作", "動作")),
    (re.compile(r"process"), ("过程", "程序")),
    (re.compile(r"Process"), ("过程", "程序")),
    (re.compile(r"step"), ("步骤", "步驟")),
    (re.compile(r"Step"), ("步骤", "步驟")),
    (re.compile(r"macro"), ("宏", "巨集")),
    (re.compile(r"Macro"), ("宏", "巨集")),
    (re.compile(r"device"), ("设备", "裝置")),
    (re.compile(r"Device"), ("设备", "裝置")),
    (re.compile(r"recommended"), ("推荐", "建議")),
    (re.compile(r"Recommended"), ("推荐", "建議")),
    (re.compile(r"documentation"), ("文档", "文件")),
    (re.compile(r"Documentation"), ("文档", "文件")),
    (re.compile(r"successfull?|successful"), ("成功", "成功")),
    (re.compile(r"Successfull?|Successful"), ("成功", "成功")),
    (re.compile(r"determin"), ("确定", "決定")),
    (re.compile(r"Determin"), ("确定", "決定")),
    (re.compile(r"similar"), ("类似", "類似")),
    (re.compile(r"Similar"), ("类似", "類似")),
    (re.compile(r"bootloader"), ("引导加载程序", "開機載入程式")),
    (re.compile(r"Bootloader"), ("引导加载程序", "開機載入程式")),
    (re.compile(r"unexpected"), ("意外", "非預期")),
    (re.compile(r"Unexpected"), ("意外", "非預期")),
    (re.compile(r"command"), ("命令", "命令")),
    (re.compile(r"Command"), ("命令", "命令")),
    (re.compile(r"internal"), ("内部", "內部")),
    (re.compile(r"Internal"), ("内部", "內部")),
    (re.compile(r"return"), ("返回", "回傳")),
    (re.compile(r"Return"), ("返回", "回傳")),
    (re.compile(r"already"), ("已经", "已經")),
    (re.compile(r"Already"), ("已经", "已經")),
    (re.compile(r"parsing"), ("解析", "剖析")),
    (re.compile(r"Parsing"), ("解析", "剖析")),
    (re.compile(r"parse"), ("解析", "剖析")),
    (re.compile(r"Parse"), ("解析", "剖析")),
    (re.compile(r"content"), ("内容", "內容")),
    (re.compile(r"Content"), ("内容", "內容")),
    (re.compile(r"\bcurrently\b"), ("当前", "目前")),
    (re.compile(r"\bCurrently\b"), ("当前", "目前")),
    (re.compile(r"\bcurrent\b"), ("当前", "目前")),
    (re.compile(r"\bCurrent\b"), ("当前", "目前")),
    (re.compile(r"finally"), ("最终", "最終")),
    (re.compile(r"Finally"), ("最终", "最終")),
    (re.compile(r"manual"), ("手动", "手動")),
    (re.compile(r"Manual"), ("手动", "手動")),
    (re.compile(r"instructions?"), ("说明", "說明")),
    (re.compile(r"Instructions?"), ("说明", "說明")),
    (re.compile(r"apply"), ("应用", "套用")),
    (re.compile(r"Apply"), ("应用", "套用")),
    (re.compile(r"popular"), ("常用", "常用")),
    (re.compile(r"Popular"), ("常用", "常用")),
    (re.compile(r"correspond(ing|s)?"), ("对应", "對應")),
    (re.compile(r"Correspond(ing|s)?"), ("对应", "對應")),
    (re.compile(r"(re)?moving"), (r"\1除", r"\1除")),
    (re.compile(r"(Re)?moving"), (r"\1除", r"\1除")),
    (re.compile(r"installing"), ("安装", "安裝")),
    (re.compile(r"Installing"), ("安装", "安裝")),
    (re.compile(r"updating"), ("更新", "更新")),
    (re.compile(r"Updating"), ("更新", "更新")),
    (re.compile(r"creating"), ("创建", "建立")),
    (re.compile(r"Creating"), ("创建", "建立")),
    (re.compile(r"identifying"), ("识别", "辨識")),
    (re.compile(r"Identifying"), ("识别", "辨識")),
    (re.compile(r"setting"), ("设置", "設定")),
    (re.compile(r"Setting"), ("设置", "設定")),
    (re.compile(r"recommended"), ("推荐", "建議")),
    (re.compile(r"Recommended"), ("推荐", "建議")),
    (re.compile(r"functional"), ("功能", "功能")),
    (re.compile(r"Functional"), ("功能", "功能")),
    (re.compile(r"working"), ("工作", "運作")),
    (re.compile(r"Working"), ("工作", "運作")),
    (re.compile(r"downloading"), ("下载", "下載")),
    (re.compile(r"Downloading"), ("下载", "下載")),
    (re.compile(r"matching"), ("匹配", "比對")),
    (re.compile(r"Matching"), ("匹配", "比對")),
    (re.compile(r"because"), ("因为", "因為")),
    (re.compile(r"Because"), ("因为", "因為")),
    (re.compile(r"before"), ("之前", "之前")),
    (re.compile(r"Before"), ("之前", "之前")),
    (re.compile(r"after"), ("之后", "之後")),
    (re.compile(r"After"), ("之后", "之後")),
    (re.compile(r"inside"), ("内部", "內部")),
    (re.compile(r"Inside"), ("内部", "內部")),
    (re.compile(r"without"), ("没有", "沒有")),
    (re.compile(r"Without"), ("没有", "沒有")),
    (re.compile(r"repeat"), ("重试", "重試")),
    (re.compile(r"Repeat"), ("重试", "重試")),
    (re.compile(r"which"), ("其中", "其中")),
    (re.compile(r"Which"), ("其中", "其中")),
    (re.compile(r"those"), ("这些", "這些")),
    (re.compile(r"Those"), ("这些", "這些")),
    (re.compile(r"about"), ("关于", "關於")),
    (re.compile(r"About"), ("关于", "關於")),
    (re.compile(r"through"), ("通过", "透過")),
    (re.compile(r"Through"), ("通过", "透過")),
    (re.compile(r"above"), ("以上", "以上")),
    (re.compile(r"Above"), ("以上", "以上")),
    (re.compile(r"following"), ("以下", "以下")),
    (re.compile(r"Following"), ("以下", "以下")),
    (re.compile(r"access"), ("访问", "存取")),
    (re.compile(r"Access"), ("访问", "存取")),
    (re.compile(r"perform"), ("执行", "執行")),
    (re.compile(r"Perform"), ("执行", "執行")),
]


_PLACEHOLDER = re.compile(r"\{[^}]*\}")


def _translate_wordlevel(src: str) -> Tuple[str, str]:
    """Apply the GLOSSARY regex-based word replacement; returns (zh_CN, zh_TW).

    Format-string placeholders ``{name}`` / ``{0}`` / ``{repo_url!r:s}``
    are temporarily removed during replacement and restored afterwards, so
    the glossary never rewrites identifiers inside ``{}``.
    """
    placeholders: List[str] = _PLACEHOLDER.findall(src)

    def _protect(s: str) -> str:
        return _PLACEHOLDER.sub("\x00", s)

    def _restore(s: str, ph: List[str]) -> str:
        out_parts: List[str] = []
        idx = 0
        for piece in s.split("\x00"):
            out_parts.append(piece)
            if idx < len(ph):
                out_parts.append(ph[idx])
                idx += 1
        return "".join(out_parts)

    zh_cn = _protect(src)
    zh_tw = zh_cn
    for pattern, (repl_cn, repl_tw) in GLOSSARY:
        zh_cn = pattern.sub(repl_cn, zh_cn)
        zh_tw = pattern.sub(repl_tw, zh_tw)
    return (_restore(zh_cn, placeholders), _restore(zh_tw, placeholders))


# Direct-entry fast path for the most common short strings in the corpus.
# Key: the exact (unescaped) msgid. Value: (zh_CN, zh_TW)
DIRECT: Dict[str, Tuple[str, str]] = {
    # ---------------------------------------------------------------------
    # Language picker / i18n UI strings
    # ---------------------------------------------------------------------
    "Select language:": ("选择语言：", "選擇語言："),
    "Select a language from the list below.": ("从下面的列表中选择一种语言。", "從下面的列表中選擇一種語言。"),
    "Currently active: {}": ("当前语言：{}", "目前語言：{}"),
    "Press L for the language list.": ("按 L 打开语言列表。", "按 L 開啟語言清單。"),
    "Moongate currently supports a single-printer setup. The instance '{}' will be used.":
        ("Moongate 当前仅支持单打印机设置。将使用实例 '{}'。",
         "Moongate 目前僅支援單印表機設定。將使用執行個體 '{}'。"),
    "All currently running {} services will be stopped!":
        ("所有当前正在运行的 {} 服务都将被停止！",
         "所有目前正在執行的 {} 服務都將被停止！"),
    "English": ("英语", "英語"),
    "Simplified Chinese": ("简体中文", "簡體中文"),
    "Traditional Chinese": ("繁体中文", "繁體中文"),
    "Language": ("语言", "語言"),
    "Language/文": ("语言/文", "語言/文"),
    "Select an option": ("请选择一个选项", "請選擇一個選項"),

    # Symbols / markers
    "● {}": ("● {}", "● {}"),
    "● {}: {}": ("● {}: {}", "● {}: {}"),
    "● Any special characters": ("● 任何特殊字符", "● 任何特殊字元"),
    "● No leading or trailing '-'": ("● 开头或结尾不能是 '-'", "● 開頭或結尾不能是 '-'"),
    "● {} removed": ("● 已移除 {}", "● 已移除 {}"),
    "● Klipper Python environment removed": ("● 已移除 Klipper Python 环境", "● 已移除 Klipper Python 環境"),
    "● Moonraker Python environment removed": ("● 已移除 Moonraker Python 环境", "● 已移除 Moonraker Python 環境"),
    "● Moonraker policykit rules removed": ("● 已移除 Moonraker polkit 规则", "● 已移除 Moonraker polkit 規則"),
    "● NGINX config removed": ("● 已移除 Nginx 配置", "● 已移除 Nginx 設定"),

    # KlipperScreen / Crowsnest / misc short statuses
    "Updating KlipperScreen ...": ("正在更新 KlipperScreen ...", "正在更新 KlipperScreen ..."),
    "Removing KlipperScreen ...": ("正在移除 KlipperScreen ...", "正在移除 KlipperScreen ..."),
    "Removing KlipperScreen environment ...": ("正在移除 KlipperScreen 环境 ...", "正在移除 KlipperScreen 環境 ..."),
    "KlipperScreen environment not found!": ("未找到 KlipperScreen 环境！", "未找到 KlipperScreen 環境！"),
    "KlipperScreen does not seem to be installed! Skipping ...": ("似乎未安装 KlipperScreen！跳过 ...", "似乎未安裝 KlipperScreen！跳過 ..."),
    "Crowsnest does not seem to be installed! Skipping ...": ("似乎未安装 Crowsnest！跳过 ...", "似乎未安裝 Crowsnest！跳過 ..."),

    "Error parsing crowsnest dependencies!": ("解析 Crowsnest 依赖失败！", "解析 Crowsnest 相依性失敗！"),
    "Error parsing Moonraker dependencies!": ("解析 Moonraker 依赖失败！", "解析 Moonraker 相依性失敗！"),

    # Firmware/Device detection
    "Unable to find a USB device!": ("找不到 USB 设备！", "找不到 USB 裝置！"),
    "Unable to find a UART device!": ("找不到 UART 设备！", "找不到 UART 裝置！"),
    "Unable to find a USB DFU device!": ("找不到 USB DFU 设备！", "找不到 USB DFU 裝置！"),
    "Unable to find a USB RP2 Boot device!": ("找不到 USB RP2040 Boot 设备！", "找不到 USB RP2040 Boot 裝置！"),
    "No MCUs found!": ("未找到任何 MCU！", "未找到任何 MCU！"),
    "Make sure they are connected and repeat this step.": ("请确认设备已连接并重试此步骤。", "請確認裝置已連接並重試此步驟。"),
    "The following MCUs were found:": ("找到以下 MCU：", "找到以下 MCU："),
    "Identifying MCU connected via USB ...": ("正在识别通过 USB 连接的 MCU ...", "正在辨識透過 USB 連接的 MCU ..."),
    "Identifying MCU possibly connected via UART ...": ("正在识别可能通过 UART 连接的 MCU ...", "正在辨識可能透過 UART 連線的 MCU ..."),
    "Identifying MCU connected via USB in DFU mode ...": ("正在识别通过 USB DFU 模式连接的 MCU ...", "正在辨識透過 USB DFU 模式連接的 MCU ..."),
    "Identifying MCU connected via USB in RP2 Boot mode ...": ("正在识别通过 USB RP2 Boot 模式连接的 MCU ...", "正在辨識透過 USB RP2 Boot 模式連接的 MCU ..."),

    "USB:": ("USB：", "USB："),
    "UART:": ("UART：", "UART："),
    "USB DFU:": ("USB DFU：", "USB DFU："),
    "USB RP2040 Boot:": ("USB RP2040 Boot：", "USB RP2040 Boot："),

    "USB": ("USB", "USB"),
    "UART": ("UART", "UART"),
    "USB (DFU mode)": ("USB (DFU 模式)", "USB (DFU 模式)"),
    "USB (RP2040 mode)": ("USB (RP2040 模式)", "USB (RP2040 模式)"),

    "Make sure that the controller board is connected now!": ("请现在确认控制主板已连接！", "請現在確認控制主板已連接！"),
    "Make sure to select the correct method for the MCU!": ("请确认选择了正确的 MCU 连接方式！", "請確認選取了正確的 MCU 連線方式！"),
    "Make sure, that:": ("请确认：", "請確認："),
    "Make sure, to select the correct MCU!": ("请务必选择正确的 MCU！", "請務必選取正確的 MCU！"),
    "Make sure everything is correct, start the process. If any": ("请确认所有参数设置正确后开始操作。若有任何", "請確認所有參數設定正確後開始作業。若有任何"),

    "How is the controller board connected to the host?": ("控制主板如何连接到主机？", "控制主板如何連線到主機？"),
    "Select connection type": ("选择连接方式", "選取連線方式"),
    "Select board type": ("选择主板类型", "選取主板型別"),
    "Please select the type of board that corresponds to": ("请选择与您刚才选择的 MCU ID", "請選取與您剛才選取的 MCU ID"),
    "the currently selected MCU ID you chose before.": ("相匹配的主板类型。", "相匹配的主板型別。"),
    "Please set the baud rate": ("请设置波特率", "請設定鮑率"),
    "Enter name for instance {}": ("请输入实例 {} 的名称", "請輸入執行個體 {} 的名稱"),

    "MCU:": ("MCU：", "MCU："),
    "Connection:": ("连接：", "連線："),
    "Board type:": ("主板：", "主板："),
    "Baudrate:": ("波特率：", "鮑率："),
    "Overview": ("概览", "總覽"),
    "if all parameters were set correctly! Once you made": ("参数是否都设置正确！确认无误后", "參數是否都設定正確！確認無誤後"),
    "sure everything is correct, start the process. If any": ("请开始操作。如需调整", "請開始作業。如需調整"),
    "parameter needs to be changed, you can go back (B)": ("参数，可使用 (B) 返回", "參數，可使用 (B) 返回"),
    "step by step or abort and start from the beginning.": ("上一步或中止后重新开始。", "上一步或中止後重新開始。"),

    "opt_data is None": ("opt_data 为空", "opt_data 為空"),
    "opt_data does not exists": ("opt_data 不存在", "opt_data 不存在"),
    "opt_index is None": ("opt_index 为空", "opt_index 為空"),
    "Missing value for selected_mcu!": ("缺少 selected_mcu 的值！", "缺少 selected_mcu 的值！"),
    "Missing value for connection_type!": ("缺少 connection_type 的值！", "缺少 connection_type 的值！"),
    "Missing value for selected_board!": ("缺少 selected_board 的值！", "缺少 selected_board 的值！"),
    "An unexpected error occured:": ("发生意外错误：", "發生非預期錯誤："),
    "Unexpected error:": ("意外错误：", "非預期錯誤："),
    "See the console output above!": ("请参见上方的控制台输出！", "請參見上方的主控台輸出！"),

    "Select an existing config or create a new one.": ("选择现有配置或创建新配置。", "選取現有設定或建立新設定。"),
    "Press ENTER to install dependencies": ("按 ENTER 安装依赖项", "按 ENTER 安裝相依套件"),
    "Dependencies are missing!": ("缺少依赖项！", "缺少相依套件！"),
    "The following dependencies are required:": ("需要安装以下依赖项：", "需要安裝以下相依套件："),
    "*INSTALLED*": ("*已安装*", "*已安裝*"),
    "*MISSING*": ("*缺失*", "*遺失*"),
    "OK!": ("完成！", "完成！"),

    "Allowed characters: a-z, 0-9 and '-'": ("允许使用的字符：a-z、0-9 及 '-'", "允許使用的字元：a-z、0-9 及 '-'"),
    "The name must not contain the following:": ("名称不能包含以下内容：", "名稱不得包含下列內容："),
    "Only alphanumeric characters are allowed!": ("仅允许字母数字字符！", "僅限英數字元！"),
    "If skipped, each instance will get an index assigned": ("若跳过，每个实例将按", "若跳過，每個執行個體將依"),
    "in ascending order, starting at '1' in case of a new": ("递增顺序分配索引，新安装时从", "遞增順序指派索引，新安裝時從"),
    "additional": ("额外的", "額外的"),
    "Error creating instance:": ("创建实例时出错：", "建立執行個體時發生錯誤："),
    "Error creating env file:": ("创建环境文件时出错：", "建立環境檔案時發生錯誤："),
    "Unable to open": ("无法打开", "無法開啟"),
    "File not found": ("未找到文件", "找不到檔案"),
    "{} not found!": ("未找到 {}！", "找不到 {}！"),
    "'{}' already exists.": ("“{}” 已存在。", "「{}」已存在。"),

    "Your current user is not in group:": ("当前用户不在以下用户组：", "目前使用者不在下列群組："),
    "Add user '{}' to group(s) now?": ("是否现在将用户 “{}” 添加到这些用户组？", "是否現在將使用者「{}」加入這些群組？"),
    "Skipped adding user to required groups. You might encounter issues.": ("已跳过将用户添加到必需用户组的步骤，后续可能会遇到问题。", "已跳過將使用者加入必要群組的步驟，後續可能會遇到問題。"),
    "Adding user '{}' to group {} ...": ("正在将用户 “{}” 添加到用户组 {} ...", "正在將使用者「{}」加入群組 {} ..."),
    "Group {} assigned to user '{}'.": ("用户组 {} 已分配给用户 “{}”。", "群組 {} 已指派給使用者「{}」。"),
    "Unable to add user to usergroups:": ("无法将用户添加到用户组：", "無法將使用者加入使用者群組："),
    "Required Klipper python environment not found!": ("未找到必需的 Klipper Python 环境！", "找不到必要的 Klipper Python 環境！"),
    "Also, the following Python package will be installed:": ("此外还将安装以下 Python 包：", "此外也會安裝下列 Python 套件："),
    "Do you want to install the required packages?": ("是否安装必需的依赖包？", "是否安裝必要的相依套件？"),
    "{} everything": ("全部{}", "全部{}"),
    "Deselect": ("取消选择", "取消選取"),
    "Enter a number and hit enter to select / deselect": ("输入编号后按回车 选择 / 取消选择", "輸入編號後按 Enter 選取 / 取消選取"),
    "Continue": ("继续", "繼續"),
    "a) Select all": ("a) 全选", "a) 全選"),

    "Do NOT continue if there are ongoing prints running!": ("若有正在进行中的打印任务，请勿继续！", "若有進行中的列印任務，請勿繼續！"),
    "Be careful if there are ongoing prints running!": ("如有正在进行的打印任务，请谨慎操作！", "如有進行中的列印任務，請謹慎操作！"),
    "The following actions were performed:": ("已执行以下操作：", "已執行下列動作："),
    "Nothing to remove.": ("没有可移除的内容。", "沒有可移除的內容。"),
    "Select Klipper instance to remove": ("选择要移除的 Klipper 实例", "選取要移除的 Klipper 執行個體"),
    "Select Moonraker instance to remove": ("选择要移除的 Moonraker 实例", "選取要移除的 Moonraker 執行個體"),
    "Removing instance {} ...": ("正在移除实例 {} ...", "正在移除執行個體 {} ..."),
    "Env file in {} not found. Skipped ...": ("未找到 {} 中的环境文件，已跳过 ...", "找不到 {} 中的環境檔案，已跳過 ..."),
    "PLEASE NOTE:": ("请注意：", "請注意："),
    "If you select an instance with an existing Moonraker": ("如果您选择的实例同时绑定了 Moonraker", "如果您選取的執行個體同時繫結了 Moonraker"),
    "instance, that Moonraker instance will be re-created!": ("实例，则该 Moonraker 实例也将被重新创建！", "，則該 Moonraker 執行個體也會重新建立！"),
    "Error selecting instance!": ("选择实例时出错！", "選取執行個體時發生錯誤！"),
    "Create example moonraker.conf?": ("是否创建示例 moonraker.conf？", "是否建立範例 moonraker.conf？"),
    "Error while installing Moonraker:": ("安装 Moonraker 时出错：", "安裝 Moonraker 時發生錯誤："),
    "Removing all Moonraker policykit rules ...": ("正在移除所有 Moonraker polkit 规则 ...", "正在移除所有 Moonraker polkit 規則 ..."),
    "Removing Moonraker Python environment ...": ("正在移除 Moonraker Python 环境 ...", "正在移除 Moonraker Python 環境 ..."),
    "Removing Klipper Python environment ...": ("正在移除 Klipper Python 环境 ...", "正在移除 Klipper Python 環境 ..."),
    "You can access Moonraker via the following URL:": ("您可以通过以下地址访问 Moonraker：", "您可以透過下列網址存取 Moonraker："),
    "Klipper not installed!": ("未安装 Klipper！", "未安裝 Klipper！"),
    "Moonraker policykit rules are already installed.": ("Moonraker polkit 规则已安装。", "Moonraker polkit 規則已安裝。"),
    "Error while installing Moonraker policykit rules:": ("安装 Moonraker polkit 规则时出错：", "安裝 Moonraker polkit 規則時發生錯誤："),
    "Error while removing policykit rules:": ("移除 polkit 规则时出错：", "移除 polkit 規則時發生錯誤："),
    "Creating example moonraker.conf in '{}'": ("正在在 “{}” 中创建示例 moonraker.conf", "正在在「{}」中建立範例 moonraker.conf"),
    "Unable to create example moonraker.conf:": ("无法创建示例 moonraker.conf：", "無法建立範例 moonraker.conf："),
    "Example moonraker.conf created in '{}'": ("已在 “{}” 中创建示例 moonraker.conf", "已在「{}」中建立範例 moonraker.conf"),
    "Unable to parse": ("无法解析", "無法剖析"),
    "{} removed from instance": ("已从实例中移除 {}", "已從執行個體移除 {}"),
    "Klipper config section '{}' removed for instance": ("已为实例移除 Klipper 配置节 “{}”", "已為執行個體移除 Klipper 設定區段「{}」"),
    "Moonraker config section '{}' removed for instance": ("已为实例移除 Moonraker 配置节 “{}”", "已為執行個體移除 Moonraker 設定區段「{}」"),
    "● Moonraker config section '{}' removed for instance: {}": ("● 已为实例移除 Moonraker 配置节 “{}”：{}", "● 已為執行個體移除 Moonraker 設定區段「{}」：{}"),

    "Another Client-Config is already installed! Skipped ...": ("已经安装了另一种客户端配置，已跳过 ...", "已安裝另一種用戶端設定，已跳過 ..."),
    "Re-install {}?": ("是否重新安装 {}？", "是否重新安裝 {}？"),
    "Updating {} ...": ("正在更新 {} ...", "正在更新 {} ..."),
    "Removing {} ...": ("正在移除 {} ...", "正在移除 {} ..."),
    "Create symlink for {} ...": ("正在为 {} 创建符号链接 ...", "正在為 {} 建立符號連結 ..."),
    "Linking {} to {}": ("正在将 {} 链接到 {}", "正在將 {} 連結至 {}"),
    "{} seems to be already installed!": ("{} 似乎已经安装过了！", "{} 似乎已經安裝過了！"),
    "It is recommended to use special macros in order to have {} fully functional and working.": ("建议使用配套的宏，以便 {} 全部功能可以正常运作。", "建議使用配套的巨集，以便 {} 全部功能可以正常運作。"),
    "The recommended macros for {} can be seen here:": ("{} 的推荐宏可在此查看：", "{} 的建議巨集可在此檢視："),
    "Removing NGINX config for {} ...": ("正在移除 {} 的 Nginx 配置 ...", "正在移除 {} 的 Nginx 設定 ..."),
    "Open {} now on: http://{}{}": ("现在可以通过 http://{}{} 打开 {}", "現在可以透過 http://{}{} 開啟 {}"),
    "Extracting {} ...": ("正在解压 {} ...", "正在解壓縮 {} ..."),
    "The following {} were found:": ("找到以下 {}：", "找到以下 {}："),

    "!!! NO FIRMWARE FILE FOUND !!!": ("!!! 未找到固件文件 !!!", "!!! 找不到韌體檔案 !!!"),
    "● the folder '~/klipper/out' and its content exist": ("● “~/klipper/out” 目录及其内容存在", "●「~/klipper/out」資料夾及其內容存在"),
    "● the folder contains the following file:": ("● 该目录包含以下文件：", "● 該資料夾包含下列檔案："),
    "!!! ERROR GETTING BOARD LIST !!!": ("!!! 获取主板列表时出错 !!!", "!!! 取得主板清單時發生錯誤 !!!"),
    "● the folder '~/klipper' and all its content exist": ("● “~/klipper” 目录及其全部内容存在", "●「~/klipper」資料夾及其全部內容存在"),
    "● the content of folder '~/klipper' is not currupted": ("● “~/klipper” 目录下的内容没有损坏", "●「~/klipper」資料夾內容未損毀"),
    "● your current user has access to those files/folders": ("● 当前用户拥有这些文件/目录的访问权限", "● 目前使用者具備這些檔案/資料夾的存取權限"),
    "If in doubt or this process continues to fail, please": ("如果有疑问或该过程持续失败，请", "如果有疑問或此程序繼續失敗，請"),
    "Many popular controller boards ship with a bootloader": ("许多常用控制主板在出厂时已经写入了引导程序", "許多熱門控制主板出廠時已預載開機載入程式"),
    "this way of updating. This method ONLY works for up-": ("的更新方式。本方法仅适用于", "的更新方式。本方法僅適用於"),
    "be done manually per the instructions that apply to": ("请根据主板说明手动完成。", "請依照主板說明手動完成。"),
    "your controller board.": ("（针对您的控制主板）。", "（針對您的控制主板）。"),
    "will detect selected microcontroller and use suitable": ("将自动识别所选 MCU 并使用合适的", "會自動辨識選取的 MCU 並使用合適的"),
    "will be used internally.": ("在内部使用。", "於內部程序中使用。"),

    "Selecting USB as the connection method will scan the": ("选择 USB 连接方式后，将扫描", "選取 USB 連線方式後，將掃描"),
    "be similar to the 'ls /dev/serial/by-id/*' command": ("结果类似于执行 'ls /dev/serial/by-id/*' 命令", "結果類似於執行 'ls /dev/serial/by-id/*' 命令"),
    "suggested by the official Klipper documentation for": ("的官方 Klipper 文档中建议用于", "官方 Klipper 文件中建議用於"),
    "determining successfull USB connections!": ("确认 USB 连接成功的方式！", "確認 USB 連線成功的方式！"),
    "Selecting UART as the connection method will list all": ("选择 UART 连接方式后，将列出所有", "選取 UART 連線方式後，將列出所有"),
    "returns something as it seems impossible to determine": ("可能会返回一些内容，但系统无法自动判断", "可能會傳回一些內容，但系統無法自動判斷"),
    "if a valid Klipper controller board is connected or": ("是否确实连接了有效的 Klipper 控制主板", "是否真的連接了有效的 Klipper 控制主板"),
    "not. Because of that, you MUST know which UART serial": ("。因此，您必须自行确认选择了哪种 UART 串口", "。因此，您必須自行確認選取了哪個 UART 序列埠"),
    "this connection method.": ("作为本次连接。", "做為本次連線。"),
    "Selecting USB DFU as the connection method will scan": ("选择 USB DFU 连接方式后，将扫描", "選取 USB DFU 連線方式後，將掃描"),
    "STM32 DFU mode, which is usually done by holding down": ("STM32 DFU 模式，进入该模式的常见方法是按住", "STM32 DFU 模式，進入該模式的常見方式為按住"),
    "the BOOT button or setting a special jumper on the": ("BOOT 按钮，或在主板上设置专用的跳线帽", "BOOT 按鈕，或在主板上設定專用的跳線帽"),
    "board before powering up.": ("后再上电。", "後再上電。"),
    "Selecting USB RP2 Boot as the connection method will": ("选择 USB RP2 Boot 连接方式后，将扫描", "選取 USB RP2 Boot 連線方式後，將掃描"),
    "boards in Boot mode, which is usually done by holding": ("处于 Boot 模式的主板，通常是在按住", "處於 Boot 模式的主板，通常是在按住"),
    "down the BOOT button before powering up.": ("BOOT 按钮的同时再上电。", "BOOT 按鈕的同時再上電。"),

    "!!! ATTENTION !!!": ("!!! 请注意 !!!", "!!! 請注意 !!!"),
    "List of detected MCUs": ("已检测到的 MCU 列表", "已偵測到的 MCU 清單"),

    "WARNING:": ("警告：", "警告："),
    "INFO:": ("信息：", "資訊："),
    "ATTENTION:": ("注意：", "注意："),

    "Error installing KlipperScreen:\n{}": ("安装 KlipperScreen 时出错:\n{}", "安裝 KlipperScreen 時發生錯誤:\n{}"),
    "Error updating KlipperScreen:\n{}": ("更新 KlipperScreen 时出错:\n{}", "更新 KlipperScreen 時發生錯誤:\n{}"),
    "Error removing KlipperScreen:\n{}": ("移除 KlipperScreen 时出错:\n{}", "移除 KlipperScreen 時發生錯誤:\n{}"),

    "Klipper not installed!": ("未安装 Klipper！", "未安裝 Klipper！"),

    # --- Final 116 catch-all entries for 100% coverage ---
    "USB": ("USB", "USB"),
    "UART": ("UART", "UART"),
    "Enable Mainsails remote mode ...": ("正在启用 Mainsail 远程模式 ...", "正在啟用 Mainsail 遠端模式 ..."),
    "Invalid 'release_info.json'": ("无效的 'release_info.json'", "無效的 'release_info.json'"),
    "Unable to read '.version'": ("无法读取 '.version'", "無法讀取 '.version'"),
    "Reconfigure": ("重新配置", "重新設定"),
    "Configure": ("配置", "設定"),
    "Reinstall {}": ("重新安装 {}", "重新安裝 {}"),
    "Open {} now on: http://{}:{}": ("现在通过 http://{}:{} 打开 {}", "現在透過 http://{}:{} 開啟 {}"),
    " everything": (" 全部", " 全部"),
    "Error disabling": ("禁用时出错", "停用時發生錯誤"),
    "Error stopping": ("停止时出错", "停止時發生錯誤"),
    "Success!": ("成功！", "成功！"),
    "OK": ("确定", "確定"),
    "WARN": ("警告", "警告"),
    "Get MCU ID": ("获取 MCU ID", "取得 MCU ID"),
    "Klipper & Moonraker API:": ("Klipper 与 Moonraker API：", "Klipper 與 Moonraker API："),
    "Moonraker Database": ("Moonraker 数据库", "Moonraker 資料庫"),
    " [ KIAUH ] ": (" [ KIAUH ] ", " [ KIAUH ] "),
    "BaseMenu cannot be instantiated directly.": ("无法直接实例化 BaseMenu。", "無法直接建立 BaseMenu 執行個體。"),
    "Branch": ("分支", "分支"),
    "Summary": ("摘要", "摘要"),
    "URL:": ("网址：", "網址："),
    "Latest:": ("最新：", "最新："),
    "Klipper & API:": ("Klipper 與 API：", "Klipper 與 API："),
    "Other:": ("其他：", "其他："),
    "UPGRADABLE SYSTEM UPDATES": ("可升级的系统更新", "可升級的系統更新"),
    "config": ("配置", "設定"),
    "Old format:": ("旧格式：", "舊格式："),
    "New format:": ("新格式：", "新格式："),
    "Migrate to the new format?": ("是否迁移到新格式？", "是否遷移至新格式？"),
    "Loading": ("正在加载", "正在載入"),
    "DroidKlipp expects KlipperScreen at:": ("DroidKlipp 期望安装 KlipperScreen 于：", "DroidKlipp 預期 KlipperScreen 位於："),
    "Do you really want to uninstall DroidKlipp?": ("是否确实要卸载 DroidKlipp？", "您確定要解除安裝 DroidKlipp 嗎？"),
    "Failed loading extension": ("加载扩展失败", "載入擴充失敗"),
    "Skipping": ("跳过", "跳過"),
    "Links:": ("链接：", "連結："),
    "Copy extension to": ("复制扩展到", "複製擴充至"),
    "Unable to install extension:": ("无法安装扩展：", "無法安裝擴充："),
    "Do you really want to remove the extension?": ("是否确实要移除此扩展？", "您確定要移除此擴充嗎？"),
    "Unable to remove extension:": ("无法移除扩展：", "無法移除擴充："),
    "Done!": ("完成！", "完成！"),
    "IMPORTANT:": ("重要：", "重要："),
    "NOTE:": ("注：", "註："),
    "Add": ("添加", "新增"),
    "to": ("到", "至"),
    "of": ("的", "的"),
    "Failed to remove": ("移除失败", "移除失敗"),
    "Unable to uninstall theme": ("无法卸载主题", "無法解除安裝主題"),
    "Info from the creator:": ("作者说明：", "作者資訊："),
    "Moonraker will not be added to any moonraker.conf.": ("Moonraker 设置不会被添加到任何 moonraker.conf。", "不會將 Moonraker 設定加入任何 moonraker.conf。"),
    "Moongate is a Moonraker component and needs Moonraker to be ": ("Moongate 是一个 Moonraker 组件，需要 Moonraker 处于", "Moongate 是 Moonraker 元件，需要 Moonraker 處於"),
    "will be used.": ("将被使用。", "將會使用。"),
    "This is a heavier install than most extensions. It will:": ("此扩展相比多数扩展安装内容更丰富，将执行：", "這是一個比多數擴充更大型的安裝，它會："),
    "● clone the Moongate repo to ~/moongate": ("● 将 Moongate 仓库克隆到 ~/moongate", "● 複製 Moongate 儲存庫到 ~/moongate"),
    "● add the Moongate component to Moonraker and register it with ": ("● 将 Moongate 组件加入 Moonraker 并注册到", "● 將 Moongate 元件加入 Moonraker 並註冊到"),
    "● install cloudflared and open a Cloudflare quick-tunnel": ("● 安装 cloudflared 并开启 Cloudflare 快速通道", "● 安裝 cloudflared 並開啟 Cloudflare 快速通道"),
    "● bind Moonraker to 127.0.0.1 (the auth proxy fronts the tunnel)": ("● 将 Moonraker 绑定到 127.0.0.1（由授权代理位于通道前端）", "● 將 Moonraker 繫結至 127.0.0.1（由驗證代理位於通道前端）"),
    "● add a tightly-scoped Avahi sudoers entry for LAN discovery": ("● 为局域网发现添加最小权限的 Avahi sudoers 条目", "● 為區域網路探索加入最小權限的 Avahi sudoers 規則"),
    "Moongate author. Moongate is licensed under PolyForm ": ("Moongate 作者所有。Moongate 使用 PolyForm 许可", "Moongate 作者版權。Moongate 使用 PolyForm 授權"),
    "Noncommercial 1.0.0 (non-commercial use only).": ("非商业 1.0.0（仅限非商业使用）。", "Noncommercial 1.0.0（僅限非營利使用）。"),
    "Obico Server URL": ("Obico 服务端网址", "Obico 伺服端網址"),
    "Obico's": ("Obico 的", "Obico 的"),
    "in": ("在", "在"),
    "Obico config in": ("Obico 配置位于", "Obico 設定位於"),
    "For more information visit:": ("了解更多信息请访问：", "更多資訊請造訪："),
    "to the Obico server ...": ("到 Obico 服务端 ...", "至 Obico 伺服端 ..."),
    "Reinstall?": ("是否重新安装？", "是否重新安裝？"),
    "Skipping creation ...": ("跳过创建 ...", "跳過建立 ..."),
    "Open PrettyGCode now on:": ("现在可通过以下地址打开 PrettyGCode：", "現在可透過下列位址開啟 PrettyGCode："),
    "PrettyGCode for Klipper removed!": ("已移除用于 Klipper 的 PrettyGCode！", "已移除 Klipper 適用的 PrettyGCode！"),
    "The setup will": ("安装程序将", "安裝程式將"),
    "Adding": ("正在添加", "正在新增"),
    "from": ("从", "從"),
    "does not": ("未", "未"),
    "un": ("取消", "取消"),
    "Spoolman container removed!": ("已移除 Spoolman 容器！", "已移除 Spoolman 容器！"),
    "Spoolman container and image removed!": ("已移除 Spoolman 容器与镜像！", "已移除 Spoolman 容器與映像檔！"),
    "Spoolman data backed up to": ("Spoolman 数据已备份到", "Spoolman 資料已備份到"),
    "Permissions set!": ("权限已设置！", "權限已設定！"),
    "Spinning up Spoolman container...": ("正在启动 Spoolman 容器...", "正在啟動 Spoolman 容器..."),
    "Spoolman integration added to Moonraker!": ("已将 Spoolman 集成添加到 Moonraker！", "已將 Spoolman 整合新增至 Moonraker！"),
    "Moonraker integration skipped.": ("已跳过 Moonraker 集成。", "已跳過 Moonraker 整合。"),
    "Add Moonraker integration?": ("是否添加 Moonraker 集成？", "是否新增 Moonraker 整合？"),
    "Adding Spoolman integration to Moonraker...": ("正在向 Moonraker 添加 Spoolman 集成...", "正在為 Moonraker 新增 Spoolman 整合..."),
    "Adding Spoolman to moonraker.asvc...": ("正在将 Spoolman 添加到 moonraker.asvc...", "正在將 Spoolman 新增到 moonraker.asvc..."),
    "Skipping...": ("跳过...", "跳過..."),
    "Spoolman added to": ("Spoolman 已添加到", "Spoolman 已新增到"),
    "Spoolman not in": ("Spoolman 不在", "Spoolman 不在"),
    "Spoolman removed from": ("已从以下位置移除 Spoolman：", "已從下列位置移除 Spoolman："),
    "Failed to get Spoolman Docker image ID": ("获取 Spoolman Docker 镜像 ID 失败", "取得 Spoolman Docker 映像 ID 失敗"),
    "Pulling latest Spoolman image...": ("正在拉取最新的 Spoolman 镜像...", "正在提取最新的 Spoolman 映像..."),
    "Tearing down old Spoolman container...": ("正在销毁旧的 Spoolman 容器...", "正在銷毀舊的 Spoolman 容器..."),
    "Spinning up new Spoolman container...": ("正在启动新的 Spoolman 容器...", "正在啟動新的 Spoolman 容器..."),
    "Failed to tear down Spoolman container:": ("销毁 Spoolman 容器时失败：", "銷毀 Spoolman 容器時發生錯誤："),
    "Failed to pull Spoolman Docker image:": ("拉取 Spoolman Docker 镜像失败：", "提取 Spoolman Docker 映像失敗："),
    "Failed to remove Spoolman Docker image:": ("移除 Spoolman Docker 镜像失败：", "移除 Spoolman Docker 映像失敗："),
    "Telegram Bot config in": ("Telegram Bot 配置位于", "Telegram Bot 設定位於"),
    "Moonraker Telegram Bot removed!": ("已移除 Moonraker Telegram 机器人！", "已移除 Moonraker Telegram 機器人！"),
    "Unable to delete": ("无法删除", "無法刪除"),
    "'autotune_tmc.cfg' is NOT removed automatically. ": ("不会自动删除 'autotune_tmc.cfg'。", "不會自動刪除 'autotune_tmc.cfg'。"),
    "Include autotune_tmc.cfg in": ("请将 autotune_tmc.cfg 包含在", "請將 autotune_tmc.cfg 包含在"),
    "for Moonraker will not be added to moonraker.conf.": ("用于 Moonraker 的将不会被添加到 moonraker.conf。", "用於 Moonraker 的設定不會加入 moonraker.conf。"),
    "for Moonraker will not be removed from moonraker.conf.": ("用于 Moonraker 的将不会从 moonraker.conf 中移除。", "用於 Moonraker 的設定不會從 moonraker.conf 中移除。"),
    "Switched to {repo_url} at branch {branch}!": ("已切换到 {repo_url}，分支 {branch}！", "已切換至 {repo_url}，分支 {branch}！"),
    "Something went wrong: {e}": ("出现错误：{e}", "發生錯誤：{e}"),
    "CHANGE SYSTEM HOSTNAME": ("修改系统主机名", "變更系統主機名稱"),
    "v?.?.?": ("v?.?.?", "v?.?.?"),
    "Trying to remove with sudo ...": ("正在尝试使用 sudo 权限移除 ...", "正在嘗試以 sudo 權限移除 ..."),
    "Error on git pull:": ("git pull 时出错：", "git pull 時發生錯誤："),
    "How many commits do you want to roll back": ("希望回退多少个提交", "希望回退多少個提交"),
    "An error occured during repo rollback:": ("仓库回退过程中出现错误：", "儲存庫復原時發生錯誤："),
    "Installed": ("已安装", "已安裝"),
    "Incomplete": ("不完整", "不完整"),
    "Not installed": ("未安装", "未安裝"),
    "Invalid choice. Please select a valid value.": ("无效选项。请选择有效值。", "無效選項。請選取有效值。"),
    "Exiting Klipper setup ...": ("正在退出 Klipper 设置 ...", "正在退出 Klipper 設定 ..."),
    "Exiting Moonraker setup ...": ("正在退出 Moonraker 设置 ...", "正在退出 Moonraker 設定 ..."),
    "A critical error has occured. KIAUH was terminated.": ("发生严重错误。KIAUH 已终止。", "發生嚴重錯誤。KIAUH 已終止。"),
    "Skipping re-creation of virtualenv ...": ("跳过重新创建虚拟环境 ...", "跳過重新建立虛擬環境 ..."),

    # ---- New unified template strings introduced in sys_utils / backup_service / fs_utils / config_utils / git_utils / kiauh_settings / instance_manager / repo_select_menu ----
    "Cloning repository from '{}'": ("正在克隆仓库：'{}'", "正在複製儲存庫：'{}'"),
    "'{}' already exists. Overwrite?": ("“{}” 已存在，是否覆盖？", "「{}」已存在，是否覆蓋？"),
    "Skip cloning of repository ...": ("跳过克隆仓库 ...", "跳過複製儲存庫 ..."),
    "An unexpected error occured during cloning of the repository.": ("克隆仓库时发生意外错误。", "複製儲存庫時發生非預期錯誤。"),
    "Error removing existing repository:": ("移除现有仓库时出错：", "移除現有儲存庫時發生錯誤："),

    "Remove '{}'": ("正在移除 '{}'", "正在移除 '{}'"),
    "Error removing service:": ("移除服务时出错：", "移除服務時發生錯誤："),

    "Switching to {}'s new source repository ...": ("正在切换到 {} 的新源仓库 ...", "正在切換至 {} 的新來源儲存庫 ..."),

    # backup_service templates
    "Creating backup of {} ...": ("正在创建 {} 的备份 ...", "正在建立 {} 的備份 ..."),
    "File '{}' does not exist! Skipping backup...": ("文件 '{}' 不存在！跳过备份...", "檔案 '{}' 不存在！跳過備份..."),
    "'{}' is not a file! Skipping backup...": ("'{}' 不是文件！跳过备份...", "'{}' 不是檔案！跳過備份..."),
    "File '{}' already exists. Skipping ...": ("文件 '{}' 已存在，跳过 ...", "檔案 '{}' 已存在，跳過 ..."),
    "Successfully backed up '{}' to '{}'": ("已成功将 '{}' 备份到 '{}'", "已成功將 '{}' 備份至 '{}'"),
    "Failed to backup '{}': {}": ("备份 '{}' 失败：{}", "備份 '{}' 失敗：{}"),
    "Directory '{}' does not exist! Skipping backup...": ("目录 '{}' 不存在！跳过备份...", "目錄 '{}' 不存在！跳過備份..."),
    "'{}' is not a directory! Skipping backup...": ("'{}' 不是目录！跳过备份...", "'{}' 不是目錄！跳過備份..."),
    "Reusing existing backup directory '{}'": ("复用现有的备份目录 '{}'", "重複使用現有的備份目錄 '{}'"),
    "File '{}' already exists. Skipping...": ("文件 '{}' 已存在，跳过...", "檔案 '{}' 已存在，跳過..."),
    "Failed to backup directory '{}': {}": ("备份目录 '{}' 失败：{}", "備份目錄 '{}' 失敗：{}"),
    "No Klipper instances found via systemd services.": ("未通过 systemd 服务找到任何 Klipper 实例。", "未透過 systemd 服務找到任何 Klipper 執行個體。"),
    "Attempting to find printer data directories in home directory...": ("正在尝试在主目录中查找打印机数据目录...", "正在嘗試在使用者家目錄中尋找印表機資料目錄..."),
    "Unable to find directory to backup!": ("找不到要备份的目录！", "找不到要備份的目錄！"),
    "No printer data directories found in home directory.": ("在主目录中未找到任何打印机数据目录。", "在使用者家目錄中未找到任何印表機資料目錄。"),

    # kiauh_settings templates
    "Invalid value '{}' for option '{}' in section '{}'": ("节 '{}' 中选项 '{}' 的值 '{}' 无效", "區段 '{}' 中選項 '{}' 的值 '{}' 無效"),
    "Option '{}' in section '{}' not defined. Falling back to '{}'.": ("节 '{}' 中未定义选项 '{}'，回退到 '{}'。", "區段 '{}' 中未定義選項 '{}'，將使用預設值 '{}'。"),

    # fs_utils templates
    "File '{}' does not exist. Skipped ...": ("文件 '{}' 不存在，已跳过 ...", "檔案 '{}' 不存在，已跳過 ..."),
    "File '{}' was successfully removed!": ("文件 '{}' 已成功移除！", "檔案 '{}' 已成功移除！"),
    "Error removing file '{}': {}": ("移除文件 '{}' 时出错：{}", "移除檔案 '{}' 時發生錯誤：{}"),
    "File '{}' is neither a file nor a directory!": ("'{}' 既不是文件也不是目录！", "'{}' 既不是檔案也不是目錄！"),
    "Unable to delete '{}':\n{}": ("无法删除 '{}'：\n{}", "無法刪除 '{}'：\n{}"),
    "Trying to remove with sudo ...": ("正在尝试使用 sudo 权限移除 ...", "正在嘗試以 sudo 權限移除 ..."),
    "Error deleting '{}' with sudo:\n{}": ("使用 sudo 删除 '{}' 时出错：\n{}", "使用 sudo 刪除 '{}' 時發生錯誤：\n{}"),
    "Remove this directory manually!": ("请手动移除此目录！", "請手動移除此目錄！"),
    "Created directory '{}'!": ("已创建目录 '{}'！", "已建立目錄 '{}'！"),
    "Error creating directories:": ("创建目录时出错：", "建立目錄時發生錯誤："),
    "Failed to create symlink:": ("创建符号链接失败：", "建立符號連結失敗："),
    "Cannot remove file": ("无法删除文件", "無法刪除檔案"),

    # config_utils templates
    "Add section '[{}]' to '{}' ...": ("正在将节 '[{}]' 添加到 '{}' ...", "正在將區段 '[{}]' 加入至 '{}' ..."),
    "'{}' not found!": ("未找到 '{}'！", "找不到 '{}'！"),
    "Section already exist. Skipped ...": ("节已存在，跳过 ...", "區段已存在，跳過 ..."),
    "Remove section '[{}]' from '{}' ...": ("正在从 '{}' 中移除节 '[{}]' ...", "正在從 '{}' 中移除區段 '[{}]' ..."),
    "Section does not exist. Skipped ...": ("节不存在，跳过 ...", "區段不存在，跳過 ..."),

    # sys_utils
    "Versioncheck failed!": ("版本检查失败！", "版本檢查失敗！"),
    "Python {} or newer required.": ("需要 Python {} 或更新版本。", "需要 Python {} 或更新版本。"),
    "Set up Python virtual environment ...": ("正在设置 Python 虚拟环境 ...", "正在設定 Python 虛擬環境 ..."),
    "Setup of virtualenv successful!": ("虚拟环境设置成功！", "虛擬環境設定成功！"),
    "Error setting up virtualenv:\n{}": ("设置虚拟环境时出错：\n{}", "設定虛擬環境時發生錯誤：\n{}"),
    "Virtualenv still exists after deletion.": ("删除后虚拟环境仍然存在。", "刪除後虛擬環境仍然存在。"),
    "Virtualenv already exists. Re-create?": ("虚拟环境已存在，是否重新创建？", "虛擬環境已存在，是否重新建立？"),
    "Skipping re-creation of virtualenv ...": ("跳过重新创建虚拟环境 ...", "跳過重新建立虛擬環境 ..."),
    "Error removing existing virtualenv: {}": ("移除现有虚拟环境时出错：{}", "移除現有虛擬環境時發生錯誤：{}"),
    "Updating pip ...": ("正在更新 pip ...", "正在更新 pip ..."),
    "Error updating pip! Not found.": ("更新 pip 失败！未找到 pip。", "更新 pip 失敗！找不到 pip。"),
    "Updating pip failed!": ("更新 pip 失败！", "更新 pip 失敗！"),
    "Updating pip successful!": ("pip 更新成功！", "pip 更新成功！"),
    "Error updating pip:\n{}": ("更新 pip 时出错：\n{}", "更新 pip 時發生錯誤：\n{}"),
    "Installing Python requirements ...": ("正在安装 Python 依赖 ...", "正在安裝 Python 相依套件 ..."),
    "Installing Python requirements successful!": ("Python 依赖安装成功！", "Python 相依套件安裝成功！"),
    "Installing Python requirements failed!": ("安装 Python 依赖失败！", "安裝 Python 相依套件失敗！"),
    "Error installing Python requirements: {}": ("安装 Python 依赖时出错：{}", "安裝 Python 相依套件時發生錯誤：{}"),
    "Updating package list...": ("正在更新软件包列表...", "正在更新套件清單..."),
    "Updating system package list failed!": ("更新系统软件包列表失败！", "更新系統套件清單失敗！"),
    "System package list update successful!": ("系统软件包列表更新成功！", "系統套件清單更新成功！"),
    "Error updating system package list:\n{}": ("更新系统软件包列表时出错：\n{}", "更新系統套件清單時發生錯誤：\n{}"),
    "Error reading upgradable packages: {}": ("读取可升级软件包时出错：{}", "讀取可升級套件時發生錯誤：{}"),
    "Packages successfully installed.": ("软件包安装成功。", "套件安裝成功。"),
    "Error installing packages:\n{}": ("安装软件包时出错：\n{}", "安裝套件時發生錯誤：\n{}"),
    "Packages successfully upgraded.": ("软件包升级成功。", "套件升級成功。"),
    "Error upgrading packages:\n{}": ("升级软件包时出错：\n{}", "升級套件時發生錯誤：\n{}"),
    "Download failed! HTTP error occured: {}": ("下载失败！发生 HTTP 错误：{}", "下載失敗！發生 HTTP 錯誤：{}"),
    "Download failed! URL error occured: {}": ("下载失败！发生 URL 错误：{}", "下載失敗！發生 URL 錯誤：{}"),
    "Download failed! An error occured: {}": ("下载失败！发生错误：{}", "下載失敗！發生錯誤：{}"),
    "Downloading: [{}{}]{:.2f}% ({:.2f}/{:.2f}MB)": ("下载中：[{}{}]{:.2f}% ({:.2f}/{:.2f}MB)", "下載中：[{}{}]{:.2f}% ({:.2f}/{:.2f}MB)"),
    "Granting NGINX the required permissions ...": ("正在授予 NGINX 所需权限 ...", "正在授予 Nginx 所需權限 ..."),
    "Permissions granted.": ("权限已授予。", "權限已授予。"),
    "Permissions set!": ("权限已设置！", "權限已設定！"),
    "{} successfully removed!": ("已成功移除 {}！", "已成功移除 {}！"),
    "Error removing {}: {}": ("移除 {} 时出错：{}", "移除 {} 時發生錯誤：{}"),
    "service_name '{}' must end with '.service'": ("service_name '{}' 必须以 '.service' 结尾", "service_name '{}' 必須以 '.service' 結尾"),
    "Service '{}' does not exist! Skipped ...": ("服务 '{}' 不存在！跳过 ...", "服務 '{}' 不存在！跳過 ..."),
    "Removing {} ...": ("正在移除 {} ...", "正在移除 {} ..."),
    "Service file created: {}": ("服务文件已创建：{}", "服務檔案已建立：{}"),
    "Error creating service file: {}": ("创建服务文件时出错：{}", "建立服務檔案時發生錯誤：{}"),
    "Env file created: {}": ("环境文件已创建：{}", "環境檔案已建立：{}"),
    "Error creating env file: {}": ("创建环境文件时出错：{}", "建立環境檔案時發生錯誤：{}"),
    "instance_type must be a class": ("instance_type 必须是类", "instance_type 必須是類別"),
    "Error reading distro info!": ("读取发行版信息失败！", "讀取發行版資訊失敗！"),
    "Error reading distro id!": ("读取发行版 ID 失败！", "讀取發行版 ID 失敗！"),
    "Error reading distro version!": ("读取发行版版本失败！", "讀取發行版版本失敗！"),
    "Could not determine system timezone, using UTC": ("无法确定系统时区，使用 UTC", "無法判定系統時區，使用 UTC"),
    "{} {} ...": ("{} {} ...", "{} {} ..."),
    "Failed to run {}: {}": ("运行 {} 失败：{}", "執行 {} 失敗：{}"),
    "Failed to {} {}: {}": ("{} {} 失败：{}", "{} {} 失敗：{}"),
}


def translate(msgid: str) -> Tuple[str, str]:
    """Return (zh_CN, zh_TW) translation for a msgid.

    Strategy:
      1. Try the DIRECT full-string dictionary (exact matches).
      2. Try regex-based sentence templates (e.g. "Error X:", "Xing Y ...").
      3. Apply glossary word-level replacement as a last pass.
    """
    src = msgid
    if src == "":
        return "", ""

    # 1) Direct exact-string
    if src in DIRECT:
        return DIRECT[src]

    # 2) Sentence-template regex matches
    zh_cn, zh_tw = _apply_sentence_templates(src)

    # 3) Word-level glossary on whatever is left
    final_cn, final_tw = _translate_wordlevel(zh_cn if zh_cn != src else src)
    if zh_cn == src:
        zh_cn = final_cn
        zh_tw = final_tw
    else:
        # The sentence template gave us a partially translated string; apply
        # word-level to fill any remaining English words in zh_CN / zh_TW
        pass2_cn, pass2_tw = _translate_wordlevel(zh_cn)
        _p2cn, p2tw = _translate_wordlevel(zh_tw)
        zh_cn = pass2_cn
        zh_tw = p2tw

    return zh_cn, zh_tw


def _re(pattern: str) -> re.Pattern:
    return re.compile(pattern)


SENTENCE_RULES: List[Tuple[re.Pattern, List[Tuple[object, object]]]] = [
    # "Doing action ..." → "正在{动作}{宾语}..."
    # These templates run BEFORE the glossary to capture the whole sentence.
    # Placeholder {} in the replacement receives the captured group.
    # Format: (pattern, list of (cn_template, tw_template) per group count)
    # Group 0 = full match; each subsequent group corresponds to templates.
]
# (kept separate for readability — we'll just apply rules inline below)


def _apply_sentence_templates(src: str) -> Tuple[str, str]:
    """Apply higher-level sentence patterns that glossary alone can't capture."""
    cn, tw = src, src

    # ---- Launching X ...
    m = re.match(r"^Launching (.+?)( install(?:er| configurator))? \.\.\.$", src)
    if m:
        what = m.group(1)
        tail_cn = "安装程序" if m.group(2) else ""
        tail_tw = "安裝程式" if m.group(2) else ""
        return (f"正在启动 {what}{tail_cn} ...", f"正在啟動 {what}{tail_tw} ...")

    # ---- Updating X ... / Removing X ... / Installing X ... / Creating X ...
    for prefix_act, cn_act, tw_act in [
        ("Updating", "更新", "更新"),
        ("Removing", "移除", "移除"),
        ("Installing", "安装", "安裝"),
        ("Creating", "创建", "建立"),
        ("Downloading", "下载", "下載"),
        ("Extracting", "解压", "解壓縮"),
        ("Building", "构建", "建置"),
        ("Flashing", "烧录", "燒錄"),
        ("Restoring", "恢复", "還原"),
        ("Generating", "生成", "產生"),
        ("Scanning", "扫描", "掃描"),
    ]:
        m = re.match(rf"^{prefix_act} (.+) \.\.\.$", src)
        if m:
            what = m.group(1)
            return (f"正在{cn_act} {what} ...", f"正在{tw_act} {what} ...")

    # ---- "Error while [action]ing [X]:"
    m = re.match(r"^Error while (\w+ing) (.+)(?:[:：])?$", src)
    if m:
        action = m.group(1)
        target = m.group(2)
        cn_act, tw_act = _translate_wordlevel(action)
        return (f"{cn_act} {target} 时出错：", f"{tw_act} {target} 時發生錯誤：")

    # ---- "Error [gerund] [X]:" or "Error [preposition gerund] X:"
    m = re.match(r"^Error (\w+ing) (.+)(?::)?$", src)
    if m:
        action = m.group(1)
        target = m.group(2).rstrip(":")
        cn_act, tw_act = _translate_wordlevel(action)
        return (f"{cn_act} {target} 时出错：", f"{tw_act} {target} 時發生錯誤：")

    # ---- "X does not seem to be installed! Skipping ..."
    m = re.match(r"^(.+) does not seem to be installed! Skipping \.\.\.$", src)
    if m:
        return (f"似乎未安装 {m.group(1)}！跳过 ...", f"似乎未安裝 {m.group(1)}！跳過 ...")

    # ---- "X not found!"  (single token)
    m = re.match(r"^(\S+) not found!$", src)
    if m:
        return (f"未找到 {m.group(1)}！", f"找不到 {m.group(1)}！")

    # ---- "X are missing!"
    m = re.match(r"^(.+) are missing!$", src)
    if m:
        return (f"{m.group(1)} 缺失！", f"{m.group(1)} 遺失！")

    # ---- "X will be installed:"
    m = re.match(r"^(.+) will be installed:$", src)
    if m:
        return (f"即将安装 {m.group(1)}：", f"即將安裝 {m.group(1)}：")

    return cn, tw



# ---------------------------------------------------------------------------
# Parser: read POT, split into header + entries, emit both PO files
# ---------------------------------------------------------------------------

def split_pot(text: str) -> Tuple[str, List[Tuple[List[str], str, str]]]:
    """Split POT text into (header, entries).

    Each entry is (comment_lines, msgid, msgstr). Entries preserve source order.
    """
    lines = text.splitlines(keepends=True)
    # header ends with the first blank line followed by a non-header entry (msgid with content)
    header_buf: List[str] = []
    entries: List[Tuple[List[str], str, str]] = []

    i = 0

    # Parse header entry: first msgid "" followed by msgstr "" with metadata
    while i < len(lines) and not lines[i].startswith('msgid ""'):
        header_buf.append(lines[i])
        i += 1

    # Grab the header msgid/msgstr block, including its "fuzzy" marker
    header_metadata: List[str] = []
    while i < len(lines):
        line = lines[i]
        header_metadata.append(line)
        # The header metadata ends at a blank line followed by the next comment / msgid
        if line.strip() == "" and i + 1 < len(lines) and (
            lines[i + 1].startswith("#") or lines[i + 1].startswith("msgid ")
        ):
            i += 1  # skip the blank separator
            break
        i += 1

    header = "".join(header_buf) + "".join(header_metadata)

    # Now parse remaining entries
    while i < len(lines):
        comments: List[str] = []
        # Read optional flags / comments
        while i < len(lines) and lines[i].startswith("#"):
            comments.append(lines[i])
            i += 1

        if i >= len(lines):
            break

        # Read msgid
        if not lines[i].startswith("msgid "):
            i += 1
            continue

        msgid_lines: List[str] = []
        while i < len(lines) and (lines[i].startswith("msgid ") or lines[i].startswith('"')):
            prefix_len = 6 if lines[i].startswith("msgid ") else 0
            raw = lines[i][prefix_len:]  # keep trailing newline
            msgid_lines.append(raw)
            i += 1

        # Skip optional msgid_plural / msgstr[N] entries — for now we only
        # need simple msgid→msgstr for zh (both variants share a single plural form)
        if i < len(lines) and lines[i].startswith("msgid_plural "):
            while i < len(lines) and not (lines[i].strip() == "" and i + 1 < len(lines) and (
                lines[i + 1].startswith("#") or lines[i + 1].startswith("msgid ")
            )):
                i += 1
            # Skip the blank separator too if present
            if i < len(lines) and lines[i].strip() == "":
                i += 1
            # For plural entries we still want them in the catalog — but we
            # already advanced. For simplicity fall through and continue.
            continue

        msgid_src = "".join(msgid_lines)
        msgid_src = msgid_src.rstrip("\n")

        # There should be a msgstr following (possibly multiline).
        msgstr_lines: List[str] = []
        while i < len(lines) and (lines[i].startswith("msgstr ") or lines[i].startswith('"')):
            prefix_len = 7 if lines[i].startswith("msgstr ") else 0
            msgstr_lines.append(lines[i][prefix_len:])
            i += 1

        # Skip blank separator
        if i < len(lines) and lines[i].strip() == "":
            i += 1

        entries.append((comments, msgid_src, "".join(msgstr_lines).rstrip("\n")))

    return header, entries


def _unescape(s: str) -> str:
    """Inverse of PO escaping. We strip leading 'msgid ""' + multiline '"..."' into one string."""
    # Concatenate lines assuming format like '"foo\\n"\n"bar"\n'
    out = []
    for line in s.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('"') and line.endswith('"'):
            line = line[1:-1]
        # Interpret escapes like \n, \", \\
        line = line.replace('\\"', '"').replace("\\\\", "\\")
        line = line.replace("\\n", "\n").replace("\\t", "\t")
        out.append(line)
    return "".join(out)


def _escape(s: str) -> str:
    """Escape a plain string to a msgstr value block (potentially multi-line)."""
    if not s:
        return '""'
    s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\t", "\\t")
    if "\n" in s:
        lines = s.split("\n")
        # The last piece after splitting by \n is empty if s ends in \n — preserve
        pieces: List[str] = []
        for idx, piece in enumerate(lines):
            if idx == len(lines) - 1 and piece == "":
                break
            if idx < len(lines) - 1:
                piece = piece + "\\n"
            pieces.append(f'"{piece}"')
        return '""\n' + "\n".join(pieces)
    return f'"{s}"'


def build_po(header: str, entries: List[Tuple[List[str], str, str]], *,
             language: str, team: str, translator_last: str = "zh-hans-locale-team") -> str:
    """Build a .po file body for a given language.

    header: the raw header extracted from the POT (includes '#', fuzzy marker,
            msgid "" and msgstr "" metadata block).
    language: "zh_CN" or "zh_TW"
    """
    out: List[str] = []

    # --- Rewrite the header metadata block -----------------------------------
    # We split the header into initial comments and the metadata msgid/msgstr,
    # then rewrite msgstr "" contents with the correct Language, Plural-Forms,
    # charset, etc.

    # Split into leading comment lines (starting with #) and the rest.
    header_lines = header.splitlines(keepends=True)
    leading_comments: List[str] = []
    metadata_start = 0
    for idx, line in enumerate(header_lines):
        if line.startswith("#") or line.strip() == "":
            leading_comments.append(line)
        else:
            metadata_start = idx
            break

    # Skip the '#, fuzzy' line for a complete translation.
    cleaned_leading: List[str] = []
    for line in leading_comments:
        if "#, fuzzy" in line:
            continue  # remove fuzzy — zh_CN & zh_TW are fully translated
        cleaned_leading.append(line)
    out.extend(cleaned_leading)

    plural_forms = {
        "zh_CN": "nplurals=1; plural=0;",
        "zh_TW": "nplurals=1; plural=0;",
    }[language]

    metadata = (
        'msgid ""\n'
        'msgstr ""\n'
        f'"Project-Id-Version: KIAUH 1.0\\n"\n'
        f'"Report-Msgid-Bugs-To: https://github.com/dw-0/kiauh/issues\\n"\n'
        f'"POT-Creation-Date: 2026-08-03 00:41-0700\\n"\n'
        f'"PO-Revision-Date: 2026-08-03 00:41-0700\\n"\n'
        f'"Last-Translator: KIAUH i18n contributors <{translator_last}@example.com>\\n"\n'
        f'"Language-Team: {team}\\n"\n'
        f'"Language: {language}\\n"\n'
        f'"MIME-Version: 1.0\\n"\n'
        f'"Content-Type: text/plain; charset=UTF-8\\n"\n'
        f'"Content-Transfer-Encoding: 8bit\\n"\n'
        f'"Plural-Forms: {plural_forms}\\n"\n'
    )
    out.append(metadata)
    out.append("\n")

    # --- Entries ------------------------------------------------------------
    for comments, msgid_src, _msgstr_src in entries:
        # Strip surrounding whitespace-only lines
        for c in comments:
            out.append(c)
        raw_msgid = _unescape(msgid_src)
        if raw_msgid == "":
            continue  # skip the header placeholder, already emitted above
        zh_cn, zh_tw = translate(raw_msgid)
        translated = zh_cn if language == "zh_CN" else zh_tw
        out.append(f"msgid {_escape(raw_msgid)}\n")
        out.append(f"msgstr {_escape(translated)}\n")
        out.append("\n")

    return "".join(out)


# ---------------------------------------------------------------------------
# Rebase workflow helpers (xgettext extract + msgmerge fuzzy-merge)
# ---------------------------------------------------------------------------

KIAUH_ROOT = Path(__file__).resolve().parent / "kiauh"


def cmd_extract_pot() -> None:
    """Re-run xgettext to produce a fresh messages.pot from .py sources."""
    py_files = sorted(str(p.relative_to(KIAUH_ROOT)) for p in KIAUH_ROOT.rglob("*.py"))
    filelist = "\n".join(py_files).encode()
    cmd = [
        "xgettext",
        "--language=Python",
        "--from-code=UTF-8",
        f"--output={POT_FILE}",
        "--keyword=_tr:1",
        "--keyword=_ntr:1,2",
        "--keyword=N_:1",
        "--sort-by-file",
        "--no-wrap",
        "--package-name=kiauh",
        "--msgid-bugs-address=zach@adam.new",
        "--files-from=-",
    ]
    subprocess.run(cmd, cwd=KIAUH_ROOT, input=filelist, check=True)
    n = sum(1 for line in POT_FILE.read_text(encoding="utf-8").splitlines() if line.startswith("msgid "))
    print(f"✓ extracted {POT_FILE} ({n} msgids)")


def cmd_merge_po(po_file: Path) -> int:
    """Run msgmerge --previous --update on one PO file. Returns fuzzy+empty count."""
    subprocess.run(
        ["msgmerge", "--previous", "--update", "--quiet", str(po_file), str(POT_FILE)],
        check=True,
    )
    # Count fuzzy + empty untranslated entries
    text = po_file.read_text(encoding="utf-8")
    fuzzy = text.count("#, fuzzy")
    empty = len(re.findall(r'^msgstr ""\s*$', text, flags=re.M)) - 1  # -1 for header
    total = len(re.findall(r'^msgid "', text, flags=re.M)) - 1
    print(f"  ✓ merged {po_file.relative_to(Path.cwd())}: {total} total, {fuzzy} fuzzy, {max(0, empty)} empty msgstr")
    return fuzzy + max(0, empty)


def po_has_any_empty_msgstr(po_file: Path) -> bool:
    """True if po has any non-header entry with msgstr = ""."""
    lines = po_file.read_text(encoding="utf-8").splitlines()
    in_msgid, seen_nonempty = False, False
    empty_count = 0
    for ln in lines:
        if ln.startswith('msgid "'):
            in_msgid = True
            seen_nonempty = ln != 'msgid ""'
        elif ln.startswith('msgstr "') and in_msgid:
            if seen_nonempty and ln == 'msgstr ""':
                empty_count += 1
            in_msgid = False
    return empty_count > 0


def po_stats_after_build(pot_entries: List[Tuple[str, str, str]]) -> Dict[str, int]:
    stats: Dict[str, int] = {}
    for lang in ("zh_CN", "zh_TW"):
        n = 0
        for _comments, msgid_src, _ in pot_entries:
            raw = _unescape(msgid_src)
            if raw == "":
                continue
            cn, tw = translate(raw)
            result = cn if lang == "zh_CN" else tw
            if result.strip() == raw.strip():
                n += 1
        stats[lang] = n
    return stats


# ---------------------------------------------------------------------------
# main entry point
# ---------------------------------------------------------------------------

def main_generate() -> None:
    """Default mode: build zh_CN.po + zh_TW.po from the current .pot,
    using the rule-based translator to fill msgstrs."""
    if not POT_FILE.exists():
        raise SystemExit(f"POT file not found: {POT_FILE}")

    text = POT_FILE.read_text(encoding="utf-8")
    header, entries = split_pot(text)

    ZH_CN_PO.parent.mkdir(parents=True, exist_ok=True)
    ZH_TW_PO.parent.mkdir(parents=True, exist_ok=True)

    po_cn = build_po(
        header, entries,
        language="zh_CN",
        team="Chinese Simplified <zh_CN@li.org>",
        translator_last="zh-cn-translators",
    )
    ZH_CN_PO.write_text(po_cn, encoding="utf-8")
    print(f"✓ wrote {ZH_CN_PO}")

    po_tw = build_po(
        header, entries,
        language="zh_TW",
        team="Chinese Traditional <zh_TW@li.org>",
        translator_last="zh-tw-translators",
    )
    ZH_TW_PO.write_text(po_tw, encoding="utf-8")
    print(f"✓ wrote {ZH_TW_PO}")
    print(f"  Total entries: {len(entries)}")

    stats = po_stats_after_build(entries)
    print(f"  zh_CN: {stats['zh_CN']} strings still match source (untranslated catch-all)")
    print(f"  zh_TW: {stats['zh_TW']} strings still match source (untranslated catch-all)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build / rebase zh_CN + zh_TW translation catalogs for KIAUH.",
    )
    parser.add_argument("--extract", action="store_true",
                        help="Only re-run xgettext to produce a fresh kiauh/locale/messages.pot")
    parser.add_argument("--merge", action="store_true",
                        help="Only run msgmerge --previous --update for zh_CN.po and zh_TW.po")
    parser.add_argument("--rebase", action="store_true",
                        help="--extract + --merge + regenerate untranslated entries via rules")
    args = parser.parse_args()

    if args.rebase:
        print("=== [REBASE step 1/3] xgettext extract ===")
        cmd_extract_pot()
        print("=== [REBASE step 2/3] msgmerge fuzzy merge ===")
        untranslated = cmd_merge_po(ZH_CN_PO) + cmd_merge_po(ZH_TW_PO)
        print("=== [REBASE step 3/3] rule-based re-fill of any empty msgstr ===")
        main_generate()
        if untranslated:
            print("⚠  Note: msgmerge flagged fuzzy/empty entries above. Hand-review the")
            print("   fuzzy-marked (#, fuzzy) entries in zh_CN.po / zh_TW.po with Poedit or")
            print("   your favourite editor, then run:  msgfmt -c *.po → *.mo  to compile.")
        return

    if args.extract:
        cmd_extract_pot()
        return

    if args.merge:
        cmd_merge_po(ZH_CN_PO)
        cmd_merge_po(ZH_TW_PO)
        return

    # Default: just build zh_CN + zh_TW from messages.pot
    main_generate()


if __name__ == "__main__":
    main()
