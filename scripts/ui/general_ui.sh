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

DEFAULT_BOX_WIDTH=57

function get_overall_width() {
  echo "${1:-${DEFAULT_BOX_WIDTH}}"
}

function box_border_line() {
  local start_char=${1}
  local middle_char=${2}
  local end_char=${3}
  local overall_width=${4}

  echo -e "${start_char}$(repeat_string "${middle_char}" "$(($(get_overall_width "${overall_width}") - 2))")${end_char}"
}

function top_border() {
  box_border_line "/" "=" "\\" "$1"
}

function bottom_border() {
  box_border_line "\\" "=" "/" "$1"
}

function blank_line() {
  box_border_line "|" " " "|" "$1"
}

function hr() {
  box_border_line "|" "-" "|" "$1"
}

function quit_footer() {
  # echo "${red}Q) Quit${white}"

  local footer=(
    "${TABLE_CENTERED_SECTION_SEPARATOR}"
    "${red}Q) Quit${white}"
  )

  # Use printf to prepare the array for eval
  printf "%q " "${footer[@]}"
}

function back_footer() {
  local overall_width=${1:-${DEFAULT_BOX_WIDTH}}

  hr "${overall_width}"
  echo -e "|                       ${green}B) « Back${white}                       |"
  bottom_border "${overall_width}"
}

function back_help_footer() {
  local overall_width=${1:-${DEFAULT_BOX_WIDTH}}

  hr "${overall_width}"
  echo -e "|         ${green}B) « Back${white}         |        ${yellow}H) Help [?]${white}        |"
  bottom_border "${overall_width}"
}

function print_header() {
  print_table \
    "${TABLE_CENTERED_SECTION_SEPARATOR}" \
    "$(title_msg "~~~~~~ [ KIAUH - Profezzional's Fork ] ~~~~~~")" \
    "$(title_msg "   Klipper Installation And Update Helper    ")" \
    "$(title_msg "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")" \
    "${1:-${TABLE_NO_WIDTH_ARG}}"
}

function get_string_without_colors() {
  echo -e "${1}" | sed 's/\x1b\[[0-9;]*m//g'
}

function print_table() {
  local last_arg="${!#}"
  local overall_width
  local lines
  local longest_string_length=0
  local console_width
  local center_lines=false
  local overall_width_was_specified

  overall_width_was_specified=$([[ "${last_arg}" =~ ^[0-9]+$ ]] && echo true || echo false)

  if [[ "${overall_width_was_specified}" == true ]]; then
    overall_width="${last_arg}" # if last arg is an integer
    lines=("${@:1:$#-1}")       # all arguments except the last one
  elif [[ "${last_arg}" == "${TABLE_NO_WIDTH_ARG}" ]]; then
    overall_width=${DEFAULT_BOX_WIDTH}
    lines=("${@:1:$#-1}") # all but last arg
  else
    lines=("$@")
    overall_width=${DEFAULT_BOX_WIDTH}
  fi

  for line in "${lines[@]}"; do
    local line_length_without_colors
    local line_without_colors

    line_without_colors=$(get_string_without_colors "${line}")
    line_length_without_colors="${#line_without_colors}"

    if ((line_length_without_colors > longest_string_length)); then
      longest_string_length="${line_length_without_colors}"
    fi
  done

  if [[ "${overall_width_was_specified}" == false && "${overall_width}" -lt $((longest_string_length + 4)) ]]; then
    overall_width=$((longest_string_length + 4))
  fi

  console_width=$(tput cols 2> /dev/null || stty size 2> /dev/null | awk '{print $2}')

  if ((overall_width > console_width)); then
    overall_width=$((console_width))
  fi

  # if console width is tiny, then just print it however its going to print, instead of trying to wrap a ton
  # or if content is tiny, make the table big enough to be noticeable
  if ((overall_width < MIN_WIDTH)); then
    overall_width=${MIN_WIDTH}
  fi

  top_border "${overall_width}"

  local line_count=${#lines[@]}

  for ((i = 0; i < line_count; i++)); do
    local line="${lines[${i}]}"
    local line_is_section_separator
    local line_is_centered_section_separator

    line_is_section_separator=$([[ "${line}" == "${TABLE_SECTION_SEPARATOR}" ]] && echo true || echo false)
    line_is_centered_section_separator=$([[ "${line}" == "${TABLE_CENTERED_SECTION_SEPARATOR}" ]] && echo true || echo false)

    if [[ "${line_is_section_separator}" == true || "${line_is_centered_section_separator}" == true ]]; then
      center_lines=${line_is_centered_section_separator}

      if ((i > 0)); then
        hr "${overall_width}"
      fi

      continue
    fi

    local line_length_without_colors
    local line_without_colors

    line_without_colors=$(get_string_without_colors "${line}")
    line_length_without_colors="${#line_without_colors}"

    # wrap long lines to the next line, keeping text colors
    if ((line_length_without_colors + 4 > overall_width)); then
      local wrapped_text_without_colors
      local color_code
      local wrapped_lines=()

      wrapped_text_without_colors=$(get_string_without_colors "${line}" | fold -sw $((overall_width - 4)))
      color_code=$(echo -e "${line}" | grep -oP '\x1b\[[0-9;]*m' | head -1)

      readarray -t wrapped_lines <<< "${wrapped_text_without_colors}"

      for wrapped_line in "${wrapped_lines[@]}"; do
        get_table_line_with_padding "${center_lines}" "${#wrapped_line}" "${color_code}${wrapped_line}"
      done
    else
      get_table_line_with_padding "${center_lines}" "${line_length_without_colors}" "${line}"
    fi
  done

  bottom_border "${overall_width}"
}

function get_table_line_with_padding() {
  local center_lines=${1}
  local line_length=${2}
  local line=${3}

  local left_padding_length
  local right_padding_length
  local left_padding
  local right_padding

  left_padding_length=$([[ "${center_lines}" == true ]] && echo $(((overall_width - line_length - 4) / 2)) || echo 0)
  right_padding_length=$((overall_width - line_length - 4 - left_padding_length))

  left_padding=$(repeat_string " " "${left_padding_length}")
  right_padding=$(repeat_string " " "${right_padding_length}")

  echo -e "${BORDER_COLOR}| ${left_padding}${line}${right_padding} ${BORDER_COLOR}|"
}

function do_action() {
  clear && print_header
  ### $1 is the action the user wants to fire
  $1
  #  print_msg && clear_msg
  ### $2 is the menu the user usually gets directed back to after an action is completed
  $2
}

function deny_action() {
  clear && print_header
  print_error "Invalid command!"
  $1
}
