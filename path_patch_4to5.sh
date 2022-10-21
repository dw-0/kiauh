#!/usr/bin/env bash

#=======================================================================#
# Copyright (C) 2022 - 2022 Zack Mau <toufubomb@gmail.com>              #
#                                                                       #
# This file is part of KIAUH - Klipper Installation And Update Helper   #
# https://github.com/th33xitus/kiauh                                    #
#                                                                       #
# This file may be distributed under the terms of the GNU GPLv3 license #
#=======================================================================#
set -e
clear

### sourcing all additional scripts
KIAUH_SRCDIR="$(dirname -- "$(readlink -f "${BASH_SOURCE[0]}")")"
for script in "${KIAUH_SRCDIR}/scripts/"*.sh; do . "${script}"; done
for script in "${KIAUH_SRCDIR}/scripts/ui/"*.sh; do . "${script}"; done

function write_moonraker_service_force() {
  local i=${1} printer_data=${2} service=${3} env_file=${4}
  local service_template="${KIAUH_SRCDIR}/resources/moonraker.service"
  local env_template="${KIAUH_SRCDIR}/resources/moonraker.env"

  ### replace all placeholders
  status_msg "Creating Moonraker Service ${i} ..."
  sudo cp "${service_template}" "${service}"
  sudo cp "${env_template}" "${env_file}"

  [[ -z ${i} ]] && sudo sed -i "s| %INST%||" "${service}"
  [[ -n ${i} ]] && sudo sed -i "s|%INST%|${i}|" "${service}"
  sudo sed -i "s|%USER%|${USER}|g; s|%ENV%|${MOONRAKER_ENV}|; s|%ENV_FILE%|${env_file}|" "${service}"
  sudo sed -i "s|%USER%|${USER}|; s|%PRINTER_DATA%|${printer_data}|" "${env_file}"
}

function write_klipper_service_force() {
  local i=${1} cfg=${2} log=${3} printer=${4} uds=${5} service=${6} env_file=${7}
  local service_template="${KIAUH_SRCDIR}/resources/klipper.service"
  local env_template="${KIAUH_SRCDIR}/resources/klipper.env"

  ### replace all placeholders
  status_msg "Creating Klipper Service ${i} ..."
  sudo cp "${service_template}" "${service}"
  sudo cp "${env_template}" "${env_file}"
  [[ -z ${i} ]] && sudo sed -i "s| %INST%||" "${service}"
  [[ -n ${i} ]] && sudo sed -i "s|%INST%|${i}|" "${service}"
  sudo sed -i "s|%USER%|${USER}|g; s|%ENV%|${KLIPPY_ENV}|; s|%ENV_FILE%|${env_file}|" "${service}"
  sudo sed -i "s|%USER%|${USER}|; s|%LOG%|${log}|; s|%CFG%|${cfg}|; s|%PRINTER%|${printer}|; s|%UDS%|${uds}|" "${env_file}"
}

function path_patch() {
  local kcfg_dir=${1}

  local configs instance files regex data_dir data_dirs="" instance_code suffix
  local kl_instances=($(find "${SYSTEMD}" -maxdepth 1 -regextype posix-extended -regex "${SYSTEMD}/klipper(-[0-9a-zA-Z]+)?.service" | sort))
  # local mr_instances=($(find "${SYSTEMD}" -maxdepth 1 -regextype posix-extended -regex "${SYSTEMD}/moonraker(-[0-9a-zA-Z]+)?.service" | sort))
  local basic_folders=("backup" "certs" "database" "comms" "logs" "systemd")
  
  if [[ -z "${kcfg_dir}" ]]; then
    kcfg_dir="${HOME}/klipper_config"
  fi
  if [[ ! -d ${kcfg_dir} ]]; then
    error_msg "Source config folder \'${kcfg_dir}\' can not be found."
    return 1
  fi

  do_action_service "stop" "moonraker"
  do_action_service "stop" "klipper"

  if [[ "${#kl_instances[@]}" -eq 1 ]]; then
    configs="${kcfg_dir}"
  else
    configs=($(ls -d -- "${kcfg_dir}/printer_"*))
  fi
  configs=(${configs[@]// / })

  # build basic folders structure also get folder array
  for cfg in ${configs[@]}; do
    if [[ ${#configs[@]} -eq 1 ]]; then
      data_dir="${HOME}/printer_data"
    else
      data_dir="${HOME}/$(echo ${cfg}| rev| cut -d"/" -f1| rev)_data"
    fi
    data_dirs+="${data_dir} "
    
    mkdir -p "${data_dir}"
    [[ -d "${data_dir}/config" ]] && rm -rfd "${data_dir}/config"
    mv ${cfg} "${data_dir}/config" # moving configs
    for folder in "${basic_folders[@]}"; do
      [[ ! -d "${data_dir}/${folder}" ]] && mkdir -p "${data_dir}/${folder}"
    done

    [[ -d "${data_dir}/gcodes" ]] && rm -rfd "${data_dir}/gcodes"
    if [[ -d "${HOME}/gcode_files" ]]; then
      ln -s "${HOME}/gcode_files" "${data_dir}/gcodes"
    else
      mkdir -p "${data_dir}/gcodes"
    fi
  done

  data_dirs=(${data_dirs[@]// / })

  # moving, linking and updating data
  for i in ${!kl_instances[@]}; do
    data_dir=${data_dirs[i]}
    status_msg "${data_dir}"
    instance=${kl_instances[i]}
    instance_code=$(echo "${instance}" | sed "s/.*klipper//; s/\-//; s/\.service//")

    # handling moonraker database
    suffix=""
    if [[ ! -z ${instance_code} ]]; then suffix="_${instance_code}"; fi ## under dash type
    [[ -d "${HOME}/.moonraker_database${suffix}" ]] && rm -rfd "${data_dir}/database" && mv "${HOME}/.moonraker_database${suffix}" "${data_dir}/database" && \
    ok_msg "Restore moonraker database for $([[ -z ${instance_code} ]] && echo "main") instance $([[ ! -z ${instance_code} ]] && echo "${instance_code}")"
    ${MOONRAKER_ENV}/bin/python -mlmdb -e ${data_dir}/database/ edit --delete=validate_install

    if [[ ! -z ${instance_code} ]]; then suffix="-${instance_code}"; fi ## dash type
    # cleaning up klippy sock files
    [[ -f "/tmp/printer${suffix}" ]] && mv "/tmp/printer${suffix}" "${data_dir}/comms/klippy.serial"
    [[ -f "/tmp/klippy_uds${suffix}" ]] && mv "/tmp/klippy_uds${suffix}" "${data_dir}/comms/klippy.sock"
    # moving logs
    [[ -f "${HOME}/klipper_logs/klippy${suffix}.log" ]] && mv "${HOME}/klipper_logs/klippy${suffix}.log" "${data_dir}/logs/klippy.log"
    [[ -f "${HOME}/klipper_logs/moonraker${suffix}.log" ]] && mv "${HOME}/klipper_logs/moonraker${suffix}.log" "${data_dir}/logs/moonraker.log"

    # new service file configuring
    write_klipper_service_force "${instance_code}" \
                                "${data_dir}/config/printer.cfg" \
                               "${data_dir}/logs/klippy.log" \
                               "${data_dir}/comms/klippy.serial" \
                               "${data_dir}/comms/klippy.sock" \
                               "${SYSTEMD}/klipper${suffix}.service" \
                               "${data_dir}/systemd/klipper.env"
    write_moonraker_service_force "${instance_code}" \
                                  "${data_dir}" \
                                  "${SYSTEMD}/moonraker${suffix}.service" \
                                  "${data_dir}/systemd/moonraker.env"

    # update uds address to */klippy/comms/klippy.sock
    if [[ -f "${data_dir}/config/moonraker.conf" ]]; then
      cp "${data_dir}/config/moonraker.conf" "${data_dir}/config/moonraker.conf.kiup.bak"
      sed -i -r "/klippy_uds_address: / s|_address:.*$|_address: ${data_dir}/comms/klippy\.sock|" "${data_dir}/config/moonraker.conf"
    fi
  done

  [[ -d "${HOME}/klipper_logs" ]] && rm -rdf "${HOME}/klipper_logs"s
  symlink_webui_nginx_log "mainsail"
  symlink_webui_nginx_log "fluidd"
  sudo systemctl daemon-reload
  do_action_service "start" "moonraker"
  do_action_service "start" "klipper"
}

if [[ $# -gt 0 ]]; then
    set_globals
    path_patch "${1}"
else
    set_globals
    path_patch
fi
