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

#=================================================#
#======== INSTALL GCODE_SHELL_COMMAND.PY =========#
#=================================================#

function setup_gcode_shell_command() {
  top_border
  echo -e "| You are about to install the 'G-Code Shell Command'   |"
  echo -e "| extension. Please make sure to read the instructions  |"
  echo -e "| before you continue and remember that potential risks |"
  echo -e "| can be involved after installing this extension!      |"
  blank_line
  echo -e "| ${red}You accept that you are doing this on your own risk!${white}  |"
  bottom_border

  local yn
  while true; do
    read -p "${cyan}###### Do you want to continue? (Y/n):${white} " yn
    case "${yn}" in
      Y|y|Yes|yes|"")
        select_msg "Yes"

        if [[ ! -d "${KLIPPER_DIR}/klippy/extras" ]]; then
          print_error "Folder ~/klipper/klippy/extras not found!\n      Klipper not installed yet?"
          return
        fi

        status_msg "Installing gcode shell command extension ..."

        if [[ ! -f "${KLIPPER_DIR}/klippy/extras/gcode_shell_command.py" ]]; then
          install_gcode_shell_command
        else
          echo; warn_msg "File 'gcode_shell_command.py' already exists in the destination location!"

          while true; do
            read -p "${cyan}###### Do you want to overwrite it? (Y/n):${white} " yn
            case "${yn}" in
              Y|y|Yes|yes|"")
                select_msg "Yes"
                rm -f "${KLIPPER_DIR}/klippy/extras/gcode_shell_command.py"
                install_gcode_shell_command
                break;;
              N|n|No|no)
                select_msg "No"
                break;;
              *)
                error_msg "Invalid Input!";;
            esac
          done
        fi
        return;;
      N|n|No|no)
        select_msg "No"
        return;;
      *)
        error_msg "Invalid Input!";;
    esac
  done
}

function install_gcode_shell_command() {
  do_action_service "stop" "klipper"
  status_msg "Copy 'gcode_shell_command.py' to '${KLIPPER_DIR}/klippy/extras' ..."

  if cp "${KIAUH_SRCDIR}/resources/gcode_shell_command.py" "${KLIPPER_DIR}/klippy/extras"; then
    ok_msg "Done!"
  else
    error_msg "Cannot copy file to target destination...Exiting!"
    return 1
  fi

  local yn
  while true; do
    echo
    read -p "${cyan}###### Create an example shell command? (Y/n):${white} " yn
    case "${yn}" in
      Y|y|Yes|yes|"")
        select_msg "Yes"
        create_example_shell_command
        break;;
      N|n|No|no)
        select_msg "No"
        break;;
    esac
  done

  do_action_service "restart" "klipper"
  print_confirm "Shell command extension installed!"
  return
}

function create_example_shell_command() {
  ### create a backup of the config folder
  backup_klipper_config_dir

  local configs regex path
  regex="${HOME//\//\\/}\/([A-Za-z0-9_]+)\/config\/printer\.cfg"
  configs=$(find "${HOME}" -maxdepth 3 -regextype posix-extended -regex "${regex}" | sort)

  for cfg in ${configs}; do
    path=$(echo "${cfg}" | rev | cut -d"/" -f2- | rev)

    if [[ ! -f "${path}/shell_command.cfg" ]]; then
      status_msg "Copy shell_command.cfg to ${path} ..."
      cp "${KIAUH_SRCDIR}/resources/shell_command.cfg" "${path}"
      ok_msg "${path}/shell_command.cfg created!"
      ### write include to the very first line of the printer.cfg
      sed -i "1 i [include shell_command.cfg]" "${cfg}"
    fi
  done
}