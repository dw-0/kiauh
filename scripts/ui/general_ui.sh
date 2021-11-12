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
  ### $1 is the action the user wants to fire
  $1
  print_msg && clear_msg
  ### $2 is the menu the user usually gets directed back to after an action is completed
  $2
}

deny_action(){
  clear && print_header
  print_unkown_cmd
  print_msg && clear_msg
  $1
}

#######################################
# description Advise user to update KIAUH
# Globals:
#   KIAUH_WHIPTAIL_NORMAL_HEIGHT
#   KIAUH_WHIPTAIL_NORMAL_WIDTH
#   RET
# Arguments:
#  None
#######################################
kiauh_update_dialog() {
  whiptail --title "New KIAUH update available!" \
    --yesno \
    "View Changelog: https://git.io/JnmlX

It is recommended to keep KIAUH up to date. Updates usually contain bugfixes, \
important changes or new features. Please consider updating!

Do you want to update now?" \
    "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH"

  local out=$?
  if [ $out -eq 0 ]; then
    do_action "update_kiauh"
  else
    deny_action "kiauh_update_dialog"
  fi
}
