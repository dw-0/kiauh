backup_ui(){
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~~~ [ Backup Menu ] ~~~~~~~~~~~~~~")     | "
  hr
  echo -e "|           ${yellow}Backup location: ~/kiauh-backups${default}            | "
  hr
  echo -e "|  Configuration folder: |  Klipper Webinterface:       | "
  echo -e "|  0) [Klipper configs]  |  3) [Mainsail]               | "
  echo -e "|                        |  4) [Fluidd]                 | "
  echo -e "|  Firmware:             |                              | "
  echo -e "|  1) [Klipper]          |  HDMI Screen:                | "
  echo -e "|                        |  5) [KlipperScreen]          | "
  echo -e "|  Klipper API:          |                              | "
  echo -e "|  2) [Moonraker]        |  Other:                      | "
  echo -e "|                        |  6) [Duet Web Control]       | "
  echo -e "|                        |  7) [OctoPrint]              | "
  quit_footer
}

backup_menu(){
  do_action "" "backup_ui"
  while true; do
    read -p "${cyan}Perform action:${default} " action; echo
    case "$action" in
      0)
        do_action "backup_klipper_config_dir" "backup_ui";;
      1)
        do_action "backup_klipper" "backup_ui";;
      2)
        do_action "backup_moonraker" "backup_ui";;
      3)
        do_action "backup_mainsail" "backup_ui";;
      4)
        do_action "backup_fluidd" "backup_ui";;
      5)
        do_action "backup_klipperscreen" "backup_ui";;
      6)
        do_action "backup_dwc2" "backup_ui";;
      7)
        do_action "backup_octoprint" "backup_ui";;
      Q|q)
        clear; main_menu; break;;
      *)
        deny_action "backup_ui";;
    esac
  done
  backup_menu
}