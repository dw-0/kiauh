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

DEFAULT_BOX_WIDTH=55

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
  local overall_width=${1:-${DEFAULT_BOX_WIDTH}}

  hr "${overall_width}"
  echo -e "|                        ${red}Q) Quit${white}                        |"
  bottom_border "${overall_width}"
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
    "$(title_msg "~~~~~~ [ KIAUH - Profezzional's Fork ] ~~~~~~")" \
    "$(title_msg "   Klipper Installation And Update Helper    ")" \
    "$(title_msg "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")"
}

function print_table() {
  local MIN_WIDTH=10

  ### An array of arrays of strings
  local sections=("$@")
  local overall_width
  local longest_string_length=0
  local console_width
  local border_color="${white}"

  # should work on both Unix and Windows (assuming you have `tput` or `stty` on Windows)
  console_width=$(tput cols 2> /dev/null || stty size 2> /dev/null | awk '{print $2}')

  # Calculate the longest string length, ignoring color codes
  for section in "${sections[@]}"; do
    for line in "${section[@]}"; do
      local line_length
      line_length=$(echo -e "${line}" | sed 's/\x1b\[[0-9;]*m//g' | wc -c)

      if ((line_length > longest_string_length)); then
        longest_string_length=${line_length}
      fi
    done
  done

  overall_width=$((longest_string_length + 4))

  # fit to console width
  if ((overall_width > console_width)); then
    overall_width=${console_width}
  fi

  # if console width is tiny, then just print it however its going to print, instead of trying to wrap a ton
  # or if content is tiny, make the table big enough to be noticeable
  if ((overall_width < MIN_WIDTH)); then
    overall_width=${MIN_WIDTH}
  fi

  # Print top border
  top_border "${overall_width}"

  for section in "${sections[@]}"; do
    for line in "${section[@]}"; do
      local line_length
      line_length=$(echo -e "${line}" | sed 's/\x1b\[[0-9;]*m//g' | wc -c)

      # wrap long lines to the next line
      if ((line_length + 4 > overall_width)); then
        local wrapped_text
        local color_code
        local wrapped_lines=()

        wrapped_text=$(echo -e "${line}" | sed 's/\x1b\[[0-9;]*m//g' | fold -sw $((overall_width - 4)))
        color_code=$(echo -e "${line}" | grep -oP '\x1b\[[0-9;]*m' | head -1)
        readarray -t wrapped_lines <<< "${wrapped_text}"

        for wrapped_line in "${wrapped_lines[@]}"; do
          echo -e "${border_color}| ${color_code}${wrapped_line}${white}$(repeat_string " " $((overall_width - ${#wrapped_line} - 4)))${border_color}|"
        done
      else
        echo -e "${border_color}| ${line}$(repeat_string " " $((overall_width - line_length - 4)))${border_color}|"
      fi
    done

    hr "${overall_width}"
  done

  bottom_border "${overall_width}"
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
