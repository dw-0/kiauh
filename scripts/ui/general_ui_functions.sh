#!/bin/bash
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
  echo -e "|                        ${red}Q) Quit${default}                        |"
  bottom_border
}

back_footer(){
  hr
  echo -e "|                       ${green}B) « Back${default}                       |"
  bottom_border
}

back_help_footer(){
  hr
  echo -e "|         ${green}B) « Back${default}         |        ${yellow}H) Help [?]${default}        |"
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
  $1
  print_msg && clear_msg
}

deny_action(){
  clear && print_header
  print_unkown_cmd
  print_msg && clear_msg
  $1
}


