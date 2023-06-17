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

#TODO (multi instance):
# if the klipper installer is started another time while other klipper
# instances are detected, ask if new instances should be added

#=================================================#
#================ INSTALL KLIPPER ================#
#=================================================#

###
# this function detects all installed klipper
# systemd instances and returns their absolute path
function klipper_systemd() {
  local services
  local blacklist
  local ignore
  local match

  ###
  # any service that uses "klipper" in its own name but isn't a full klipper service must be blacklisted using
  # this variable, otherwise they will be falsely recognized as klipper instances. E.g. "klipper-mcu.service"
  # is not a klipper service, but related to klippers linux mcu, which also requires its own service file, hence
  # it must be blacklisted.
  blacklist="mcu"

  ignore="${SYSTEMD}/klipper-(${blacklist}).service"
  match="${SYSTEMD}/klipper(-[0-9a-zA-Z]+)?.service"

  services=$(find "${SYSTEMD}" -maxdepth 1 -regextype awk ! -regex "${ignore}" -regex "${match}" | sort)
  echo "${services}"
}

function start_klipper_setup() {
  local klipper_systemd_services
  local python_version
  local instance_count
  local instance_names
  local use_custom_names
  local input
  local regex
  local blacklist
  local error

  status_msg "Initializing Klipper installation ...\n"

  ### return early if klipper already exists
  klipper_systemd_services=$(klipper_systemd)

  if [[ -n ${klipper_systemd_services} ]]; then
    error="At least one Klipper service is already installed:"

    for s in ${klipper_systemd_services}; do
      log_info "Found Klipper service: ${s}"
      error="${error}\n ➔ ${s}"
    done
  fi
  [[ -n ${error} ]] && print_error "${error}" && return

  ### user selection for python version
  print_dialog_user_select_python_version
  while true; do
    read -p "${cyan}###### Select Python version:${white} " -i "1" -e input
    case "${input}" in
      1)
        select_msg "Python 3.x\n"
        python_version=3
        break;;
      2)
        select_msg "Python 2.7\n"
        python_version=2
        break;;
      B|b)
        clear; install_menu; break;;
      *)
        error_msg "Invalid Input!\n";;
    esac
  done && input=""

  ### user selection for instance count
  print_dialog_user_select_instance_count
  regex="^[1-9][0-9]*$"
  while [[ ! ${input} =~ ${regex} ]]; do
    read -p "${cyan}###### Number of Klipper instances to set up:${white} " -i "1" -e input

    if [[ ${input} =~ ${regex} ]]; then
      instance_count="${input}"
      select_msg "Instance count: ${instance_count}\n"
      break
    elif [[ ${input} == "B" || ${input} == "b" ]]; then
      install_menu
    else
      error_msg "Invalid Input!\n"
    fi
  done && input=""

  ### user selection for custom names
  use_custom_names="false"
  if (( instance_count > 1 )); then
    print_dialog_user_select_custom_name_bool
    while true; do
      read -p "${cyan}###### Assign custom names? (y/N):${white} " input
      case "${input}" in
        Y|y|Yes|yes)
          select_msg "Yes\n"
          use_custom_names="true"
          break;;
        N|n|No|no|"")
          select_msg "No\n"
          break;;
        B|b)
          clear; install_menu; break;;
        *)
          error_msg "Invalid Input!\n";;
      esac
    done && input=""
  else
    instance_names+=("printer")
  fi

  ### user selection for setting the actual custom names
  shopt -s nocasematch
  if (( instance_count > 1 )) && [[ ${use_custom_names} == "true" ]]; then
    local i

    i=1
    regex="^[0-9a-zA-Z]+$"
    blacklist="mcu"
    while [[ ! ${input} =~ ${regex} || ${input} =~ ${blacklist} || ${i} -le ${instance_count} ]]; do
      read -p "${cyan}###### Name for instance #${i}:${white} " input

      if [[ ${input} =~ ${blacklist} ]]; then
        error_msg "Name not allowed! You are trying to use a reserved name."
      elif [[ ${input} =~ ${regex} && ! ${input} =~ ${blacklist} ]]; then
        select_msg "Name: ${input}\n"
        if [[ ${input} =~ ^[0-9]+$ ]]; then
          instance_names+=("printer_${input}")
        else
          instance_names+=("${input}")
        fi
        i=$(( i + 1 ))
      else
        error_msg "Invalid Input!\n"
      fi
    done && input=""
  elif (( instance_count > 1 )) && [[ ${use_custom_names} == "false" ]]; then
    for (( i=1; i <= instance_count; i++ )); do
      instance_names+=("printer_${i}")
    done
  fi
  shopt -u nocasematch

  (( instance_count > 1 )) && status_msg "Installing ${instance_count} Klipper instances ..."
  (( instance_count == 1 )) && status_msg "Installing single Klipper instance ..."

  run_klipper_setup "${python_version}" "${instance_names[@]}"
}

function print_dialog_user_select_python_version() {
  top_border
  echo -e "| Please select your preferred Python version.          | "
  echo -e "| The recommended version is Python 3.x.                | "
  hr
  echo -e "|  1) [Python 3.x]  (recommended)                       | "
  echo -e "|  2) [Python 2.7]  ${yellow}(legacy)${white}                            | "
  back_footer
}

function print_dialog_user_select_instance_count() {
  top_border
  echo -e "| Please select the number of Klipper instances to set  |"
  echo -e "| up. The number of Klipper instances will determine    |"
  echo -e "| the amount of printers you can run from this host.    |"
  blank_line
  echo -e "| ${yellow}WARNING:${white}                                              |"
  echo -e "| ${yellow}Setting up too many instances may crash your system.${white}  |"
  back_footer
}

function print_dialog_user_select_custom_name_bool() {
  top_border
  echo -e "| You can now assign a custom name to each instance.    |"
  echo -e "| If skipped, each instance will get an index assigned  |"
  echo -e "| in ascending order, starting at index '1'.            |"
  blank_line
  echo -e "| Info:                                                 |"
  echo -e "| Only alphanumeric characters for names are allowed!   |"
  back_footer
}

function run_klipper_setup() {
  read_kiauh_ini "${FUNCNAME[0]}"

  local python_version=${1}
  local instance_names
  local confirm
  local custom_repo
  local custom_branch
  local dep

  shift 1
  read -r -a instance_names <<< "${@}"

  custom_repo="${custom_klipper_repo}"
  custom_branch="${custom_klipper_repo_branch}"
  dep=(git)

  ### checking dependencies
  dependency_check "${dep[@]}"

  ### step 1: clone klipper
  clone_klipper "${custom_repo}" "${custom_branch}"

  ### step 2: install klipper dependencies and create python virtualenv
  install_klipper_packages "${python_version}"
  create_klipper_virtualenv "${python_version}"

  ### step 3: create klipper instances
  for instance in "${instance_names[@]}"; do
    create_klipper_service "${instance}"
  done

  ### step 4: enable and start all instances
  do_action_service "enable" "klipper"
  do_action_service "start" "klipper"

  ### step 5: check for dialout group membership
  check_usergroups

  ### confirm message
  (( ${#instance_names[@]} == 1 )) && confirm="Klipper has been set up!"
  (( ${#instance_names[@]} > 1 )) && confirm="${#instance_names[@]} Klipper instances have been set up!"

  ### finalizing the setup with writing instance names to the kiauh.ini
  set_multi_instance_names

  print_confirm "${confirm}" && return
}

function clone_klipper() {
  local repo=${1} branch=${2}

  [[ -z ${repo} ]] && repo="${KLIPPER_REPO}"
  repo=$(echo "${repo}" | sed -r "s/^(http|https):\/\/github\.com\///i; s/\.git$//")
  repo="https://github.com/${repo}"

  [[ -z ${branch} ]] && branch="master"

  ### force remove existing klipper dir and clone into fresh klipper dir
  [[ -d ${KLIPPER_DIR} ]] && rm -rf "${KLIPPER_DIR}"

  status_msg "Cloning Klipper from ${repo} ..."

  cd "${HOME}" || exit 1
  if git clone "${repo}" "${KLIPPER_DIR}"; then
    cd "${KLIPPER_DIR}" && git checkout "${branch}"
  else
    print_error "Cloning Klipper from\n ${repo}\n failed!"
    exit 1
  fi
}

function create_klipper_virtualenv() {
  local python_version="${1}"

  [[ -d ${KLIPPY_ENV} ]] && rm -rf "${KLIPPY_ENV}"

  status_msg "Installing $("python${python_version}" -V) virtual environment..."

  if virtualenv -p "python${python_version}" "${KLIPPY_ENV}"; then
    (( python_version == 3 )) && "${KLIPPY_ENV}"/bin/pip install -U pip
    "${KLIPPY_ENV}"/bin/pip install -r "${KLIPPER_DIR}"/scripts/klippy-requirements.txt
  else
    log_error "failure while creating python3 klippy-env"
    error_msg "Creation of Klipper virtualenv failed!"
    exit 1
  fi
}

###
# extracts the required packages from the
# install-debian.sh script and installs them
#
# @param {string}: python_version - klipper-env python version
#
function install_klipper_packages() {
  local packages log_name="Klipper" python_version="${1}"
  local install_script="${KLIPPER_DIR}/scripts/install-debian.sh"

  status_msg "Reading dependencies..."
  # shellcheck disable=SC2016
  packages=$(grep "PKGLIST=" "${install_script}" | cut -d'"' -f2 | sed 's/\${PKGLIST}//g' | tr -d '\n')
  ### add dfu-util for octopi-images
  packages+=" dfu-util"
  ### add dbus requirement for DietPi distro
  [[ -e "/boot/dietpi/.version" ]] && packages+=" dbus"

  if (( python_version == 3 )); then
    ### replace python-dev with python3-dev if python3 was selected
    packages="${packages//python-dev/python3-dev}"
  elif (( python_version == 2 )); then
    ### package name 'python-dev' is deprecated (-> no installation candidate) on more modern linux distros
    packages="${packages//python-dev/python2-dev}"
  else
    log_error "Internal Error: missing parameter 'python_version' during function call of ${FUNCNAME[0]}"
    error_msg "Internal Error: missing parameter 'python_version' during function call of ${FUNCNAME[0]}"
    exit 1
  fi

  echo "${cyan}${packages}${white}" | tr '[:space:]' '\n'
  read -r -a packages <<< "${packages}"

  ### Update system package lists if stale
  update_system_package_lists

  ### Install required packages
  install_system_packages "${log_name}" "packages[@]"
}

function create_klipper_service() {
  local instance_name=${1}

  local printer_data
  local cfg_dir
  local cfg
  local log
  local klippy_serial
  local klippy_socket
  local env_file
  local service
  local service_template
  local env_template
  local suffix

  printer_data="${HOME}/${instance_name}_data"
  cfg_dir="${printer_data}/config"
  cfg="${cfg_dir}/printer.cfg"
  log="${printer_data}/logs/klippy.log"
  klippy_serial="${printer_data}/comms/klippy.serial"
  klippy_socket="${printer_data}/comms/klippy.sock"
  env_file="${printer_data}/systemd/klipper.env"

  if [[ ${instance_name} == "printer" ]]; then
    suffix="${instance_name//printer/}"
  else
    suffix="-${instance_name//printer_/}"
  fi

  create_required_folders "${printer_data}"

  service_template="${KIAUH_SRCDIR}/resources/klipper.service"
  env_template="${KIAUH_SRCDIR}/resources/klipper.env"
  service="${SYSTEMD}/klipper${suffix}.service"

  if [[ ! -f ${service} ]]; then
    status_msg "Create Klipper service file ..."

    sudo cp "${service_template}" "${service}"
    sudo cp "${env_template}" "${env_file}"
    sudo sed -i "s|%USER%|${USER}|g; s|%KLIPPER_DIR%|${KLIPPER_DIR}|; s|%ENV%|${KLIPPY_ENV}|; s|%ENV_FILE%|${env_file}|" "${service}"
    sudo sed -i "s|%USER%|${USER}|; s|%KLIPPER_DIR%|${KLIPPER_DIR}|; s|%LOG%|${log}|; s|%CFG%|${cfg}|; s|%PRINTER%|${klippy_serial}|; s|%UDS%|${klippy_socket}|" "${env_file}"

    ok_msg "Klipper service file created!"
  fi

  if [[ ! -f ${cfg} ]]; then
    write_example_printer_cfg "${cfg}"
  fi
}

function write_example_printer_cfg() {
  local cfg=${1}
  local cfg_template

  cfg_template="${KIAUH_SRCDIR}/resources/example.printer.cfg"

  status_msg "Creating minimal example printer.cfg ..."
  if cp "${cfg_template}" "${cfg}"; then
    ok_msg "Minimal example printer.cfg created!"
  else
    error_msg "Couldn't create minimal example printer.cfg!"
  fi
}

#================================================#
#================ REMOVE KLIPPER ================#
#================================================#

function remove_klipper_service() {
  [[ -z $(klipper_systemd) ]] && return

  status_msg "Removing Klipper services ..."

  for service in $(klipper_systemd | cut -d"/" -f5); do
    status_msg "Removing ${service} ..."
    sudo systemctl stop "${service}"
    sudo systemctl disable "${service}"
    sudo rm -f "${SYSTEMD}/${service}"
    sudo systemctl daemon-reload
    sudo systemctl reset-failed
  done

  ok_msg "All Klipper services removed!"
}

function find_instance_files() {
  local target_folder=${1}
  local target_name=${2}
  local files

  readarray -t files < <(find "${HOME}" -regex "${HOME}/[A-Za-z0-9_]+_data/${target_folder}/${target_name}" | sort)

  echo -e "${files[@]}"
}

function find_legacy_klipper_logs() {
  local files
  local regex="klippy(-[0-9a-zA-Z]+)?\.log(.*)?"

  readarray -t files < <(find "${HOME}/klipper_logs" -maxdepth 1 -regextype posix-extended -regex "${HOME}/klipper_logs/${regex}" 2> /dev/null | sort)
  echo -e "${files[@]}"
}

function find_legacy_klipper_uds() {
  local files

  readarray -t files < <(find /tmp -maxdepth 1 -regextype posix-extended -regex "/tmp/klippy_uds(-[0-9a-zA-Z]+)?" | sort)
  echo -e "${files[@]}"
}

function find_legacy_klipper_printer() {
  local files

  readarray -t files < <(find /tmp -maxdepth 1 -regextype posix-extended -regex "/tmp/printer(-[0-9a-zA-Z]+)?" | sort)
  echo -e "${files[@]}"
}

function remove_klipper_dir() {
  [[ ! -d ${KLIPPER_DIR} ]] && return

  status_msg "Removing Klipper directory ..."
  rm -rf "${KLIPPER_DIR}"
  ok_msg "Directory removed!"
}

function remove_klipper_env() {
  [[ ! -d ${KLIPPY_ENV} ]] && return

  status_msg "Removing klippy-env directory ..."
  rm -rf "${KLIPPY_ENV}"
  ok_msg "Directory removed!"
}

###
# takes in a string of space separated absolute
# filepaths and removes those files one after another
#
function remove_files() {
  local files
  read -r -a files <<< "${@}"

  if (( ${#files[@]} > 0 )); then
    for file in "${files[@]}"; do
      status_msg "Removing ${file} ..."
      rm -f "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_klipper() {
  remove_klipper_service
  remove_files "$(find_instance_files "systemd" "klipper.env")"
  remove_files "$(find_instance_files "logs" "klippy.log.*")"
  remove_files "$(find_instance_files "comms" "klippy.sock")"
  remove_files "$(find_instance_files "comms" "klippy.serial")"

  remove_files "$(find_legacy_klipper_logs)"
  remove_files "$(find_legacy_klipper_uds)"
  remove_files "$(find_legacy_klipper_printer)"

  remove_klipper_dir
  remove_klipper_env

  print_confirm "Klipper was successfully removed!" && return
}

#================================================#
#================ UPDATE KLIPPER ================#
#================================================#

###
# stops klipper, performs a git pull, installs
# possible new dependencies, then restarts klipper
#
function update_klipper() {
  read_kiauh_ini "${FUNCNAME[0]}"

  local py_ver
  local custom_repo="${custom_klipper_repo}"
  local custom_branch="${custom_klipper_repo_branch}"

  py_ver=$(get_klipper_python_ver)

  do_action_service "stop" "klipper"

  if [[ ! -d ${KLIPPER_DIR} ]]; then
    clone_klipper "${custom_repo}" "${custom_branch}"
  else
    backup_before_update "klipper"

    status_msg "Updating Klipper ..."
    cd "${KLIPPER_DIR}" && git pull
    ### read PKGLIST and install possible new dependencies
    install_klipper_packages "${py_ver}"
    ### install possible new python dependencies
    "${KLIPPY_ENV}"/bin/pip install -r "${KLIPPER_DIR}/scripts/klippy-requirements.txt"
  fi

  ok_msg "Update complete!"
  do_action_service "restart" "klipper"
}

#================================================#
#================ KLIPPER STATUS ================#
#================================================#

function get_klipper_status() {
  local sf_count status py_ver
  sf_count="$(klipper_systemd | wc -w)"

  py_ver=$(get_klipper_python_ver)

  ### remove the "SERVICE" entry from the data array if a klipper service is installed
  local data_arr=(SERVICE "${KLIPPER_DIR}" "${KLIPPY_ENV}")
  (( sf_count > 0 )) && unset "data_arr[0]"

  ### count+1 for each found data-item from array
  local filecount=0
  for data in "${data_arr[@]}"; do
    [[ -e ${data} ]] && filecount=$(( filecount + 1 ))
  done

  if (( filecount == ${#data_arr[*]} )); then
    if (( py_ver == 3 )); then
      status="Installed: ${sf_count}(py${py_ver})"
    else
      status="Installed: ${sf_count}"
    fi
  elif (( filecount == 0 )); then
    status="Not installed!"
  else
    status="Incomplete!"
  fi

  echo "${status}"
}

function get_local_klipper_commit() {
  [[ ! -d ${KLIPPER_DIR} || ! -d "${KLIPPER_DIR}/.git" ]] && return

  local commit
  cd "${KLIPPER_DIR}"
  commit="$(git describe HEAD --always --tags | cut -d "-" -f 1,2)"
  echo "${commit}"
}

function get_remote_klipper_commit() {
  [[ ! -d ${KLIPPER_DIR} || ! -d "${KLIPPER_DIR}/.git" ]] && return

  local commit
  local branch

  read_kiauh_ini "${FUNCNAME[0]}"
  branch="${custom_klipper_repo_branch}"
  [[ -z ${branch} ]] && branch="master"

  cd "${KLIPPER_DIR}" && git fetch origin -q
  commit=$(git describe "origin/${branch}" --always --tags | cut -d "-" -f 1,2)
  echo "${commit}"
}

function compare_klipper_versions() {
  local versions local_ver remote_ver
  local_ver="$(get_local_klipper_commit)"
  remote_ver="$(get_remote_klipper_commit)"

  if [[ ${local_ver} != "${remote_ver}" ]]; then
    versions="${yellow}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    # add klipper to application_updates_available in kiauh.ini
    add_to_application_updates "klipper"
  else
    versions="${green}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
  fi

  echo "${versions}"
}

#================================================#
#=================== HELPERS ====================#
#================================================#

###
# reads the python version from the klipper virtual environment
#
# @output: writes the python major version to STDOUT
#
function get_klipper_python_ver() {
  [[ ! -d ${KLIPPY_ENV} ]] && return

  local version
  version=$("${KLIPPY_ENV}"/bin/python --version 2>&1 | cut -d" " -f2 | cut -d"." -f1)
  echo "${version}"
}
