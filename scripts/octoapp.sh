#!/usr/bin/env bash

#=======================================================================#
# Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>       #
#                                                                       #
# This file is part of KIAUH - Klipper Installation And Update Helper   #
# https://github.com/dw-0/kiauh                                         #
#                                                                       #
# This file may be distributed under the terms of the GNU GPLv3 license #
#=======================================================================#

#
# This file is written and maintained by Christian Würthner from OctoApp
# Please contact me if you need any help!
# hello@octoapp.eu
#

set -e

#===================================================#
#==============         Install         ============#
#===================================================#

function octoapp_systemd() {
  local services
  services=$(find "${SYSTEMD}" -maxdepth 1 -regextype posix-extended -regex "${SYSTEMD}/octoapp(-[0-9a-zA-Z]+)?.service")
  echo "${services}"
}

function octoapp_setup_dialog() {
  status_msg "Initializing OctoApp for Klipper installation ..."

  # First, check for moonraker service instances.
  local moonraker_count
  local moonraker_names
  moonraker_count=$(moonraker_systemd | wc -w)
  if (( moonraker_count == 0 )); then
    ### return early if moonraker is not installed
    local error="Moonraker not installed! Please install Moonraker first!"
    log_error   "OctoApp setup started without Moonraker being installed. Aborting setup."
    print_error "${error}" && return
  elif (( moonraker_count > 1 )); then
    # moonraker_names is valid only in case of multi-instance
    read -r -a moonraker_names <<< "$(get_multi_instance_names)"
  fi

  # Next, check for any existing OctoApp services.
  local octoapp_services
  local existing_octoapp_count
  octoapp_services=$(octoapp_systemd)
  existing_octoapp_count=$(echo "${octoapp_services}" | wc -w )

  # We need to make the moonraker instance count to the OctoApp service count.
  local allowed_octoapp_count=$(( moonraker_count - existing_octoapp_count ))
  if (( allowed_octoapp_count > 0 )); then
    local new_octoapp_count

    ### Step 1: Ask for the number of OctoApp instances to install
    if (( moonraker_count == 1 )); then
      ok_msg "Moonraker installation found!\n"
      new_octoapp_count=1
    elif (( moonraker_count > 1 )); then
      top_border
      printf "|${green}%-55s${white}|\n" " ${moonraker_count} Moonraker instances found!"
      for name in "${moonraker_names[@]}"; do
        printf "|${cyan}%-57s${white}|\n" " ● moonraker-${name}"
      done
      blank_line
      if (( existing_octoapp_count > 0 )); then
        printf "|${green}%-55s${white}|\n" " ${existing_octoapp_count} OctoApp instances already installed!"
        for svc in ${octoapp_services}; do
          printf "|${cyan}%-57s${white}|\n" " ● octoapp-$(get_instance_name "${svc}")"
        done
      fi
      blank_line
      echo -e "| The setup will apply the same names to OctoApp        |"
      blank_line
      echo -e "| Please select the number of OctoApp instances to      |"
      echo -e "| install. Usually one OctoApp instance per Moonraker   |"
      echo -e "| instance is required, but you may not install more    |"
      echo -e "| OctoApp instances than available Moonraker instances. |"
      bottom_border

      ### ask for amount of instances
      local re="^[1-9][0-9]*$"
      while [[ ! ${new_octoapp_count} =~ ${re} || ${new_octoapp_count} -gt ${allowed_octoapp_count} ]]; do
        read -p "${cyan}###### Number of new OctoApp instances to set up:${white} " -i "${allowed_octoapp_count}" -e new_octoapp_count
        ### break if input is valid
        [[ ${new_octoapp_count} =~ ${re} && ${new_octoapp_count} -le ${allowed_octoapp_count} ]] && break
        ### conditional error messages
        [[ ! ${new_octoapp_count} =~ ${re} ]] && error_msg "Input not a number"
        (( new_octoapp_count > allowed_octoapp_count )) && error_msg "Number of OctoApp instances larger than installed Moonraker instances"
      done && select_msg "${new_octoapp_count}"
    else
      log_error "Internal error. moonraker_count of '${moonraker_count}' not equal or grater than one!"
      return 1
    fi  # (( moonraker_count == 1 ))
  fi  # (( allowed_octoapp_count > 0 ))

  # Special case for one moonraker instance with OctoApp already installed.
  # If the user selects the install option again, they might be trying to recover the install
  # or complete a printer link they didn't finish in the past.
  # So in this case, we will allow them to run the install script again, since it's safe to run
  # if the service is already installed, it will repair any missing issues.
  if (( allowed_octoapp_count == 0 && moonraker_count == 1 )); then
    local yn
    while true; do
      echo "${yellow}OctoApp is already installed.${white}"
      echo "It is safe to run the install again to repair any issues or if the printer isn't linked, run the printer linking logic again."
      echo ""
      local question="Do you want to run the OctoApp recovery or linking logic again?"
      read -p "${cyan}###### ${question} (Y/n):${white} " yn
      case "${yn}" in
        Y|y|Yes|yes|"")
          select_msg "Yes"
          break;;
        N|n|No|no)
          select_msg "No"
          abort_msg "Exiting OctoApp setup ...\n"
          return;;
        *)
          error_msg "Invalid Input!";;
      esac
    done
    # The user responded yes, allow the install to run again.
    allowed_octoapp_count=1
  fi

  # If there's something to install, do it!
  if (( allowed_octoapp_count > 0 )); then

    (( new_octoapp_count > 1 )) && status_msg "Installing ${new_octoapp_count} OctoApp instances ..."
    (( new_octoapp_count == 1 )) && status_msg "Installing OctoApp ..."

    # Ensure the basic system dependencies are installed.
    local dep=(git dfu-util virtualenv python3 python3-pip python3-venv)
    dependency_check "${dep[@]}"

    # Close the repo
    clone_octoapp "${OCTOAPP_REPO}"

    # Call install with the correct args.
    local instance_cfg_dirs
    read -r -a instance_cfg_dirs <<< "$(get_instance_folder_path "config")"
    echo instance_cfg_dirs[0]

    if (( moonraker_count == 1 )); then
      "${OCTOAPP_DIR}/install.sh" "${instance_cfg_dirs[0]}/moonraker.conf"
    elif (( moonraker_count > 1 )); then
      local j=${existing_octoapp_count}

      for (( i=1; i <= new_octoapp_count; i++ )); do
        "${OCTOAPP_DIR}/install.sh" "${instance_cfg_dirs[${j}]}/moonraker.conf"
        j=$(( j + 1 ))
      done && unset j
    fi # (( moonraker_count == 1 ))
  fi  # (( allowed_octoapp_count > 0 ))
}

function octoapp_install() {
  "${OCTOAPP_DIR}/install.sh" "$@"
}

#===================================================#
#=============        Remove          ==============#
#===================================================#

function remove_octoapp_systemd() {
  [[ -z $(octoapp_systemd) ]] && return
  status_msg "Removing OctoApp Systemd Services ..."

  for service in $(octoapp_systemd | cut -d"/" -f5); do
    status_msg "Removing ${service} ..."
    sudo systemctl stop "${service}"
    sudo systemctl disable "${service}"
    sudo rm -f "${SYSTEMD}/${service}"
    ok_msg "Done!"
  done

  ### reloading units
  sudo systemctl daemon-reload
  sudo systemctl reset-failed
  ok_msg "OctoApp Services removed!"
}

function remove_octoapp_logs() {
  local files regex="${HOME//\//\\/}\/([A-Za-z0-9_]+)\/logs\/octoapp(-[0-9a-zA-Z]+)?\.log(.*)?"
  files=$(find "${HOME}" -maxdepth 3 -regextype posix-extended -regex "${regex}" | sort)

  if [[ -n ${files} ]]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -f "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_octoapp_dir() {
  [[ ! -d ${OCTOAPP_DIR} ]] && return

  status_msg "Removing OctoApp directory ..."
  rm -rf "${OCTOAPP_DIR}"
  ok_msg "Directory removed!"
}

function remove_octoapp_config() {
  # Remove the system config but not the main config, so the printer id doesn't get lost.
  local files regex="${HOME//\//\\/}\/([A-Za-z0-9_]+)\/config\/octoapp-system(-[0-9a-zA-Z]+)?\.cfg(.*)?"
  files=$(find "${HOME}" -maxdepth 4 -regextype posix-extended -regex "${regex}" | sort)

  if [[ -n ${files} ]]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -f "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_octoapp_store_dir() {
  local files regex="${HOME//\//\\/}\/([A-Za-z0-9_]+)\/octoapp-store"
  files=$(find "${HOME}" -maxdepth 2 -type d -regextype posix-extended -regex "${regex}" | sort)

  if [[ -n ${files} ]]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -rf "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_octoapp_env() {
  [[ ! -d "${HOME}/octoapp-env" ]] && return

  status_msg "Removing octoapp-env directory ..."
  rm -rf "${HOME}/octoapp-env"
  ok_msg "Directory removed!"
}

function remove_octoapp()
{
  remove_octoapp_systemd
  remove_octoapp_logs
  remove_octoapp_dir
  remove_octoapp_env
  remove_octoapp_config
  remove_octoapp_store_dir

  print_confirm "OctoApp was successfully removed!"
  return
}

#===================================================#
#=============        UPDATE          ==============#
#===================================================#

function update_octoapp() {
  do_action_service "stop" "octoapp"

  if [[ ! -d ${OCTOAPP_DIR} ]]; then
    clone_octoapp "${OCTOAPP_REPO}"
  else
    backup_before_update "octoapp"
    status_msg "Updating OctoApp for Klipper ..."
    cd "${OCTOAPP_DIR}" && git pull
    ### read PKGLIST and install possible new dependencies
    install_octoapp_dependencies
    ### install possible new python dependencies
    "${OCTOAPP_ENV}"/bin/pip install -r "${OCTOAPP_DIR}/requirements.txt"
  fi

  ok_msg "Update complete!"
  do_action_service "restart" "octoapp"
}

function clone_octoapp() {
  local repo=${1}

  status_msg "Cloning OctoApp from ${repo} ..."

  ### force remove existing octoapp dir and clone into fresh octoapp dir
  [[ -d ${OCTOAPP_DIR} ]] && rm -rf "${OCTOAPP_DIR}"

  cd "${HOME}" || exit 1
  if ! git clone "${OCTOAPP_REPO}" "${OCTOAPP_DIR}"; then
    print_error "Cloning OctoApp from\n ${repo}\n failed!"
    exit 1
  fi
}

function install_octoapp_dependencies() {
  local packages log_name="OctoApp"
  local install_script="${OCTOAPP_DIR}/install.sh"

  ### read PKGLIST from official install-script
  status_msg "Reading dependencies..."
  # shellcheck disable=SC2016
  packages="$(grep "PKGLIST=" "${install_script}" | cut -d'"' -f2 | sed 's/\${PKGLIST}//g' | tr -d '\n')"

  echo "${cyan}${packages}${white}" | tr '[:space:]' '\n'
  read -r -a packages <<< "${packages}"

  ### Update system package lists if stale
  update_system_package_lists

  ### Install required packages
  install_system_packages "${log_name}" "packages[@]"
}

#===================================================#
#=============        STATUS          ==============#
#===================================================#

function get_octoapp_status() {
  local status
  local service_count
  local octoapp_services

  octoapp_services=$(octoapp_systemd)
  service_count=$(echo "${octoapp_services}" | wc -w )

  if (( service_count == 0 )); then
    status="Not installed!"
  elif [[ ! -d "${OCTOAPP_DIR}" ]]; then
    status="Incomplete!"
  else
    status="Installed!"
  fi

  echo "${status}"
}

function get_local_octoapp_commit() {
  [[ ! -d ${OCTOAPP_DIR} || ! -d "${OCTOAPP_DIR}/.git" ]] && return

  local commit
  cd "${OCTOAPP_DIR}"
  commit="$(git describe HEAD --always --tags | cut -d "-" -f 1,2)"
  echo "${commit}"
}

function get_remote_octoapp_commit() {
  [[ ! -d ${OCTOAPP_DIR} || ! -d "${OCTOAPP_DIR}/.git" ]] && return

  local commit
  cd "${OCTOAPP_DIR}" && git fetch origin -q
  commit=$(git describe origin/release --always --tags | cut -d "-" -f 1,2)
  echo "${commit}"
}

function compare_octoapp_versions() {
  local versions local_ver remote_ver
  local_ver="$(get_local_octoapp_commit)"
  remote_ver="$(get_remote_octoapp_commit)"

  if [[ ${local_ver} != "${remote_ver}" ]]; then
    versions="${yellow}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    # Add us to the update file, so if the user selects "update all" it includes us.
    add_to_application_updates "octoapp"
  else
    versions="${green}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
  fi

  echo "${versions}"
}
