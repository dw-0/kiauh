#!/usr/bin/env bash

#=======================================================================#
# Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>       #
#                                                                       #
# This file is part of KIAUH - Klipper Installation And Update Helper   #
# https://github.com/dw-0/kiauh                                         #
#                                                                       #
# This file may be distributed under the terms of the GNU GPLv3 license #
#=======================================================================#

set -e

#TODO (multi instance):
# if the klipper installer is started another time while other klipper
# instances are detected, ask if new instances should be added

#region Install Klipper
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

function print_dialog_user_select_klipper_instance() {
  local instance_names

  instance_names=$(get_multi_instance_names)
  instance_names_list=$(prefix_array_values_with_index instance_names[@])

  eval print_table \
    "\"Please select the Klipper instance to use:\"" \
    "\"${TABLE_SECTION_SEPARATOR}\"" \
    "${instance_names_list[@]}"
}

function list_klipper_instances() {
  local klipper_systemd_services
  local instance_names
  local services
  local instances

  instance_names=$(get_multi_instance_names)
  instances="Found the following Klipper instances:"

  for instance_name in ${instance_names}; do
    instances="${instances}\n ➔ ${instance_name}"
  done

  print_info "${instances}"

  klipper_systemd_services=$(klipper_systemd)
  services="Found the following Klipper services:"

  for service in ${klipper_systemd_services}; do
    services="${services}\n ➔ ${service}"
  done

  print_info "${services}"
}

function start_klipper_setup() {
  local klipper_systemd_services
  local python_version
  local instance_count

  local klipper_instance_names=()
  local klipper_instance_python_versions=()
  local klipper_instance_repos=()

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

  shopt -s nocasematch

  for ((i = 1; i <= instance_count; i++)); do
    local use_custom_klipper_instance_name
    local use_custom_klipper_repo

    print_dialog_user_select_python_version

    while true; do
      read -p "${cyan}###### Select Python version (3.x):${white} " -i "1" -e input

      case "${input}" in
        1 | "")
          select_msg "Python 3.x\n"
          python_version=3
          break
          ;;
        2)
          select_msg "Python 2.7\n"
          python_version=2
          break
          ;;
        B | b)
          clear
          install_menu
          break
          ;;
        *)
          error_msg "Invalid Input!\n"
          ;;
      esac
    done && input=""

    klipper_instance_python_versions+=("${python_version}")

    print_dialog_user_select_custom_name_bool
    use_custom_klipper_instance_name=$(get_user_confirmation "###### Assign custom Klipper instance name")

    if [[ ${use_custom_klipper_instance_name} == true ]]; then
      local instance_name_regex="^[0-9a-zA-Z]+$"
      local number_regex="^[0-9]+$"
      local blacklist="mcu"

      while [[ ! ${input} =~ ${instance_name_regex} || ${input} =~ ${blacklist} ]]; do
        read -p "${cyan}###### Name for instance #${i}:${white} " input

        if [[ ${input} =~ ${blacklist} ]]; then
          error_msg "Name not allowed! You are trying to use a reserved name."
        elif [[ ${input} =~ ${regex} && ! ${input} =~ ${blacklist} ]]; then
          select_msg "Name: ${input}\n"

          klipper_instance_names+=("$([[ ${input} =~ ${number_regex} ]] && echo "printer_${input}" || echo "${input}")")
        else
          error_msg "Invalid Input!\n"
        fi
      done && input=""
    else
      klipper_instance_names+=("printer_${i}")
    fi

    print_dialog_user_select_custom_repo_bool
    use_custom_klipper_repo=$(get_user_confirmation "###### Use custom Klipper repo")

    if [[ ${use_custom_klipper_repo} == true ]]; then
      local repo_file="${KIAUH_SRCDIR}/klipper_repos.txt"

      if [[ ! -f ${repo_file} ]]; then
        print_error "File not found:\n '${repo_file}'"
        return
      fi

      local repo
      local branch
      declare -A repos=()

      while IFS="," read -r repo branch; do
        repo=$(echo "${repo}" | sed -r "s/^http(s)?:\/\/github.com\///" | sed "s/\.git$//")

        if [[ -z "${repos[${repo}]}" ]]; then
          repos[${repo}]=""
        fi

        branch="${branch:-DEFAULT_KLIPPER_BRANCH}"

        if [[ ! "${repos[${repo}]}" == *"${branch}"* ]]; then
          if [[ -n "${repos[${repo}]}" ]]; then
            repos[${repo}]+=","
          fi

          repos[${repo}]+="${branch}"
        fi
      done < <(grep -E "^[^#]" "${repo_file}")

      local repos_list=()

      for repo in "${!repos[@]}"; do
        IFS=',' read -r -a branches <<< "${repos[repo]}"

        for branch in "${branches[@]}"; do
          repos_list+=("${repo}|${branch}")
        done
      done

      repos_list=$(prefix_array_values_with_index repos_list[@])

      eval print_table \
        "\"Please select the Klipper repo and branch to use:\"" \
        "\"${TABLE_SECTION_SEPARATOR}\"" \
        "${repos_list[@]}" \
        $(quit_footer) \
        57

      local number_regex="^[1-9]+$"

      while true; do
        read -p "${cyan}###### Select Klipper repo and branch:${white} " option

        if [[ ${option} =~ ${number_regex} && ${option} -le ${#repos_list[@]} ]]; then
          local selected_option="${repos_list[$((option - 1))]}"
          selected_option="${selected_option#*) }"
          klipper_instance_repos+=("${selected_option}")
        else
          error_msg "Invalid command!"
        fi
      done
    else
      klipper_instance_repos+=("${DEFAULT_KLIPPER_REPO}|${DEFAULT_KLIPPER_BRANCH}")
    fi
  done

  shopt -u nocasematch

  status_msg "Installing ${instance_count} Klipper instance$([[ ${instance_count} -gt 1 ]] && echo "s" || echo "")..."

  run_klipper_setup "${klipper_instance_python_versions[@]}" "${klipper_instance_names[@]}" "${klipper_instance_repos[@]}"
}

function print_dialog_user_select_python_version() {
  eval print_table \
    "\"Please select your preferred Python version.\"" \
    "\"The recommended version is Python 3.x.\"" \
    "\"${TABLE_SECTION_SEPARATOR}\"" \
    "\"  1) [Python 3.x]  (recommended)\"" \
    "\"  2) [Python 2.7]  ${yellow}(legacy)${white}\"" \
    $(back_footer_new)
}

function print_dialog_user_select_instance_count() {
  eval print_table \
    "\"Please select the number of Klipper instances to set up.\"" \
    "\"The number of Klipper instances will determine\"" \
    "\"the amount of printers you can run from this host.\"" \
    "\"${TABLE_SECTION_SEPARATOR}\"" \
    "\"${yellow}WARNING:${white}\"" \
    "\"${yellow}Setting up too many instances may crash your system.${white}\"" \
    $(back_footer_new)
}

function print_dialog_user_select_custom_name_bool() {
  eval print_table \
    "\"You can now assign a custom name to each instance.\"" \
    "\"If skipped, each instance will get an index assigned\"" \
    "\"in ascending order, starting at index '1'.\"" \
    "\"${TABLE_SECTION_SEPARATOR}\"" \
    "\"Info:\"" \
    "\"Only alphanumeric characters for names are allowed!\"" \
    $(back_footer_new)
}

function print_dialog_user_select_custom_repo_bool() {
  eval print_table \
    "\"You can now assign a custom Klipper repo to each instance.\"" \
    "\"If skipped, each instance will default to the main Klipper Github repo.\"" \
    "\"${TABLE_SECTION_SEPARATOR}\"" \
    "\"Info:\"" \
    "\"These custom repos need to be defined in ${KIAUH_SRCDIR}/klipper_repos.txt.\"" \
    $(back_footer_new)
}

function run_klipper_setup() {
  read_kiauh_ini "${FUNCNAME[0]}"

  local -n python_versions_ref=${1}
  local -n instance_names_ref=${2}
  local -n klipper_repos_ref=${3}

  local confirm
  local custom_repo
  local custom_branch
  local dep

  dep=(git)

  ### checking dependencies
  dependency_check "${dep[@]}"

  for ((i = 0; i < "${#klipper_repos_ref[@]}"; i++)); do
    local repo="${klipper_repos_ref[i]%%|*}"
    local branch="${klipper_repos_ref[i]##*|}"
    clone_klipper "${repo}" "${branch}"

    install_klipper_packages "${python_versions_ref[i]}" "${instance_names_ref[i]}"
    create_klipper_virtualenv "${python_version}" "${instance_names_ref[i]}"
    create_klipper_service "${instance_names_ref[i]}"

  done

  do_action_service "enable" "klipper"
  do_action_service "start" "klipper"

  check_usergroups

  confirm="${#instance_names_ref[@]} Klipper instance$([[ ${#instance_names_ref[@]} -gt 1 ]] && echo "s have" || echo " has") been set up!"

  set_multi_instance_names
  mask_disrupting_services

  print_confirm "${confirm}" && return
}

function clone_klipper() {
  local repo=${1}
  local branch=${2}
  local klipper_instance_name=${3}

  [[ -z ${repo} ]] && repo="${DEFAULT_KLIPPER_REPO}"

  repo=$(echo "${repo}" | sed -r "s/^(http|https):\/\/github\.com\///i; s/\.git$//")
  repo="https://github.com/${repo}"

  [[ -z ${branch} ]] && branch="${DEFAULT_KLIPPER_BRANCH}"

  local klipper_instance_dir="${KLIPPER_DIR}/${instance_name}"

  [[ -d "${klipper_instance_dir}" ]] && rm -rf "${klipper_instance_dir}"

  status_msg "Cloning Klipper from ${repo} ..."

  cd "${HOME}" || exit 1

  if git clone "${repo}" "${klipper_instance_dir}"; then
    cd "${klipper_instance_dir}" && git checkout "${branch}"
  else
    print_error "Cloning Klipper from\n ${repo}\n failed!"
    exit 1
  fi
}

function create_klipper_virtualenv() {
  local python_version="${1}"
  local klipper_instance_name="${2}"
  local virtual_python_environment_folder="${KLIPPY_ENV}/${klipper_instance_name:?}"

  # remove virtual Python environment if it exists
  [[ -d "${virtual_python_environment_folder}" ]] && rm -rf "${virtual_python_environment_folder}"

  status_msg "Installing $("python${python_version}" -V) virtual environment for Klipper instance \"${virtual_python_environment_folder}\"..."

  if virtualenv -p "python${python_version}" "${virtual_python_environment_folder}"; then
    ((python_version == 3)) && "${virtual_python_environment_folder}"/bin/pip install -U pip
    "${virtual_python_environment_folder}"/bin/pip install -r "${virtual_python_environment_folder}"/scripts/klippy-requirements.txt
  else
    log_error "failure while creating python3 klippy-env for Klipper instance ${klipper_instance_name}"
    error_msg "Creation of Klipper virtualenv for Klipper instance ${klipper_instance_name} failed!"
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
  local packages
  local log_name="Klipper"
  local python_version="${1}"
  local klipper_instance_name="${2}"
  local install_script="${KLIPPER_DIR}/${klipper_instance_name}/scripts/install-debian.sh"

  status_msg "Reading dependencies..."
  # shellcheck disable=SC2016
  packages=$(grep "PKGLIST=" "${install_script}" | cut -d'"' -f2 | sed 's/\${PKGLIST}//g' | tr -d '\n')
  ### add dfu-util for octopi-images
  packages+=" dfu-util"
  ### add dbus requirement for DietPi distro
  [[ -e "/boot/dietpi/.version" ]] && packages+=" dbus"

  if ((python_version == 3)); then
    ### replace python-dev with python3-dev if python3 was selected
    packages="${packages//python-dev/python3-dev}"
  elif ((python_version == 2)); then
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
  local gcodes_dir
  local cfg
  local log
  local klippy_serial
  local klippy_socket
  local env_file
  local service
  local service_template
  local env_template
  local suffix
  local klipper_dir="${KLIPPER_DIR}/${instance_name}"
  local klippy_env_dir="${KLIPPY_ENV}/${instance_name}"

  printer_data="${HOME}/${instance_name}_data"
  cfg_dir="${printer_data}/config"
  gcodes_dir="${printer_data}/gcodes"
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
    sudo sed -i "s|%USER%|${USER}|g; s|%KLIPPER_DIR%|${klipper_dir}|; s|%ENV%|${klippy_env_dir}|; s|%ENV_FILE%|${env_file}|" "${service}"
    sudo sed -i "s|%USER%|${USER}|; s|%KLIPPER_DIR%|${klipper_dir}|; s|%LOG%|${log}|; s|%CFG%|${cfg}|; s|%PRINTER%|${klippy_serial}|; s|%UDS%|${klippy_socket}|" "${env_file}"

    ok_msg "Klipper service file created!"
  fi

  if [[ ! -f ${cfg} ]]; then
    write_example_printer_cfg "${cfg}" "${gcodes_dir}"
  fi
}

function write_example_printer_cfg() {
  local cfg=${1}
  local gcodes_dir=${2}
  local cfg_template

  cfg_template="${KIAUH_SRCDIR}/resources/example.printer.cfg"

  status_msg "Creating minimal example printer.cfg ..."
  if cp "${cfg_template}" "${cfg}"; then
    sed -i "s|%GCODES_DIR%|${gcodes_dir}|" "${cfg}"
    ok_msg "Minimal example printer.cfg created!"
  else
    error_msg "Couldn't create minimal example printer.cfg!"
  fi
}
#endregion

#region Remove Klipper
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

  if ((${#files[@]} > 0)); then
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
#endregion

#region Update Klipper
###
# stops klipper, performs a git pull, installs
# possible new dependencies, then restarts klipper
#
function update_klipper() {
  read_kiauh_ini "${FUNCNAME[0]}"

  local klipper_instance_names
  local selected_klipper_instance_name
  local regex="^[1-9]+$"

  klipper_instance_names=$(get_multi_instance_names)

  print_dialog_user_select_klipper_instance

  while true; do
    read -p "${cyan}###### Select Klipper instance:${white} " -i "1" -e input

    if [[ "${input}" == "B" || "${input}" == "b" ]]; then
      clear
      update_menu
      break
    elif [[ ! ${input} =~ ${regex} ]]; then
      error_msg "Invalid input!"
    elif [[ ${input} -lt 1 ]] || [[ ${input} -gt ${i} ]]; then
      error_msg "Please select a number between 1 and ${i}!"
    fi

    selected_klipper_instance_name="${klipper_instance_names[$((input - 1))]}"
  done && input=""

  local klipper_instance_python_version
  local custom_repo="${custom_klipper_repo}"
  local custom_branch="${custom_klipper_repo_branch}"

  klipper_instance_python_version=$(get_klipper_python_version "${selected_klipper_instance_name}")

  do_action_service "stop" "klipper"

  if [[ ! -d ${KLIPPER_DIR} ]]; then
    clone_klipper "${custom_repo}" "${custom_branch}" "${selected_klipper_instance_name}"
  else
    backup_before_update "klipper"

    status_msg "Updating Klipper instance ${selected_klipper_instance_name} ..."

    cd "${KLIPPER_DIR}" && git pull
    install_klipper_packages "${klipper_instance_python_version}"
    "${KLIPPY_ENV}"/bin/pip install -r "${KLIPPER_DIR}/scripts/klippy-requirements.txt"
  fi

  ok_msg "Update complete!"
  do_action_service "restart" "klipper"
}
#endregion

#region Klipper Status
function get_klipper_status() {
  local klipper_instances
  local klipper_instance_python_versions=()
  local klipper_instance_status

  klipper_instances=$(klipper_systemd)

  if ((${#klipper_instances} > 0)); then
    for klipper_instance in "${klipper_instances[@]}"; do
      local klipper_instance_python_version

      klipper_instance_python_version=$(get_klipper_python_version "${klipper_instance}")

      if [[ "$(array_contains_value "${klipper_instance_python_version}" "${klipper_instance_python_versions[@]}")" == false ]]; then
        klipper_instance_python_versions+=("${klipper_instance_python_version}")
      fi
    done
  fi

  local data_arr=(SERVICE "${KLIPPER_DIR}" "${KLIPPY_ENV}")

  if ((${#klipper_instances} > 0)); then
    ### remove the "SERVICE" entry from the data array if a klipper service is installed
    unset "data_arr[0]"
  fi

  local file_count=0

  for data in "${data_arr[@]}"; do
    [[ -e ${data} ]] && file_count=$((file_count + 1))
  done

  if ((file_count == ${#data_arr[*]})); then
    klipper_instance_status="Installed: ${#klipper_instances} ("

    for ((i = 0; i < ${#klipper_instance_python_versions[@]}; i++)); do
      klipper_instance_status+="${klipper_instance_python_versions[${i}]}$([[ ${i} -lt $((${#klipper_instance_python_versions[@]} - 1)) ]] && echo ", " || echo "")"
    done
  elif ((file_count == 0)); then
    klipper_instance_status="Not installed!"
  else
    klipper_instance_status="Incomplete!"
  fi

  echo "${klipper_instance_status}"
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
#endregion

#region Helpers
function get_klippy_python_virtual_environment_folder() {
  local klipper_instance_name="${1}"

  echo "${KLIPPY_ENV}/${klipper_instance_name:?}"
}

###
# reads the python version from the klipper virtual environment
#
# @output: writes the python major version to STDOUT
#
function get_klipper_python_version() {
  local klipper_instance_name=${1}
  local klippy_python_virtual_environment_folder

  klippy_python_virtual_environment_folder=$(get_klippy_python_virtual_environment_folder "${klipper_instance_name}")

  [[ ! -d ${klippy_python_virtual_environment_folder} ]] && return

  local version
  version=$("${klippy_python_virtual_environment_folder}"/bin/python --version 2>&1 | cut -d" " -f2 | cut -d"." -f1)
  echo "${version}"
}

function mask_disrupting_services() {
  local brltty="false"
  local brltty_udev="false"
  local modem_manager="false"

  [[ $(dpkg -s brltty 2> /dev/null | grep "Status") = *\ installed ]] && brltty="true"
  [[ $(dpkg -s brltty-udev 2> /dev/null | grep "Status") = *\ installed ]] && brltty_udev="true"
  [[ $(dpkg -s ModemManager 2> /dev/null | grep "Status") = *\ installed ]] && modem_manager="true"

  status_msg "Installed brltty package detected, masking brltty service ..."

  if [[ ${brltty} == "true" ]]; then
    sudo systemctl stop brltty
    sudo systemctl mask brltty
  fi

  ok_msg "brltty service masked!"
  status_msg "Installed brltty-udev package detected, masking brltty-udev service ..."

  if [[ ${brltty_udev} == "true" ]]; then
    sudo systemctl stop brltty-udev
    sudo systemctl mask brltty-udev
  fi

  ok_msg "brltty-udev service masked!"
  status_msg "Installed ModemManager package detected, masking ModemManager service ..."

  if [[ ${modem_manager} == "true" ]]; then
    sudo systemctl stop ModemManager
    sudo systemctl mask ModemManager
  fi

  ok_msg "ModemManager service masked!"
}
#endregion
