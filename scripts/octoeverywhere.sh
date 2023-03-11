#!/usr/bin/env bash

#=======================================================================#
# Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>       #
#                                                                       #
# This file is part of KIAUH - Klipper Installation And Update Helper   #
# https://github.com/th33xitus/kiauh                                    #
#                                                                       #
# This file may be distributed under the terms of the GNU GPLv3 license #
#=======================================================================#

#
# This file is written and maintained by Quinn Damerell from OctoEverywhere
# Please contact our support team if you need any help!
# https://octoeverywhere.com/support
#

set -e

#===================================================#
#==============         Install         ============#
#===================================================#

function octoeverywhere_systemd() {
  local services
  services=$(find "${SYSTEMD}" -maxdepth 1 -regextype posix-extended -regex "${SYSTEMD}/octoeverywhere(-[0-9a-zA-Z]+)?.service")
  echo "${services}"
}

function octoeverywhere_setup_dialog() {
  status_msg "Initializing OctoEverywhere for Klipper installation ..."

  # First, check for moonraker service instances.
  local moonraker_count
  local moonraker_names
  moonraker_count=$(moonraker_systemd | wc -w)
  if (( moonraker_count == 0 )); then
    ### return early if moonraker is not installed
    local error="Moonraker not installed! Please install Moonraker first!"
    log_error   "OctoEverywhere setup started without Moonraker being installed. Aborting setup."
    print_error "${error}" && return
  elif (( moonraker_count > 1 )); then
    # moonraker_names is valid only in case of multi-instance
    read -r -a moonraker_names <<< "$(get_multi_instance_names)"
  fi

  # Next, check for any existing OctoEverywhere services.
  local octoeverywhere_services
  local existing_octoeverywhere_count
  octoeverywhere_services=$(octoeverywhere_systemd)
  existing_octoeverywhere_count=$(echo "${octoeverywhere_services}" | wc -w )

  # We need to make the moonraker instance count to the OctoEverywhere service count.
  local allowed_octoeverywhere_count=$(( moonraker_count - existing_octoeverywhere_count ))
  if (( allowed_octoeverywhere_count > 0 )); then
    local new_octoeverywhere_count

    ### Step 1: Ask for the number of OctoEverywhere instances to install
    if (( moonraker_count == 1 )); then
      ok_msg "Moonraker installation found!\n"
      new_octoeverywhere_count=1
    elif (( moonraker_count > 1 )); then
      top_border
      printf "|${green}%-55s${white}|\n" " ${moonraker_count} Moonraker instances found!"
      for name in "${moonraker_names[@]}"; do
        printf "|${cyan}%-57s${white}|\n" " ● moonraker-${name}"
      done
      blank_line
      if (( existing_octoeverywhere_count > 0 )); then
        printf "|${green}%-55s${white}|\n" " ${existing_octoeverywhere_count} OctoEverywhere instances already installed!"
        for svc in ${octoeverywhere_services}; do
          printf "|${cyan}%-57s${white}|\n" " ● octoeverywhere-$(get_instance_name "${svc}")"
        done
      fi
      blank_line
      echo -e "| The setup will apply the same names to                |"
      echo -e "| OctoEverywhere                                        |"
      blank_line
      echo -e "| Please select the number of OctoEverywhere instances  |"
      echo -e "| to install. Usually one OctoEverywhere instance per   |"
      echo -e "| Moonraker instance is required, but you may not       |"
      echo -e "| install more OctoEverywhere instances than available  |"
      echo -e "| Moonraker instances.                                  |"
      bottom_border

      ### ask for amount of instances
      local re="^[1-9][0-9]*$"
      while [[ ! ${new_octoeverywhere_count} =~ ${re} || ${new_octoeverywhere_count} -gt ${allowed_octoeverywhere_count} ]]; do
        read -p "${cyan}###### Number of new OctoEverywhere instances to set up:${white} " -i "${allowed_octoeverywhere_count}" -e new_octoeverywhere_count
        ### break if input is valid
        [[ ${new_octoeverywhere_count} =~ ${re} && ${new_octoeverywhere_count} -le ${allowed_octoeverywhere_count} ]] && break
        ### conditional error messages
        [[ ! ${new_octoeverywhere_count} =~ ${re} ]] && error_msg "Input not a number"
        (( new_octoeverywhere_count > allowed_octoeverywhere_count )) && error_msg "Number of OctoEverywhere instances larger than installed Moonraker instances"
      done && select_msg "${new_octoeverywhere_count}"
    else
      log_error "Internal error. moonraker_count of '${moonraker_count}' not equal or grater than one!"
      return 1
    fi  # (( moonraker_count == 1 ))
  fi  # (( allowed_octoeverywhere_count > 0 ))

  # Special case for one moonraker instance with OctoEverywhere already installed.
  # If the user selects the install option again, they might be trying to recover the install
  # or complete a printer link they didn't finish in the past.
  # So in this case, we will allow them to run the install script again, since it's safe to run
  # if the service is already installed, it will repair any missing issues.
  if (( allowed_octoeverywhere_count == 0 && moonraker_count == 1 )); then
    local yn
    while true; do
      echo "${yellow}OctoEverywhere is already installed.${white}"
      echo "It is safe to run the install again to repair any issues or if the printer isn't linked, run the printer linking logic again."
      echo ""
      local question="Do you want to run the OctoEverywhere recovery or linking logic again?"
      read -p "${cyan}###### ${question} (Y/n):${white} " yn
      case "${yn}" in
        Y|y|Yes|yes|"")
          select_msg "Yes"
          break;;
        N|n|No|no)
          select_msg "No"
          abort_msg "Exiting OctoEverywhere setup ...\n"
          return;;
        *)
          error_msg "Invalid Input!";;
      esac
    done
    # The user responded yes, allow the install to run again.
    allowed_octoeverywhere_count=1
  fi

  # If there's something to install, do it!
  if (( allowed_octoeverywhere_count > 0 )); then

    (( new_octoeverywhere_count > 1 )) && status_msg "Installing ${new_octoeverywhere_count} OctoEverywhere instances ..."
    (( new_octoeverywhere_count == 1 )) && status_msg "Installing OctoEverywhere ..."

    # Ensure the basic system dependencies are installed.
    local dep=(git dfu-util virtualenv python3 python3-pip python3-venv)
    dependency_check "${dep[@]}"

    # Close the repo
    clone_octoeverywhere "${OCTOEVERYWHERE_REPO}"

    # Call install with the correct args.
    local instance_cfg_dirs
    read -r -a instance_cfg_dirs <<< "$(get_instance_folder_path "config")"
    echo instance_cfg_dirs[0]

    if (( moonraker_count == 1 )); then
      "${OCTOEVERYWHERE_DIR}/install.sh" "${instance_cfg_dirs[0]}/moonraker.conf"
    elif (( moonraker_count > 1 )); then
      local j=${existing_octoeverywhere_count}

      for (( i=1; i <= new_octoeverywhere_count; i++ )); do
        "${OCTOEVERYWHERE_DIR}/install.sh" "${instance_cfg_dirs[${j}]}/moonraker.conf"
        j=$(( j + 1 ))
      done && unset j
    fi # (( moonraker_count == 1 ))
  fi  # (( allowed_octoeverywhere_count > 0 ))
}

function clone_octoeverywhere() {
  local repo=${1}

  status_msg "Cloning OctoEverywhere..."
  ### force remove existing repos
  [[ -d "${OCTOEVERYWHERE_DIR}" ]] && rm -rf "${OCTOEVERYWHERE_DIR}"

  cd "${HOME}" || exit 1
  if ! git clone "${repo}" "${OCTOEVERYWHERE_DIR}"; then
    print_error "Cloning OctoEverywhere from\n ${repo}\n failed!"
    exit 1
  fi
}

function octoeverywhere_install() {
  "${OCTOEVERYWHERE_DIR}/install.sh" "$@"
}

#===================================================#
#=============        Remove          ==============#
#===================================================#

function remove_octoeverywhere_systemd() {
  [[ -z $(octoeverywhere_systemd) ]] && return
  status_msg "Removing OctoEverywhere Systemd Services ..."

  for service in $(octoeverywhere_systemd | cut -d"/" -f5); do
    status_msg "Removing ${service} ..."
    sudo systemctl stop "${service}"
    sudo systemctl disable "${service}"
    sudo rm -f "${SYSTEMD}/${service}"
    ok_msg "Done!"
  done

  ### reloading units
  sudo systemctl daemon-reload
  sudo systemctl reset-failed
  ok_msg "OctoEverywhere Services removed!"
}

function remove_octoeverywhere_logs() {
  local files regex="${HOME//\//\\/}\/([A-Za-z0-9_]+)\/logs\/octoeverywhere(-[0-9a-zA-Z]+)?\.log(.*)?"
  files=$(find "${HOME}" -maxdepth 3 -regextype posix-extended -regex "${regex}" | sort)

  if [[ -n ${files} ]]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -f "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_octoeverywhere_dir() {
  [[ ! -d ${OCTOEVERYWHERE_DIR} ]] && return

  status_msg "Removing OctoEverywhere directory ..."
  rm -rf "${OCTOEVERYWHERE_DIR}"
  ok_msg "Directory removed!"
}

function remove_octoeverywhere_config() {
  # Remove the system config but not the main config, so the printer id doesn't get lost.
  local files regex="${HOME//\//\\/}\/([A-Za-z0-9_]+)\/config\/octoeverywhere-system(-[0-9a-zA-Z]+)?\.cfg(.*)?"
  files=$(find "${HOME}" -maxdepth 4 -regextype posix-extended -regex "${regex}" | sort)

  if [[ -n ${files} ]]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -f "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_octoeverywhere_store_dir() {
  local files regex="${HOME//\//\\/}\/([A-Za-z0-9_]+)\/octoeverywhere-store"
  files=$(find "${HOME}" -maxdepth 2 -type d -regextype posix-extended -regex "${regex}" | sort)

  if [[ -n ${files} ]]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -rf "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_octoeverywhere_env() {
  [[ ! -d "${HOME}/octoeverywhere-env" ]] && return

  status_msg "Removing octoeverywhere-env directory ..."
  rm -rf "${HOME}/octoeverywhere-env"
  ok_msg "Directory removed!"
}

function remove_octoeverywhere()
{
  remove_octoeverywhere_systemd
  remove_octoeverywhere_logs
  remove_octoeverywhere_dir
  remove_octoeverywhere_env
  remove_octoeverywhere_config
  remove_octoeverywhere_store_dir

  print_confirm "OctoEverywhere was successfully removed!"
  return
}

#===================================================#
#=============        UPDATE          ==============#
#===================================================#

function update_octoeverywhere() {
  do_action_service "stop" "octoeverywhere"

  if [[ ! -d ${OCTOEVERYWHERE_DIR} ]]; then
    clone_octoeverywhere "${OCTOEVERYWHERE_REPO}"
  else
    backup_before_update "octoeverywhere"
    status_msg "Updating OctoEverywhere for Klipper ..."
    cd "${OCTOEVERYWHERE_DIR}" && git pull
    ### read PKGLIST and install possible new dependencies
    install_octoeverywhere_dependencies
    ### install possible new python dependencies
    "${OCTOEVERYWHERE_ENV}"/bin/pip install -r "${OCTOEVERYWHERE_DIR}/requirements.txt"
  fi

  ok_msg "Update complete!"
  do_action_service "restart" "octoeverywhere"
}

function clone_octoeverywhere() {
  local repo=${1}

  status_msg "Cloning OctoEverywhere from ${repo} ..."

  ### force remove existing octoeverywhere dir and clone into fresh octoeverywhere dir
  [[ -d ${OCTOEVERYWHERE_DIR} ]] && rm -rf "${OCTOEVERYWHERE_DIR}"

  cd "${HOME}" || exit 1
  if ! git clone "${OCTOEVERYWHERE_REPO}" "${OCTOEVERYWHERE_DIR}"; then
    print_error "Cloning OctoEverywhere from\n ${repo}\n failed!"
    exit 1
  fi
}

function install_octoeverywhere_dependencies() {
  local packages
  local install_script="${OCTOEVERYWHERE_DIR}/install.sh"

  ### read PKGLIST from official install-script
  status_msg "Reading dependencies..."
  # shellcheck disable=SC2016
  packages="$(grep "PKGLIST=" "${install_script}" | cut -d'"' -f2 | sed 's/\${PKGLIST}//g' | tr -d '\n')"

  echo "${cyan}${packages}${white}" | tr '[:space:]' '\n'
  read -r -a packages <<< "${packages}"

  ### Update system package info
  status_msg "Updating package lists..."
  if ! sudo apt-get update --allow-releaseinfo-change; then
    log_error "failure while updating package lists"
    error_msg "Updating package lists failed!"
    exit 1
  fi

  ### Install required packages
  status_msg "Installing required packages..."
  if ! sudo apt-get install --yes "${packages[@]}"; then
    log_error "failure while installing required octoeverywhere packages"
    error_msg "Installing required packages failed!"
    exit 1
  fi
}

#===================================================#
#=============        STATUS          ==============#
#===================================================#

function get_octoeverywhere_status() {
  local status
  local service_count
  local octoeverywhere_services

  octoeverywhere_services=$(octoeverywhere_systemd)
  service_count=$(echo "${octoeverywhere_services}" | wc -w )

  if (( service_count == 0 )); then
    status="Not installed!"
  elif [[ ! -d "${OCTOEVERYWHERE_DIR}" ]]; then
    status="Incomplete!"
  else
    status="Installed!"
  fi

  echo "${status}"
}

function get_local_octoeverywhere_commit() {
  [[ ! -d ${OCTOEVERYWHERE_DIR} || ! -d "${OCTOEVERYWHERE_DIR}/.git" ]] && return

  local commit
  cd "${OCTOEVERYWHERE_DIR}"
  commit="$(git describe HEAD --always --tags | cut -d "-" -f 1,2)"
  echo "${commit}"
}

function get_remote_octoeverywhere_commit() {
  [[ ! -d ${OCTOEVERYWHERE_DIR} || ! -d "${OCTOEVERYWHERE_DIR}/.git" ]] && return

  local commit
  cd "${OCTOEVERYWHERE_DIR}" && git fetch origin -q
  commit=$(git describe origin/master --always --tags | cut -d "-" -f 1,2)
  echo "${commit}"
}

function compare_octoeverywhere_versions() {
  local versions local_ver remote_ver
  local_ver="$(get_local_octoeverywhere_commit)"
  remote_ver="$(get_remote_octoeverywhere_commit)"

  if [[ ${local_ver} != "${remote_ver}" ]]; then
    versions="${yellow}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    # Add us to the update file, so if the user selects "update all" it includes us.
    add_to_application_updates "octoeverywhere"
  else
    versions="${green}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
  fi

  echo "${versions}"
}
