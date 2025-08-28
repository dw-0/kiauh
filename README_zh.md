# KIAUH - Klipper 安装与更新助手

<p align="center">
  <a>
    <img src="https://raw.githubusercontent.com/dw-0/kiauh/master/resources/screenshots/kiauh.png" alt="KIAUH logo" height="181">
    <h1 align="center">Klipper Installation And Update Helper</h1>
  </a>
</p>

<p align="center">
  一个方便的安装脚本，让安装Klipper（以及更多组件）变得轻松！
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

## 📄 使用说明

### 📋 系统要求
KIAUH 是一个帮助您在 Linux 系统上安装 Klipper 的脚本工具，
它需要一个已经写入树莓派（或其他单板计算机）SD 卡的 Linux 系统。
如果您使用树莓派，推荐使用 `Raspberry Pi OS Lite (32位或64位)` 系统镜像。
[官方 Raspberry Pi Imager](https://www.raspberrypi.com/software/) 是将此类镜像写入 SD 卡的最简单方式。

* 下载、安装并启动 Raspberry Pi Imager 后，
选择 `Choose OS -> Raspberry Pi OS (other)`:

<p align="center">
  <img src="https://raw.githubusercontent.com/dw-0/kiauh/master/resources/screenshots/rpi_imager1.png" alt="KIAUH logo" height="350">
</p>

* 然后选择 `Raspberry Pi OS Lite (32位)` (或如果您想使用64位版本):

<p align="center">
  <img src="https://raw.githubusercontent.com/dw-0/kiauh/master/resources/screenshots/rpi_imager2.png" alt="KIAUH logo" height="350">
</p>

* 返回 Raspberry Pi Imager 主界面，选择对应的 SD 卡作为写入目标。

* 确保点击左下角的齿轮图标（在主菜单中）
启用 SSH 并配置 Wi-Fi。

* 如果您需要更多关于使用 Raspberry Pi Imager 的帮助，请访问 [官方文档](https://www.raspberrypi.com/documentation/computers/getting-started.html)。

这些步骤**仅适用于**您实际使用树莓派的情况。如果您想使用其他单板计算机（如香橙派或其他 Pi 衍生产品），
请查找如何将合适的 Linux 镜像写入 SD 卡（通常使用 Balena Etcher）。
同时确保 KIAUH 能够在您要安装的 Linux 发行版上运行。
您在使用基于 Debian 11 Bullseye 的系统时可能会获得最佳体验。
请阅读本文档下方的注意事项。

### 💾 下载并使用 KIAUH

**📢 免责声明：使用此脚本的风险由您自行承担！**

* **第一步：**
要下载此脚本，需要先安装 git。
如果您不确定是否已安装 git，请运行以下命令：
```shell
sudo apt-get update && sudo apt-get install git -y
```

* **第二步：**
安装完 git 后，
使用以下命令将 KIAUH 下载到您的主目录：

```shell
cd ~ && git clone https://github.com/dw-0/kiauh.git
```

* **第三步：**
最后，通过运行以下命令启动 KIAUH：

```shell
./kiauh/kiauh.sh
```

* **第四步：**
您现在应该会看到 KIAUH 的主菜单。
根据您的选择，
您会看到几个可选操作。
要选择某个操作，只需在 "Perform action" 提示后输入对应的数字并按回车键确认。

## ❗ 注意事项

### **📋 请查看 [更新日志](docs/changelog.md) 以了解可能的重要更新！**

- 主要在 Raspberry Pi OS Lite (Debian 10 Buster / Debian 11 Bullseye) 上测试
    - 其他基于 Debian 的发行版（如 Ubuntu 20 到 22）也可能正常工作
    - 据报告在 Armbian 上也可用，但未进行详细测试
- 在使用此脚本的过程中，
您会被要求输入 sudo 密码。
因为有几个功能需要 sudo 权限。

## 🌐 相关资源与更多信息

<table align="center">
<tr>
    <th><h3><a href="https://github.com/Klipper3d/klipper">Klipper</a></h3></th>
    <th><h3><a href="https://github.com/Arksine/moonraker">Moonraker</a></h3></th>
    <th><h3><a href="https://github.com/mainsail-crew/mainsail">Mainsail</a></h3></th>
</tr>
<tr>
    <th><img src="https://raw.githubusercontent.com/Klipper3d/klipper/master/docs/img/klipper-logo.png" alt="Klipper Logo" height="64"></th>
    <th><img src="https://avatars.githubusercontent.com/u/9563098?v=4" alt="Arksine avatar" height="64"></th>
    <th><img src="https://raw.githubusercontent.com/mainsail-crew/docs/master/assets/img/logo.png" alt="Mainsail Logo" height="64"></th>
</tr>
<tr>
    <th>由 <a href="https://github.com/KevinOConnor">KevinOConnor</a></th>
    <th>由 <a href="https://github.com/Arksine">Arksine</a></th>
    <th>由 <a href="https://github.com/mainsail-crew">mainsail-crew</a></th>
</tr>

<tr>
    <th><h3><a href="https://github.com/fluidd-core/fluidd">Fluidd</a></h3></th>
    <th><h3><a href="https://github.com/jordanruthe/KlipperScreen">KlipperScreen</a></h3></th>
    <th><h3><a href="https://github.com/OctoPrint/OctoPrint">OctoPrint</a></h3></th>
</tr>
<tr>
    <th><img src="https://raw.githubusercontent.com/fluidd-core/fluidd/master/docs/assets/images/logo.svg" alt="Fluidd Logo" height="64"></th>
    <th><img src="https://avatars.githubusercontent.com/u/31575189?v=4" alt="jordanruthe avatar" height="64"></th>
    <th><img src="https://raw.githubusercontent.com/OctoPrint/OctoPrint/master/docs/images/octoprint-logo.png" alt="OctoPrint Logo" height="64"></th>
</tr>
<tr>
    <th>由 <a href="https://github.com/fluidd-core">fluidd-core</a></th>
    <th>由 <a href="https://github.com/jordanruthe">jordanruthe</a></th>
    <th>由 <a href="https://github.com/OctoPrint">OctoPrint</a></th>
</tr>

<tr>
    <th><h3><a href="https://github.com/nlef/moonraker-telegram-bot">Moonraker-Telegram-Bot</a></h3></th>
    <th><h3><a href="https://github.com/Kragrathea/pgcode">PrettyGCode for Klipper</a></h3></th>
    <th><h3><a href="https://github.com/TheSpaghettiDetective/moonraker-obico">Obico for Klipper</a></h3></th>
</tr>
<tr>
    <th><img src="https://avatars.githubusercontent.com/u/52351624?v=4" alt="nlef avatar" height="64"></th>
    <th><img src="https://avatars.githubusercontent.com/u/5917231?v=4" alt="Kragrathea avatar" height="64"></th>
    <th><img src="https://avatars.githubusercontent.com/u/46323662?s=200&v=4" alt="Obico logo" height="64"></th>
</tr>
<tr>
    <th>由 <a href="https://github.com/nlef">nlef</a></th>
    <th>由 <a href="https://github.com/Kragrathea">Kragrathea</a></th>
    <th>由 <a href="https://github.com/TheSpaghettiDetective">Obico</a></th>
</tr>

<tr>
    <th><h3><a href="https://github.com/Clon1998/mobileraker_companion">Mobileraker's Companion</a></h3></th>
    <th><h3><a href="https://octoeverywhere.com/?source=kiauh_readme">OctoEverywhere For Klipper</a></h3></th>
    <th><h3><a href="https://github.com/crysxd/OctoApp-Plugin">OctoApp For Klipper</a></h3></th>
</tr>
<tr>
    <th><a href="https://github.com/Clon1998/mobileraker_companion"><img src="https://raw.githubusercontent.com/Clon1998/mobileraker/master/assets/icon/mr_appicon.png" alt="Mobileraker Logo" height="64"></a></th>
    <th><a href="https://octoeverywhere.com/?source=kiauh_readme"><img src="https://octoeverywhere.com/img/logo.svg" alt="OctoEverywhere Logo" height="64"></a></th>
    <th><a href="https://octoapp.eu/?source=kiauh_readme"><img src="https://octoapp.eu/octoapp.webp" alt="OctoApp Logo" height="64"></a></th>
</tr>
<tr>
    <th>由 <a href="https://github.com/Clon1998">Patrick Schmidt</a></th>
    <th>由 <a href="https://github.com/QuinnDamerell">Quinn Damerell</a></th>
    <th>由 <a href="https://github.com/crysxd">Christian Würthner</a></th>
</tr>

<tr>
    <th><h3><a href="https://github.com/staubgeborener/klipper-backup">Klipper-Backup</a></h3></th>
    <th><h3><a href="https://simplyprint.io/">SimplyPrint for Klipper</a></h3></th>
</tr>
<tr>
    <th><a href="https://github.com/staubgeborener/klipper-backup"><img src="https://avatars.githubusercontent.com/u/28908603?v=4" alt="Staubgeroner Avatar" height="64"></a></th>
    <th><a href="https://github.com/SimplyPrint"><img src="https://avatars.githubusercontent.com/u/64896552?s=200&v=4" alt="" height="64"></a></th>
</tr>
<tr>
    <th>由 <a href="https://github.com/Staubgeborener">Staubgeborener</a></th>
    <th>由 <a href="https://github.com/SimplyPrint">SimplyPrint</a></th>
</tr>
</table>

## 🎖️ 贡献者

<div align="center">
  <a href="https://github.com/dw-0/kiauh/graphs/contributors">
    <img src="https://contrib.rocks/image?repo=dw-0/kiauh" alt=""/>
  </a>
</div>

<div align="center">
    <img src="https://repobeats.axiom.co/api/embed/a1afbda9190c04a90cf4bd3061e5573bc836cb05.svg" alt="Repobeats analytics image"/>
</div>

## ✨ 特别感谢

* 非常感谢 [lixxbox](https://github.com/lixxbox) 设计了如此出色的 KIAUH 标志！
* 同时，非常感谢所有通过 [Ko-fi](https://ko-fi.com/dw__0) 支持我的工作的人！
* 最后但同样重要的是：感谢所有为 Klipper 社区做出贡献的成员，以及喜欢和分享这个项目的朋友们！

<h4 align="center">特别感谢 JetBrains 为本项目提供其出色的软件赞助！</h4>
<p align="center">
  <a href="https://www.jetbrains.com/community/opensource/#support" target="_blank">
    <img src="https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.png" alt="JetBrains Logo (Main) logo." height="128">
  </a>
</p>
