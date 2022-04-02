#!/bin/bash

#=======================================================================#
# Copyright (C) 2020 - 2022 Dominik Willner <th33xitus@gmail.com>       #
#                                                                       #
# This file is part of KIAUH - Klipper Installation And Update Helper   #
# https://github.com/th33xitus/kiauh                                    #
#                                                                       #
# This file may be distributed under the terms of the GNU GPLv3 license #
#=======================================================================#

set -e

#ui total width = 57 chars
top_border(){
  echo -e "/=======================================================\\"
}

bottom_border(){
  echo -e "\=======================================================/"
}

blank_line(){
  echo -e "|                                                       |"
}

hr(){
  echo -e "|-------------------------------------------------------|"
}

quit_footer(){
  hr
  echo -e "|                        ${red}Q) Quit${white}                        |"
  bottom_border
}

back_footer(){
  hr
  echo -e "|                       ${green}B) « Back${white}                       |"
  bottom_border
}

back_help_footer(){
  hr
  echo -e "|         ${green}B) « Back${white}         |        ${yellow}H) Help [?]${white}        |"
  bottom_border
}

print_header(){
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~~~~~~ [ KIAUH ] ~~~~~~~~~~~~~~~~~")     |"
  echo -e "|     $(title_msg "   Klipper Installation And Update Helper    ")     |"
  echo -e "|     $(title_msg "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")     |"
  bottom_border
}

################################################################################
#******************************************************************************#
################################################################################
### TODO: rework other menus to make use of the following functions too and make them more readable

do_action(){
  clear && print_header
  ### $1 is the action the user wants to fire
  $1
#  print_msg && clear_msg
  ### $2 is the menu the user usually gets directed back to after an action is completed
  $2
}

deny_action(){
  clear && print_header
  print_error "Invalid command!"
  $1
}
