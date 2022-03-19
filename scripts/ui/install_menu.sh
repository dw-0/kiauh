install_ui(){
  top_border
  echo -e "|     ${green}~~~~~~~~~~~ [ Installation Menu ] ~~~~~~~~~~~${default}     | "
  hr
  echo -e "|  You need this menu usually only for installing       | "
  echo -e "|  all necessary dependencies for the various           | "
  echo -e "|  functions on a completely fresh system.              | "
  hr
  echo -e "|  Firmware & API:          |  Other:                   | "
  echo -e "|  1) [Klipper]             |  6) [Duet Web Control]    | "
  echo -e "|  2) [Moonraker]           |  7) [OctoPrint]           | "
  echo -e "|                           |  8) [PrettyGCode]         | "
  echo -e "|  Klipper Webinterface:    |  9) [Telegram Bot]        | "
  echo -e "|  3) [Mainsail]            |                           | "
  echo -e "|  4) [Fluidd]              |  Webcam:                  | "
  echo -e "|                           |  10) [MJPG-Streamer]      | "
  echo -e "|  Touchscreen GUI:         |                           | "
  echo -e "|  5) [KlipperScreen]       |                           | "
  back_footer
}

install_menu(){
  do_action "" "install_ui"
  while true; do
    read -p "${cyan}Perform action:${default} " action; echo
    case "$action" in
      1)
        do_action "klipper_setup_dialog" "install_ui";;
      2)
        do_action "moonraker_setup_dialog" "install_ui";;
      3)
        do_action "install_webui mainsail" "install_ui";;
      4)
        do_action "install_webui fluidd" "install_ui";;
      5)
        do_action "install_klipperscreen" "install_ui";;
      6)
        do_action "dwc_setup_dialog" "install_ui";;
      7)
        do_action "octoprint_setup_dialog" "install_ui";;
      8)
        do_action "install_pgc_for_klipper" "install_ui";;
      9)
        do_action "install_MoonrakerTelegramBot" "install_ui";;
      10)
        do_action "install_mjpg-streamer" "install_ui";;
      B|b)
        clear; main_menu; break;;
      *)
        deny_action "install_ui";;
    esac
  done
  install_menu
}
