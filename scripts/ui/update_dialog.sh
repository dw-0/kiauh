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