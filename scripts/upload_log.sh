#!/usr/bin/env bash

#=======================================================================#
# Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>       #
#                                                                       #
# This file is part of KIAUH - Klipper Installation And Update Helper   #
# https://github.com/th33xitus/kiauh                                    #
#                                                                       #
# This file may be distributed under the terms of the GNU GPLv3 license #
#=======================================================================#

set -e

function accept_upload_conditions() {
  top_border
  echo -e "|     ${red}~~~~~~~~~~~ [ Upload Agreement ] ~~~~~~~~~~~~${white}     |"
  hr
  echo -e "| The following function will help to quickly upload    |"
  echo -e "| logs for debugging purposes. With confirming this     |"
  echo -e "| dialog, you agree that during that process your logs  |"
  echo -e "| will be uploaded to: ${yellow}http://paste.c-net.org/${white}          |"
  hr
  echo -e "| ${red}PLEASE NOTE:${white}                                          |"
  echo -e "| Be aware that logs can contain network information,   |"
  echo -e "| private data like usernames, filenames, or other      |"
  echo -e "| information you may not want to make public.          |"
  blank_line
  echo -e "| Do ${red}NOT${white} use this function if you don't agree!          |"
  bottom_border

  local yn
  while true; do
    read -p "${cyan}Do you accept? (Y/n):${white} " yn
    case "${yn}" in
      Y|y|Yes|yes|"")
        sed -i "/logupload_accepted=/s/false/true/" "${INI_FILE}"
        clear && print_header && upload_selection
        ;;
      N|n|No|no)
        clear
        main_menu
        break
        ;;
      *)
        error_msg "Invalid command!";;
    esac
  done
}

function upload_selection() {
  read_kiauh_ini "${FUNCNAME[0]}"

  local upload_agreed="${logupload_accepted}"
  [[ ${upload_agreed} == "false" ]] && accept_upload_conditions

  local logfiles
  local logs_dir="${KLIPPER_LOGS}"
  local webif_logs="/var/log/nginx"

  function find_logfile() {
    local name=${1} location=${2}
    for log in $(find "${location}" -maxdepth 1 -regextype posix-extended -regex "${location}/${name}" | sort -g); do
      logfiles+=("${log}")
    done
  }

  find_logfile "kiauh\.log" "/tmp"
  find_logfile "klippy(-[0-9a-zA-Z]+)?\.log" "${logs_dir}"
  find_logfile "moonraker(-[0-9a-zA-Z]+)?\.log" "${logs_dir}"
  find_logfile "telegram(-[0-9a-zA-Z]+)?\.log" "${logs_dir}"
  find_logfile "mainsail.*" "${webif_logs}"
  find_logfile "fluidd.*" "${webif_logs}"
  find_logfile "KlipperScreen.log" "/tmp"
  find_logfile "webcamd\.log(\.[0-9]+)?$" "/var/log"

  ### draw interface
  local i=0
  top_border
  echo -e "|     ${yellow}~~~~~~~~~~~~~~~ [ Log Upload ] ~~~~~~~~~~~~~~${white}     |"
  hr
  echo -e "| You can choose the following logfiles for uploading:  |"
  blank_line

  for log in "${logfiles[@]}"; do
    log=${log//${HOME}/"~"}
    (( i < 10 )) && printf "|  ${i}) %-50s|\n" "${log}"
    (( i >= 10 )) && printf "| ${i}) %-50s|\n" "${log}"
    i=$(( i + 1 ))
  done

  blank_line
  back_footer

  local option re="^[0-9]+$"
  while true; do
    read -p "${cyan}###### Please select:${white} " option

    if [[ ${option} =~ ${re} && ${option} -lt ${#logfiles[@]} ]]; then
      upload_log "${logfiles[${option}]}"
      upload_selection
    elif [[ ${option} == "B" || ${option} == "b" ]]; then
      return
    else
      error_msg "Invalid command!"
    fi
  done
}

function upload_log() {
  local link
  clear && print_header
  status_msg "Uploading ${1} ..."
  link=$(curl -s -H "x-random;" --upload-file "${1}" 'http://paste.c-net.org/')

  if [[ -n ${link} ]]; then
    ok_msg "${1} upload successfull!"
    echo -e "\n${cyan}###### Here is your link:${white}"
    echo -e ">>>>>> ${link}\n"
  else
    error_msg "Uploading failed!"
  fi
}
