#!/usr/bin/env bash

#=======================================================================#
# Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>       #
#                                                                       #
# This file is part of KIAUH - Klipper Installation And Update Helper   #
# https://github.com/th33xitus/kiauh                                    #
#                                                                       #
# This file may be distributed under the terms of the GNU GPLv3 license #
#=======================================================================#

# shellcheck disable=SC2034
set -e

function set_globals() {
  #=================== SYSTEM ===================#
  SYSTEMD="/etc/systemd/system"
  INITD="/etc/init.d"
  ETCDEF="/etc/default"

  #=================== KIAUH ====================#
  green=$(echo -en "\e[92m")
  yellow=$(echo -en "\e[93m")
  magenta=$(echo -en "\e[35m")
  red=$(echo -en "\e[91m")
  cyan=$(echo -en "\e[96m")
  white=$(echo -en "\e[39m")
  INI_FILE="${HOME}/.kiauh.ini"
  LOGFILE="/tmp/kiauh.log"
  RESOURCES="${KIAUH_SRCDIR}/resources"
  BACKUP_DIR="${HOME}/kiauh-backups"

  #================== KLIPPER ===================#
  KLIPPY_ENV="${HOME}/klippy-env"
  KLIPPER_DIR="${HOME}/klipper"
  KLIPPER_REPO="https://github.com/Klipper3d/klipper.git"

  #================= MOONRAKER ==================#
  MOONRAKER_ENV="${HOME}/moonraker-env"
  MOONRAKER_DIR="${HOME}/moonraker"
  MOONRAKER_REPO="https://github.com/Arksine/moonraker.git"

  #================= MAINSAIL ===================#
  MAINSAIL_DIR="${HOME}/mainsail"

  #================== FLUIDD ====================#
  FLUIDD_DIR="${HOME}/fluidd"

  #=============== KLIPPERSCREEN ================#
  KLIPPERSCREEN_ENV="${HOME}/.KlipperScreen-env"
  KLIPPERSCREEN_DIR="${HOME}/KlipperScreen"
  KLIPPERSCREEN_REPO="https://github.com/jordanruthe/KlipperScreen.git"

  #========== MOONRAKER-TELEGRAM-BOT ============#
  TELEGRAM_BOT_ENV="${HOME}/moonraker-telegram-bot-env"
  TELEGRAM_BOT_DIR="${HOME}/moonraker-telegram-bot"
  TELEGRAM_BOT_REPO="https://github.com/nlef/moonraker-telegram-bot.git"

  #=============== PRETTY-GCODE =================#
  PGC_DIR="${HOME}/pgcode"
  PGC_REPO="https://github.com/Kragrathea/pgcode"

  #================== NGINX =====================#
  NGINX_SA="/etc/nginx/sites-available"
  NGINX_SE="/etc/nginx/sites-enabled"
  NGINX_CONFD="/etc/nginx/conf.d"

  #=============== MOONRAKER-OBICO ================#
  MOONRAKER_OBICO_DIR="${HOME}/moonraker-obico"
  MOONRAKER_OBICO_REPO="https://github.com/TheSpaghettiDetective/moonraker-obico.git"

  #=============== OCTOEVERYWHERE ================#
  OCTOEVERYWHERE_ENV="${HOME}/octoeverywhere-env"
  OCTOEVERYWHERE_DIR="${HOME}/octoeverywhere"
  OCTOEVERYWHERE_REPO="https://github.com/QuinnDamerell/OctoPrint-OctoEverywhere.git"

  #=============== Crowsnest ================#
  CROWSNEST_DIR="${HOME}/crowsnest"
  CROWSNEST_REPO="https://github.com/mainsail-crew/crowsnest.git"

}
