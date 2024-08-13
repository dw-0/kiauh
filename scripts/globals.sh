#!/usr/bin/env bash

#=======================================================================#
# Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>       #
#                                                                       #
# This file is part of KIAUH - Klipper Installation And Update Helper   #
# https://github.com/dw-0/kiauh                                         #
#                                                                       #
# This file may be distributed under the terms of the GNU GPLv3 license #
#=======================================================================#

# shellcheck disable=SC2034
set -e

function set_globals() {
  #region System
  SYSTEMD="/etc/systemd/system"
  INITD="/etc/init.d"
  ETCDEF="/etc/default"
  #endregion

  #region Console Colors
  green=$(echo -en "\e[92m")
  yellow=$(echo -en "\e[93m")
  magenta=$(echo -en "\e[35m")
  red=$(echo -en "\e[91m")
  cyan=$(echo -en "\e[96m")
  white=$(echo -en "\e[39m")
  #endregion

  #region KIAUH
  INI_FILE="${HOME}/.kiauh.ini"
  LOGFILE="/tmp/kiauh.log"
  RESOURCES="${KIAUH_SRCDIR}/resources"
  BACKUP_DIR="${HOME}/kiauh-backups"
  #endregion

  #region Klipper
  KLIPPY_ENV="${HOME}/klippy-env"
  KLIPPER_DIR="${HOME}/klipper"
  KLIPPER_REPO="https://github.com/Klipper3d/klipper.git"
  #endregion

  #region Moonraker
  MOONRAKER_ENV="${HOME}/moonraker-env"
  MOONRAKER_DIR="${HOME}/moonraker"
  MOONRAKER_REPO="https://github.com/Arksine/moonraker.git"
  #endregion

  #region Mainsail
  MAINSAIL_DIR="${HOME}/mainsail"
  #endregion

  #region Fluidd
  FLUIDD_DIR="${HOME}/fluidd"
  #endregion

  #region Klipperscreen
  KLIPPERSCREEN_ENV="${HOME}/.KlipperScreen-env"
  KLIPPERSCREEN_DIR="${HOME}/KlipperScreen"
  KLIPPERSCREEN_REPO="https://github.com/jordanruthe/KlipperScreen.git"
  #endregion

  #region Moonraker-Telegram-Bot
  TELEGRAM_BOT_ENV="${HOME}/moonraker-telegram-bot-env"
  TELEGRAM_BOT_DIR="${HOME}/moonraker-telegram-bot"
  TELEGRAM_BOT_REPO="https://github.com/nlef/moonraker-telegram-bot.git"
  #endregion

  #region Pretty-Gcode
  PGC_DIR="${HOME}/pgcode"
  PGC_REPO="https://github.com/Kragrathea/pgcode"
  #endregion

  #region Nginx
  NGINX_SA="/etc/nginx/sites-available"
  NGINX_SE="/etc/nginx/sites-enabled"
  NGINX_CONFD="/etc/nginx/conf.d"
  #endregion

  #region Moonraker-Obico
  MOONRAKER_OBICO_DIR="${HOME}/moonraker-obico"
  MOONRAKER_OBICO_REPO="https://github.com/TheSpaghettiDetective/moonraker-obico.git"
  #endregion

  #region OctoEverywhere
  OCTOEVERYWHERE_ENV="${HOME}/octoeverywhere-env"
  OCTOEVERYWHERE_DIR="${HOME}/octoeverywhere"
  OCTOEVERYWHERE_REPO="https://github.com/QuinnDamerell/OctoPrint-OctoEverywhere.git"
  #endregion

  #region Crowsnest
  CROWSNEST_DIR="${HOME}/crowsnest"
  CROWSNEST_REPO="https://github.com/mainsail-crew/crowsnest.git"
  #endregion

  #region Mobileraker
  MOBILERAKER_ENV="${HOME}/mobileraker-env"
  MOBILERAKER_DIR="${HOME}/mobileraker_companion"
  MOBILERAKER_REPO="https://github.com/Clon1998/mobileraker_companion.git"
  #endregion

  #region OctoApp
  OCTOAPP_ENV="${HOME}/octoapp-env"
  OCTOAPP_DIR="${HOME}/octoapp"
  OCTOAPP_REPO="https://github.com/crysxd/OctoApp-Plugin.git"
  #endregion

  #region Spoolman
  SPOOLMAN_DIR="${HOME}/Spoolman"
  SPOOLMAN_DB_DIR="${HOME}/.local/share/spoolman"
  SPOOLMAN_REPO="https://api.github.com/repos/Donkie/Spoolman/releases/latest"
  #endregion
}
