#!/bin/bash
### set important directories

# klipper
readonly KLIPPER_DIR=${HOME}/klipper
readonly KLIPPY_ENV=${HOME}/klippy-env
#nginx
readonly NGINX_SA=/etc/nginx/sites-available
readonly NGINX_SE=/etc/nginx/sites-enabled
readonly NGINX_CONFD=/etc/nginx/conf.d
#moonraker
readonly MOONRAKER_DIR=${HOME}/moonraker
readonly MOONRAKER_ENV=${HOME}/moonraker-env
readonly MOONRAKER_REPO="https://github.com/Arksine/moonraker.git"
#mainsail
readonly MAINSAIL_DIR=${HOME}/mainsail
#fluidd
readonly FLUIDD_DIR=${HOME}/fluidd
#dwc2
readonly DWC2FK_DIR=${HOME}/dwc2-for-klipper-socket
readonly DWC_ENV_DIR=${HOME}/dwc-env
readonly DWC2_DIR=${HOME}/duetwebcontrol
#octoprint
readonly OCTOPRINT_DIR=${HOME}/OctoPrint
readonly OCTOPRINT_ENV_DIR=${HOME}/OctoPrint/env
#KlipperScreen
readonly KLIPPERSCREEN_DIR=${HOME}/KlipperScreen
readonly KLIPPERSCREEN_ENV_DIR=${HOME}/.KlipperScreen-env
#MoonrakerTelegramBot
readonly MOONRAKER_TELEGRAM_BOT_DIR=${HOME}/moonraker-telegram-bot
readonly MOONRAKER_TELEGRAM_BOT_ENV_DIR=${HOME}/moonraker-telegram-bot-env
#misc
readonly INI_FILE=${HOME}/.kiauh.ini
readonly BACKUP_DIR=${HOME}/kiauh-backups
readonly SYSTEMD_DIR=/etc/systemd/system
#set github repos
readonly KLIPPER_REPO=https://github.com/Klipper3d/klipper.git
readonly ARKSINE_REPO=https://github.com/Arksine/klipper.git
readonly DMBUTYUGIN_REPO=https://github.com/dmbutyugin/klipper.git
readonly DWC2FK_REPO=https://github.com/Stephan3/dwc2-for-klipper-socket.git
readonly KLIPPERSCREEN_REPO=https://github.com/jordanruthe/KlipperScreen.git
readonly NLEF_REPO=https://github.com/nlef/moonraker-telegram-bot.git
#branches
readonly BRANCH_SCURVE_SMOOTHING=dmbutyugin/scurve-smoothing
readonly BRANCH_SCURVE_SHAPING=dmbutyugin/scurve-shaping
#Webcam
readonly WEBCAMD_SRC="https://raw.githubusercontent.com/raymondh2/MainsailOS/master/src/modules/mjpgstreamer/filesystem/root/usr/local/bin/webcamd"
readonly WEBCAM_TXT_SRC="https://raw.githubusercontent.com/raymondh2/MainsailOS/master/src/modules/mjpgstreamer/filesystem/home/pi/klipper_config/webcam.txt"
#Whiptail
readonly KIAUH_WHIPTAIL_NORMAL_WIDTH=70
readonly KIAUH_WHIPTAIL_NORMAL_HEIGHT=24
readonly KIAUH_WHIPTAIL_SINGLE_LINE_HEIGHT=7
