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

#ui total width = 57 chars
function top_border() {
  echo -e "/=======================================================\\"
}

function bottom_border() {
  echo -e "\=======================================================/"
}

function blank_line() {
  echo -e "|                                                       |"
}

function hr() {
  echo -e "|-------------------------------------------------------|"
}

function quit_footer() {
  hr
  echo -e "|                        ${red}Q) Quit${white}                        |"
  bottom_border
}

function back_footer() {
  hr
  echo -e "|                       ${green}B) « Back${white}                       |"
  bottom_border
}

function back_help_footer() {
  hr
  echo -e "|         ${green}B) « Back${white}         |        ${yellow}H) Help [?]${white}        |"
  bottom_border
}

function print_header() {
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~~~~~~ [ KIAUH ] ~~~~~~~~~~~~~~~~~")     |"
  echo -e "|     $(title_msg "   Klipper Installation And Update Helper    ")     |"
  echo -e "|     $(title_msg "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")     |"
  bottom_border
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
