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

function init_flash_process() {
  ### step 1: check for required userhgroups (tty & dialout)
  check_usergroups

  top_border
  echo -e "|        ~~~~~~~~~~~~ [ Flash MCU ] ~~~~~~~~~~~~        |"
  hr
  echo -e "| Please select the flashing method to flash your MCU.  |"
  echo -e "| Make sure to only select a method your MCU supports.  |"
  echo -e "| Not all MCUs support both methods!                    |"
  hr
  blank_line
  echo -e "| 1) Regular flashing method                            |"
  echo -e "| 2) Updating via SD-Card Update                        |"
  blank_line
  back_help_footer

  local choice method
  while true; do
    read -p "${cyan}###### Please select:${white} " choice
    case "${choice}" in
      1)
        select_msg "Regular flashing method"
        method="regular"
        break;;
      2)
        select_msg "SD-Card Update"
        method="sdcard"
        break;;
      B|b)
        advanced_menu
        break;;
      H|h)
        clear && print_header
        show_flash_method_help
        break;;
      *)
        error_msg "Invalid command!";;
    esac
  done

  ### step 2: select how the mcu is connected to the host
  select_mcu_connection

  ### step 3: select which detected mcu should be flashed
  select_mcu_id "${method}"
}

#================================================#
#=================== STEP 2 =====================#
#================================================#
function select_mcu_connection() {
  top_border
  echo -e "| ${yellow}Make sure that the controller board is connected now!${white} |"
  hr
  blank_line
  echo -e "| How is the controller board connected to the host?    |"
  echo -e "| 1) USB                                                |"
  echo -e "| 2) UART                                               |"
  echo -e "| 3) USB (DFU mode)                                     |"
  blank_line
  back_help_footer

  local choice
  while true; do
    read -p "${cyan}###### Connection method:${white} " choice
    case "${choice}" in
      1)
        status_msg "Identifying MCU connected via USB ...\n"
        get_usb_id || true # continue even after exit code 1
        break;;
      2)
        status_msg "Identifying MCU possibly connected via UART ...\n"
        get_uart_id || true # continue even after exit code 1
        break;;
      3)
        status_msg "Identifying MCU connected via USB in DFU mode ...\n"
        get_dfu_id || true # continue even after exit code 1
        break;;
      B|b)
        advanced_menu
        break;;
      H|h)
        clear && print_header
        show_mcu_connection_help
        break;;
      *)
        error_msg "Invalid command!";;
    esac
  done
}

function print_detected_mcu_to_screen() {
  local i=1

  if (( ${#mcu_list[@]} < 1 )); then
    print_error "No MCU found!\n MCU either not connected or not detected!"
    return
  fi

  for mcu in "${mcu_list[@]}"; do
    mcu=$(echo "${mcu}" | rev | cut -d"/" -f1 | rev)
    echo -e " ● MCU #${i}: ${cyan}${mcu}${white}"
    i=$(( i + 1 ))
  done
  echo
}

#================================================#
#=================== STEP 3 =====================#
#================================================#
function select_mcu_id() {
  local i=0 sel_index=0 method=${1}

  if (( ${#mcu_list[@]} < 1 )); then
    print_error "No MCU found!\n MCU either not connected or not detected!"
    return
  fi

  top_border
  echo -e "|                   ${red}!!! ATTENTION !!!${white}                   |"
  hr
  echo -e "| Make sure, to select the correct MCU!                 |"
  echo -e "| ${red}ONLY flash a firmware created for the respective MCU!${white} |"
  bottom_border
  echo -e "${cyan}###### List of available MCU:${white}"

  ### list all mcus
  for mcu in "${mcu_list[@]}"; do
    i=$(( i + 1 ))
    mcu=$(echo "${mcu}" | rev | cut -d"/" -f1 | rev)
    echo -e " ● MCU #${i}: ${cyan}${mcu}${white}"
  done

  ### verify user input
  local regex="^[1-9]+$"
  while [[ ! ${sel_index} =~ ${regex} ]] || [[ ${sel_index} -gt ${i} ]]; do
    echo
    read -p "${cyan}###### Select MCU to flash:${white} " sel_index

    if [[ ! ${sel_index} =~ ${regex} ]]; then
      error_msg "Invalid input!"
    elif [[ ${sel_index} -lt 1 ]] || [[ ${sel_index} -gt ${i} ]]; then
      error_msg "Please select a number between 1 and ${i}!"
    fi

    local mcu_index=$(( sel_index - 1 ))
    local selected_mcu_id="${mcu_list[${mcu_index}]}"
  done

  ### confirm selection
  local yn
  while true; do
    echo -e "\n###### You selected:\n ● MCU #${sel_index}: ${selected_mcu_id}\n"
    read -p "${cyan}###### Continue? (Y/n):${white} " yn
    case "${yn}" in
      Y|y|Yes|yes|"")
        select_msg "Yes"
        status_msg "Flashing ${selected_mcu_id} ..."
        if [[ ${method} == "regular" ]]; then
          log_info "Flashing device '${selected_mcu_id}' with method '${method}'"
          start_flash_mcu "${selected_mcu_id}"
        elif [[ ${method} == "sdcard" ]]; then
          log_info "Flashing device '${selected_mcu_id}' with method '${method}'"
          start_flash_sd "${selected_mcu_id}"
        else
          print_error "No flash method set! Aborting..."
          log_error "No flash method set!"
          return
        fi
        break;;
      N|n|No|no)
        select_msg "No"
        break;;
      *)
        error_msg "Invalid command!";;
    esac
  done
}

function start_flash_mcu() {
  local device=${1}
  do_action_service "stop" "klipper"

  if make flash FLASH_DEVICE="${device}"; then
    ok_msg "Flashing successfull!"
  else
    warn_msg "Flashing failed!"
    warn_msg "Please read the console output above!"
  fi

  do_action_service "start" "klipper"
}

function start_flash_sd() {
  local i=0 board_list=() device=${1}
  local flash_script="${KLIPPER_DIR}/scripts/flash-sdcard.sh"

  ### write each supported board to the array to make it selectable
  for board in $("${flash_script}" -l | tail -n +2); do
    board_list+=("${board}")
  done

  top_border
  echo -e "|  Please select the type of board that corresponds to  |"
  echo -e "|  the currently selected MCU ID you chose before.      |"
  blank_line
  echo -e "|  The following boards are currently supported:        |"
  hr
  ### display all supported boards to the user
  for board in "${board_list[@]}"; do
    if [[ ${i} -lt 10 ]]; then
      printf "|  ${i}) %-50s|\n" "${board_list[${i}]}"
    else
      printf "|  ${i}) %-49s|\n" "${board_list[${i}]}"
    fi
    i=$(( i + 1 ))
  done
  quit_footer

  ### make the user select one of the boards
  local choice
  while true; do
    read -p "${cyan}###### Please select board type:${white} " choice
    if [[ ${choice} = "q" || ${choice} = "Q" ]]; then
      clear && advanced_menu && break
    elif [[ ${choice} -le ${#board_list[@]} ]]; then
      local selected_board="${board_list[${choice}]}"
      break
    else
      clear && print_header
      error_msg "Invalid choice!"
      flash_mcu_sd
    fi
  done

  while true; do
    echo
    top_border
    echo -e "| If your board is flashed with firmware that connects  |"
    echo -e "| at a custom baud rate, please change it now.          |"
    blank_line
    echo -e "| If you are unsure, stick to the default 250000!       |"
    bottom_border

    local baud_rate regex="^[0-9]+$"
    echo -e "${cyan}###### Please set the baud rate:${white} "
    while [[ ! ${baud_rate} =~ ${regex} ]]; do
      read -e -i "250000" -e baud_rate
      local selected_baud_rate=${baud_rate}
      break
    done
    break
  done

  ###flash process
  do_action_service "stop" "klipper"
  if "${flash_script}" -b "${selected_baud_rate}" "${device}" "${selected_board}"; then
    print_confirm "Flashing successfull!"
    log_info "Flash successfull!"
  else
    print_error "Flashing failed!\n Please read the console output above!"
    log_error "Flash failed!"
  fi
  do_action_service "start" "klipper"
}

function build_fw() {
  local python_version

  if [[ ! -d ${KLIPPER_DIR} || ! -d ${KLIPPY_ENV} ]]; then
    print_error "Klipper not found!\n Cannot build firmware without Klipper!"
    return
  fi

  python_version=$(get_klipper_python_ver)

  cd "${KLIPPER_DIR}"
  status_msg "Initializing firmware build ..."
  local dep=(build-essential dpkg-dev make)
  dependency_check "${dep[@]}"

  make clean

  status_msg "Building firmware ..."
  if (( python_version == 3 )); then
    make PYTHON=python3 menuconfig
    make PYTHON=python3
  elif (( python_version == 2 )); then
    make PYTHON=python2 menuconfig
    make PYTHON=python2
  else
    warn_msg "Error reading Python version!"
    return 1
  fi

  ok_msg "Firmware built!"
}

#================================================#
#=================== HELPERS ====================#
#================================================#

function get_usb_id() {
  unset mcu_list
  sleep 1
  mcus=$(find /dev/serial/by-id/* 2>/dev/null)

  for mcu in ${mcus}; do
    mcu_list+=("${mcu}")
  done
}

function get_uart_id() {
  unset mcu_list
  sleep 1
  mcus=$(find /dev -maxdepth 1 -regextype posix-extended -regex "^\/dev\/tty(AMA0|S0)$" 2>/dev/null)

  for mcu in ${mcus}; do
    mcu_list+=("${mcu}")
  done
}

function get_dfu_id() {
  unset mcu_list
  sleep 1
  mcus=$(lsusb | grep "DFU" | cut -d " " -f 6 2>/dev/null)

  for mcu in ${mcus}; do
    mcu_list+=("${mcu}")
  done
}

function show_flash_method_help() {
  top_border
  echo -e "|     ~~~~~~~~ < ? > Help: Flash MCU < ? > ~~~~~~~~     |"
  hr
  echo -e "| ${cyan}Regular flashing method:${white}                              |"
  echo -e "| The default method to flash controller boards which   |"
  echo -e "| are connected and updated over USB and not by placing |"
  echo -e "| a compiled firmware file onto an internal SD-Card.    |"
  blank_line
  echo -e "| Common controllers that get flashed that way are:     |"
  echo -e "| - Arduino Mega 2560                                   |"
  echo -e "| - Fysetc F6 / S6 (used without a Display + SD-Slot)   |"
  blank_line
  echo -e "| ${cyan}Updating via SD-Card Update:${white}                          |"
  echo -e "| Many popular controller boards ship with a bootloader |"
  echo -e "| capable of updating the firmware via SD-Card.         |"
  echo -e "| Choose this method if your controller board supports  |"
  echo -e "| this way of updating. This method ONLY works for up-  |"
  echo -e "| grading firmware. The initial flashing procedure must |"
  echo -e "| be done manually per the instructions that apply to   |"
  echo -e "| your controller board.                                |"
  blank_line
  echo -e "| Common controllers that can be flashed that way are:  |"
  echo -e "| - BigTreeTech SKR 1.3 / 1.4 (Turbo) / E3 / Mini E3    |"
  echo -e "| - Fysetc F6 / S6 (used with a Display + SD-Slot)      |"
  echo -e "| - Fysetc Spider                                       |"
  blank_line
  back_footer

  local choice
  while true; do
    read -p "${cyan}###### Please select:${white} " choice
    case "${choice}" in
      B|b)
        clear && print_header
        init_flash_process
        break;;
      *)
        error_msg "Invalid command!";;
    esac
  done
}

function show_mcu_connection_help() {
  top_border
  echo -e "|     ~~~~~~~~ < ? > Help: Flash MCU < ? > ~~~~~~~~     |"
  hr
  echo -e "| ${cyan}USB:${white}                                                  |"
  echo -e "| Selecting USB as the connection method will scan the  |"
  echo -e "| USB ports for connected controller boards. This will  |"
  echo -e "| be similar to the 'ls /dev/serial/by-id/*' command    |"
  echo -e "| suggested by the official Klipper documentation for   |"
  echo -e "| determining successfull USB connections!              |"
  blank_line
  echo -e "| ${cyan}UART:${white}                                                 |"
  echo -e "| Selecting UART as the connection method will list all |"
  echo -e "| possible UART serial ports. Note: This method ALWAYS  |"
  echo -e "| returns something as it seems impossible to determine |"
  echo -e "| if a valid Klipper controller board is connected or   |"
  echo -e "| not. Because of that, you ${red}MUST${white} know which UART serial |"
  echo -e "| port your controller board is connected to when using |"
  echo -e "| this connection method.                               |"
  blank_line
  back_footer

  local choice
  while true; do
    read -p "${cyan}###### Please select:${white} " choice
    case "${choice}" in
      B|b)
        clear && print_header
        select_mcu_connection
        break;;
      *)
        error_msg "Invalid command!";;
    esac
  done
}
