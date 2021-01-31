remove_ui(){
  top_border
  echo -e "|     ${red}~~~~~~~~~~~~~~ [ Remove Menu ] ~~~~~~~~~~~~~~${default}     | "
  hr
  echo -e "|  Directories which remain untouched:                  | "
  echo -e "|  --> Your printer configuration directory             | "
  echo -e "|  --> ~/kiauh-backups                                  | "
  echo -e "|  You need remove them manually if you wish so.        | "
  hr
  echo -e "|  Firmware:             |  Klipper Webinterface:       | "
  echo -e "|  1) [Klipper]          |  3) [Mainsail]               | "
  echo -e "|                        |  4) [Fluidd]                 | "
  echo -e "|  Klipper API:          |                              | "
  echo -e "|  2) [Moonraker]        |  HDMI Screen:                | "
  echo -e "|                        |  5) [KlipperScreen]          | "
  echo -e "|                        |                              | "
  echo -e "|                        |  Other:                      | "
  echo -e "|                        |  6) [Duet Web Control]       | "
  echo -e "|                        |  7) [OctoPrint]              | "
  echo -e "|                        |  8) [NGINX]                  | "
  quit_footer
}

remove_menu(){
  do_action "" "remove_ui"
  while true; do
    read -p "${cyan}Perform action:${default} " action; echo
    case "$action" in
      1)
        do_action "remove_klipper" "remove_ui";;
      2)
        do_action "remove_moonraker" "remove_ui";;
      3)
        do_action "remove_mainsail" "remove_ui";;
      4)
        do_action "remove_fluidd" "remove_ui";;
      5)
        do_action "remove_klipperscreen" "remove_ui";;
      6)
        do_action "remove_dwc2" "remove_ui";;
      7)
        do_action "remove_octoprint" "remove_ui";;
      8)
        do_action "remove_nginx" "remove_ui";;
      Q|q)
        clear; main_menu; break;;
      *)
        deny_action "remove_ui";;
    esac
  done
  remove_menu
}
