#!/bin/bash
clear
set -e

### set color variables
green=$(echo -en "\e[92m")
yellow=$(echo -en "\e[93m")
red=$(echo -en "\e[91m")
cyan=$(echo -en "\e[96m")
default=$(echo -en "\e[39m")

### sourcing all additional scripts
SRCDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/.. && pwd )"
for script in "${SRCDIR}/kiauh/scripts/"*.sh; do . $script; done
for script in "${SRCDIR}/kiauh/scripts/ui/"*.sh; do . $script; done

### set important directories
#klipper
KLIPPER_DIR=${HOME}/klipper
KLIPPY_ENV=${HOME}/klippy-env
#nginx
NGINX_SA=/etc/nginx/sites-available
NGINX_SE=/etc/nginx/sites-enabled
NGINX_CONFD=/etc/nginx/conf.d
#moonraker
MOONRAKER_DIR=${HOME}/moonraker
MOONRAKER_ENV=${HOME}/moonraker-env
#mainsail
MAINSAIL_DIR=${HOME}/mainsail
#fluidd
FLUIDD_DIR=${HOME}/fluidd
#dwc2
DWC2FK_DIR=${HOME}/dwc2-for-klipper-socket
DWC_ENV_DIR=${HOME}/dwc-env
DWC2_DIR=${HOME}/duetwebcontrol
#octoprint
OCTOPRINT_DIR=${HOME}/OctoPrint
#KlipperScreen
KLIPPERSCREEN_DIR=${HOME}/KlipperScreen
KLIPPERSCREEN_ENV_DIR=${HOME}/.KlipperScreen-env
#MoonrakerTelegramBot
MOONRAKER_TELEGRAM_BOT_DIR=${HOME}/moonraker-telegram-bot
MOONRAKER_TELEGRAM_BOT_ENV_DIR=${HOME}/moonraker-telegram-bot-env
#misc
INI_FILE=${HOME}/.kiauh.ini
BACKUP_DIR=${HOME}/kiauh-backups

### set github repos
KLIPPER_REPO=https://github.com/Klipper3d/klipper.git
ARKSINE_REPO=https://github.com/Arksine/klipper.git
DMBUTYUGIN_REPO=https://github.com/dmbutyugin/klipper.git
DWC2FK_REPO=https://github.com/Stephan3/dwc2-for-klipper-socket.git
KLIPPERSCREEN_REPO=https://github.com/jordanruthe/KlipperScreen.git
NLEF_REPO=https://github.com/nlef/moonraker-telegram-bot.git
#branches
BRANCH_SCURVE_SMOOTHING=dmbutyugin/scurve-smoothing
BRANCH_SCURVE_SHAPING=dmbutyugin/scurve-shaping

### set some messages
warn_msg(){
  echo -e "${red}<!!!!> $1${default}"
}
status_msg(){
  echo; echo -e "${yellow}###### $1${default}"
}
ok_msg(){
  echo -e "${green}>>>>>> $1${default}"
}
title_msg(){
  echo -e "${cyan}$1${default}"
}
get_date(){
  current_date=$(date +"%y%m%d-%H%M")
}
print_unkown_cmd(){
  ERROR_MSG="Invalid command!"
}

print_msg(){
  if [[ "$ERROR_MSG" != "" ]]; then
    echo -e "${red}"
    echo -e "#########################################################"
    echo -e " $ERROR_MSG "
    echo -e "#########################################################"
    echo -e "${default}"
  fi
  if [ "$CONFIRM_MSG" != "" ]; then
    echo -e "${green}"
    echo -e "#########################################################"
    echo -e " $CONFIRM_MSG "
    echo -e "#########################################################"
    echo -e "${default}"
  fi
}

clear_msg(){
  unset CONFIRM_MSG
  unset ERROR_MSG
}

check_euid
init_ini
kiauh_status
main_menu
