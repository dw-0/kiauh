#!/usr/bin/env bash
#
# KIAUH - Klipper Installation And Update Helper
# https://github.com/th33xitus/kiauh
#
# Copyright (C) 2020 - 2022 Dominik Willner <th33xitus@gmail.com>
#
# This file may be distributed under the terms of the GNU GPLv3 license

### global variables
SYSTEMD="/etc/systemd/system"
INITD="/etc/init.d"
ETCDEF="/etc/default"
KLIPPY_ENV="${HOME}/klippy-env"
KLIPPER_DIR="${HOME}/klipper"
KLIPPER_REPO="https://github.com/Klipper3d/klipper.git"

#=================================================#
#================ INSTALL KLIPPER ================#
#=================================================#

### check for existing klipper service installations
function check_klipper_exists() {
  local SERVICE_FILES
  local INITD_SF
  local SYSTEMD_SF

  INITD_SF=$(find "${INITD}" -regextype posix-extended -regex "${INITD}/klipper(-[^0])?[0-9]*")
  SYSTEMD_SF=$(find "${SYSTEMD}" -regextype posix-extended -regex "${SYSTEMD}/klipper(-[^0])?[0-9]*.service")

  if [ -n "${INITD_SF}" ]; then
    SERVICE_FILES+="${INITD_SF}"
  fi
  if [ -n "${SYSTEMD_SF}" ]; then
    SERVICE_FILES+=" ${SYSTEMD_SF}"
  fi

  if [ -n "${SERVICE_FILES}" ]; then
    ERROR_MSG="At least one Klipper service is already installed:"
    for service in $SERVICE_FILES; do
      ERROR_MSG="${ERROR_MSG}\n ➔ ${service}"
    done && return
  fi

  klipper_setup_dialog
}

function klipper_setup_dialog(){
  status_msg "Initializing Klipper installation ..."

  ### initial printer.cfg path check
  check_klipper_cfg_path

  ### ask for amount of instances to create
  top_border
  echo -e "| Please select the number of Klipper instances to set  |"
  echo -e "| up. The number of Klipper instances will determine    |"
  echo -e "| the amount of printers you can run from this machine. |"
  blank_line
  echo -e "| ${yellow}WARNING: There is no limit on the number of instances${default} |"
  echo -e "| ${yellow}you can set up with this script.${default}                      |"
  bottom_border

  local count
  while [[ ! ($count =~ ^[1-9]+((0)+)?$) ]]; do
    read -p "${cyan}###### Number of Klipper instances to set up:${default} " count
    if [[ ! ($count =~ ^[1-9]+((0)+)?$) ]]; then
      warn_msg "Invalid Input!\n"
    else
      echo
      read -p "${cyan}###### Install $count instance(s)? (Y/n):${default} " yn
      case "$yn" in
        Y|y|Yes|yes|"")
          echo -e "###### > Yes"
          status_msg "Installing $count Klipper instance(s) ..."
          klipper_setup "$count"
          break;;
        N|n|No|no)
          echo -e "###### > No"
          warn_msg "Exiting Klipper setup ...\n"
          break;;
        *)
          print_unkown_cmd
          print_msg && clear_msg;;
      esac
    fi
  done
}

function install_klipper_packages(){
  ### read PKGLIST from official install script
  status_msg "Reading dependencies..."
  install_script="${HOME}/klipper/scripts/install-octopi.sh"
  #PKGLIST=$(grep "PKGLIST=" $install_script | sed 's/PKGLIST//g; s/[$={}\n"]//g')
  PKGLIST=$(grep "PKGLIST=" "$install_script" | sed 's/PKGLIST//g; s/[$"{}=]//g; s/\s\s*/ /g' | tr -d '\n')
  ### add dbus requirement for DietPi distro
  [ -e "/boot/dietpi/.version" ] && PKGLIST+=" dbus"

  for pkg in $PKGLIST; do
    echo "${cyan}${pkg}${default}"
  done
  read -r -a PKGLIST <<< "$PKGLIST"

  ### Update system package info
  status_msg "Running apt-get update..."
  sudo apt-get update --allow-releaseinfo-change

  ### Install desired packages
  status_msg "Installing packages..."
  sudo apt-get install --yes "${PKGLIST[@]}"
}

function create_klipper_virtualenv(){
  status_msg "Installing python virtual environment..."
  # Create virtualenv if it doesn't already exist
  [ ! -d "${KLIPPY_ENV}" ] && virtualenv -p python2 "${KLIPPY_ENV}"
  # Install/update dependencies
  "${KLIPPY_ENV}"/bin/pip install -r "${KLIPPER_DIR}"/scripts/klippy-requirements.txt
}

function klipper_setup(){
  INSTANCE_COUNT=$1
  ### checking dependencies
  dep=(git)
  dependency_check

  ### step 1: clone klipper
  status_msg "Downloading Klipper ..."
  ### force remove existing klipper dir and clone into fresh klipper dir
  [ -d "${KLIPPER_DIR}" ] && rm -rf "${KLIPPER_DIR}"
  cd "${HOME}" && git clone "${KLIPPER_REPO}"
  status_msg "Download complete!"

  ### step 2: install klipper dependencies and create python virtualenv
  status_msg "Installing dependencies ..."
  install_klipper_packages
  create_klipper_virtualenv

  ### step 3: create shared gcode_files and logs folder
  [ ! -d "${HOME}/gcode_files" ] && mkdir -p "${HOME}/gcode_files"
  [ ! -d "${HOME}/klipper_logs" ] && mkdir -p "${HOME}/klipper_logs"

  ### step 4: create klipper instances
  create_klipper_service

  ### confirm message
  if [[ ${INSTANCE_COUNT} -eq 1 ]]; then
    CONFIRM_MSG="Klipper has been set up!"
  elif [[ ${INSTANCE_COUNT} -gt 1 ]]; then
    CONFIRM_MSG="${INSTANCE_COUNT} Klipper instances have been set up!"
  fi && print_msg && clear_msg
}

function create_klipper_service(){
  ### get config directory
  source_kiauh_ini

  ### set up default values
  SINGLE_INST=1
  CFG_PATH="$klipper_cfg_loc"
  KL_ENV=$KLIPPY_ENV
  KL_DIR=$KLIPPER_DIR
  KL_LOG="${HOME}/klipper_logs/klippy.log"
  KL_UDS="/tmp/klippy_uds"
  P_TMP="/tmp/printer"
  P_CFG="$CFG_PATH/printer.cfg"
  P_CFG_SRC="${SRCDIR}/kiauh/resources/printer.cfg"
  KL_SERV_SRC="${SRCDIR}/kiauh/resources/klipper.service"
  KL_SERV_TARGET="${SYSTEMD}/klipper.service"

  write_kl_service(){
    [ ! -d "$CFG_PATH" ] && mkdir -p "$CFG_PATH"
    ### create a minimal config if there is no printer.cfg
    [ ! -f "$P_CFG" ] && cp "$P_CFG_SRC" "$P_CFG"
    ### replace placeholder
    if [ ! -f $KL_SERV_TARGET ]; then
      status_msg "Creating Klipper Service $i ..."
        sudo cp "$KL_SERV_SRC" $KL_SERV_TARGET
        sudo sed -i "s|%INST%|$i|" $KL_SERV_TARGET
        sudo sed -i "s|%USER%|${USER}|" $KL_SERV_TARGET
        sudo sed -i "s|%KL_ENV%|$KL_ENV|" $KL_SERV_TARGET
        sudo sed -i "s|%KL_DIR%|$KL_DIR|" $KL_SERV_TARGET
        sudo sed -i "s|%KL_LOG%|$KL_LOG|" $KL_SERV_TARGET
        sudo sed -i "s|%P_CFG%|$P_CFG|" $KL_SERV_TARGET
        sudo sed -i "s|%P_TMP%|$P_TMP|" $KL_SERV_TARGET
        sudo sed -i "s|%KL_UDS%|$KL_UDS|" $KL_SERV_TARGET
    fi
  }

  if [[ $SINGLE_INST -eq $INSTANCE_COUNT ]]; then
    ### write single instance service
    write_kl_service
    ### enable instance
    sudo systemctl enable klipper.service
    ok_msg "Single Klipper instance created!"
    ### launching instance
    status_msg "Launching Klipper instance ..."
    sudo systemctl start klipper
  else
    i=1
    while [[ $i -le $INSTANCE_COUNT ]]; do
      ### rewrite default variables for multi instance cases
      CFG_PATH="$klipper_cfg_loc/printer_$i"
      KL_SERV_TARGET="${SYSTEMD}/klipper-$i.service"
      P_TMP="/tmp/printer-$i"
      P_CFG="$CFG_PATH/printer.cfg"
      KL_LOG="${HOME}/klipper_logs/klippy-$i.log"
      KL_UDS="/tmp/klippy_uds-$i"
      ### write multi instance service
      write_kl_service
      ### enable instance
      sudo systemctl enable klipper-$i.service
      ok_msg "Klipper instance #$i created!"
      ### launching instance
      status_msg "Launching Klipper instance #$i ..."
      sudo systemctl start klipper-$i

      ### raise values by 1
      i=$((i+1))
    done
    unset i
  fi
}

#================================================#
#================ REMOVE KLIPPER ================#
#================================================#

function remove_klipper(){
  shopt -s extglob # enable extended globbing
  ### ask the user if he wants to uninstall moonraker too.
  ###? currently usefull if the user wants to switch from single-instance to multi-instance
  FILE="${SYSTEMD}/moonraker?(-*([0-9])).service"
  if ls $FILE 2>/dev/null 1>&2; then
    while true; do
      unset REM_MR
      top_border
      echo -e "| Do you want to remove Moonraker afterwards?           |"
      echo -e "|                                                       |"
      echo -e "| This is useful in case you want to switch from a      |"
      echo -e "| single-instance to a multi-instance installation,     |"
      echo -e "| which makes a re-installation of Moonraker necessary. |"
      echo -e "|                                                       |"
      echo -e "| If for any other reason you only want to uninstall    |"
      echo -e "| Klipper, please select 'No' and continue.             |"
      bottom_border
      read -p "${cyan}###### Remove Moonraker afterwards? (y/N):${default} " yn
      case "$yn" in
        Y|y|Yes|yes)
          echo -e "###### > Yes"
          REM_MR="true"
          break;;
        N|n|No|no|"")
          echo -e "###### > No"
          REM_MR="false"
          break;;
        *)
          print_unkown_cmd
          print_msg && clear_msg;;
    esac
    done
  fi

  ### remove "legacy" klipper SysVinit service
  if [ -e "${INITD}/klipper" ]; then
    status_msg "Removing Klipper Service ..."
    sudo systemctl stop klipper
    sudo update-rc.d -f klipper remove
    sudo rm -f "${INITD}/klipper"
    sudo rm -f "${ETCDEF}/klipper"
    ok_msg "Klipper Service removed!"
  fi

  ### remove all klipper services
  FILE="${SYSTEMD}/klipper?(-*([0-9])).service"
  if ls "${FILE}" 2>/dev/null 1>&2; then
    status_msg "Removing Klipper Services ..."
    for service in $(ls "${FILE}" | cut -d"/" -f5)
    do
      status_msg "Removing ${service} ..."
      sudo systemctl stop "${service}"
      sudo systemctl disable "${service}"
      sudo rm -f "${SYSTEMD}/${service}"
      ok_msg "Done!"
    done
    ### reloading units
    sudo systemctl daemon-reload
    sudo systemctl reset-failed
    ok_msg "Klipper Service removed!"
  fi

  ### remove all logfiles
  FILE="${HOME}/klipper_logs/klippy?(-*([0-9])).log"
  if ls "${FILE}" 2>/dev/null 1>&2; then
    for log in $(ls "${FILE}"); do
      status_msg "Removing ${log} ..."
      rm -f "${log}"
      ok_msg "${log} removed!"
    done
  fi

  ### remove all UDS
  FILE="/tmp/klippy_uds?(-*([0-9]))"
  if ls "${FILE}" 2>/dev/null 1>&2; then
    for uds in $(ls "${FILE}"); do
      status_msg "Removing ${uds} ..."
      rm -f "${uds}"
      ok_msg "${uds} removed!"
    done
  fi

  ### remove all tmp-printer
  FILE="/tmp/printer?(-*([0-9]))"
  if ls "${FILE}" 2>/dev/null 1>&2; then
    for tmp_printer in $(ls "${FILE}"); do
      status_msg "Removing ${tmp_printer} ..."
      rm -f "${tmp_printer}"
      ok_msg "${tmp_printer} removed!"
    done
  fi

  ### removing klipper and klippy-env folders
  if [ -d "${KLIPPER_DIR}" ]; then
    status_msg "Removing Klipper directory ..."
    rm -rf "${KLIPPER_DIR}" && ok_msg "Directory removed!"
  fi
  if [ -d "${KLIPPY_ENV}" ]; then
    status_msg "Removing klippy-env directory ..."
    rm -rf "${KLIPPY_ENV}" && ok_msg "Directory removed!"
  fi

  CONFIRM_MSG=" Klipper was successfully removed!" && print_msg && clear_msg
  export CONFIRM_MSG

  shopt -u extglob # enable extended globbing

  if [ "${REM_MR}" == "true" ]; then
    remove_moonraker && unset REM_MR
  fi
}

#================================================#
#================ UPDATE KLIPPER ================#
#================================================#

function update_klipper(){
  do_action_service "stop" "klipper"
  if [ ! -d "${KLIPPER_DIR}" ]; then
    cd "${HOME}" && git clone "${KLIPPER_REPO}"
  else
    bb4u "klipper"
    read_branch
    save_klipper_state
    status_msg "Updating ${GET_BRANCH}"
    cd "${KLIPPER_DIR}"
    if [ "$DETACHED_HEAD" == "true" ]; then
      git checkout "${GET_BRANCH}"
      unset DETACHED_HEAD
    fi
    ### pull latest files from github
    git pull
    ### read PKGLIST and install possible new dependencies
    install_klipper_packages
    ### install possible new python dependencies
    KLIPPER_REQ_TXT="${KLIPPER_DIR}/scripts/klippy-requirements.txt"
    "${KLIPPY_ENV}"/bin/pip install -r "${KLIPPER_REQ_TXT}"
  fi
  update_log_paths "klipper"
  ok_msg "Update complete!"
  do_action_service "restart" "klipper"
}

#================================================#
#================ KLIPPER STATUS ================#
#================================================#

function klipper_status(){
  kcount=0
  klipper_data=(
    SERVICE
    "${KLIPPER_DIR}"
    "${KLIPPY_ENV_DIR}"
  )

  ### count amount of klipper service files in /etc/systemd/system
  SERVICE_FILE_COUNT=$(ls "${SYSTEMD}" | grep -E "^klipper(\-[[:digit:]]+)?\.service$" | wc -l)

  ### a fix to detect an existing "legacy" klipper init.d installation
  if [ -f "${INITD}/klipper" ]; then
    SERVICE_FILE_COUNT=1
  fi

  ### remove the "SERVICE" entry from the klipper_data array if a klipper service is installed
  [ $SERVICE_FILE_COUNT -gt 0 ] && unset klipper_data[0]

  ### count+1 for each found data-item from array
  for kd in "${klipper_data[@]}"
  do
    if [ -e "${kd}" ]; then
      kcount=$(expr ${kcount} + 1)
    fi
  done

  ### display status
  if [ "$kcount" == "${#klipper_data[*]}" ]; then
    KLIPPER_STATUS="$(printf "${green}Installed: %-5s${default}" ${SERVICE_FILE_COUNT})"
  elif [ "$kcount" == 0 ]; then
    KLIPPER_STATUS="${red}Not installed!${default}  "
  else
    KLIPPER_STATUS="${yellow}Incomplete!${default}     "
  fi
}

### reading the klipper branch the user is currently on
read_branch(){
  if [ -d "${KLIPPER_DIR}/.git" ]; then
    cd "${KLIPPER_DIR}"
    GET_BRANCH="$(git branch | grep "*" | cut -d"*" -f2 | cut -d" " -f2)"
    ### try to fix a detached HEAD state and read the correct branch from the output you get
    if [ "$(echo "${GET_BRANCH}" | grep "HEAD" )" ]; then
      DETACHED_HEAD="true"
      GET_BRANCH=$(git branch | grep "HEAD" | rev | cut -d" " -f1 | rev | cut -d")" -f1 | cut -d"/" -f2)
      ### try to identify the branch when the HEAD was detached at a single commit
      ### will only work if its either master, scurve-shaping or scurve-smoothing branch
      if [[ ${GET_BRANCH} =~ [[:alnum:]] ]]; then
        if [ "$(git branch -r --contains "${GET_BRANCH}" | grep "master")" ]; then
          GET_BRANCH="master"
        elif [ "$(git branch -r --contains "${GET_BRANCH}" | grep "scurve-shaping")" ]; then
          GET_BRANCH="scurve-shaping"
        elif [ "$(git branch -r --contains "${GET_BRANCH}" | grep "scurve-smoothing")" ]; then
          GET_BRANCH="scurve-smoothing"
        fi
      fi
    fi
  else
    GET_BRANCH=""
  fi
}

#prints the current klipper branch in the main menu
print_branch(){
  read_branch
  if [ -n "${GET_BRANCH}" ]; then
    PRINT_BRANCH="$(printf "%-16s" "${GET_BRANCH}")"
  else
    PRINT_BRANCH="${red}--------------${default}  "
  fi
}

read_local_klipper_commit(){
  if [ -d "${KLIPPER_DIR}" ] && [ -d "${KLIPPER_DIR}"/.git ]; then
    cd "${KLIPPER_DIR}"
    LOCAL_COMMIT=$(git describe HEAD --always --tags | cut -d "-" -f 1,2)
  else
    LOCAL_COMMIT="${NONE}"
  fi
}

read_remote_klipper_commit(){
  read_branch
  if [ -n "${GET_BRANCH}" ];then
    if [ "${GET_BRANCH}" = "origin/master" ] || [ "${GET_BRANCH}" = "master" ]; then
      git fetch origin -q
      REMOTE_COMMIT=$(git describe origin/master --always --tags | cut -d "-" -f 1,2)
    elif [ "${GET_BRANCH}" = "scurve-shaping" ]; then
      git fetch dmbutyugin scurve-shaping -q
      REMOTE_COMMIT=$(git describe dmbutyugin/scurve-shaping --always --tags | cut -d "-" -f 1,2)
    elif [ "${GET_BRANCH}" = "scurve-smoothing" ]; then
      git fetch dmbutyugin scurve-smoothing -q
      REMOTE_COMMIT=$(git describe dmbutyugin/scurve-smoothing --always --tags | cut -d "-" -f 1,2)
    fi
  else
    REMOTE_COMMIT="${NONE}"
  fi
}

compare_klipper_versions(){
  unset KLIPPER_UPDATE_AVAIL
  read_local_klipper_commit && read_remote_klipper_commit
  if [ "${LOCAL_COMMIT}" != "${REMOTE_COMMIT}" ]; then
    LOCAL_COMMIT="${yellow}$(printf "%-12s" "${LOCAL_COMMIT}")${default}"
    REMOTE_COMMIT="${green}$(printf "%-12s" "${REMOTE_COMMIT}")${default}"
    # add klipper to the update all array for the update all function in the updater
    KLIPPER_UPDATE_AVAIL="true" && update_arr+=(update_klipper)
  else
    LOCAL_COMMIT="${green}$(printf "%-12s" "${LOCAL_COMMIT}")${default}"
    REMOTE_COMMIT="${green}$(printf "%-12s" "${REMOTE_COMMIT}")${default}"
    KLIPPER_UPDATE_AVAIL="false"
  fi
  #if detached head was found, force the user with warn message to update klipper
  if [ "${DETACHED_HEAD}" == "true" ]; then
    LOCAL_COMMIT="${red}$(printf "%-12s" "Need update!")${default}"
  fi
}