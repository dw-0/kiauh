backup_ui(){
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~~~ [ Backup Menu ] ~~~~~~~~~~~~~~")     | "
  hr
  echo -e "|           ${yellow}Backup location: ~/kiauh-backups${default}            | "
  hr
  echo -e "|  Configuration folder:    |  Webinterface:            | "
  echo -e "|  0) [Klipper configs]     |  3) [Mainsail]            | "
  echo -e "|                           |  4) [Fluidd]              | "
  echo -e "|  Firmware:                |  5) [DWC2 Web UI]         | "
  echo -e "|  1) [Klipper]             |  6) [OctoPrint]           | "
  echo -e "|                           |                           | "
  echo -e "|  Klipper API:             |  HDMI Screen:             | "
  echo -e "|  2) [Moonraker]           |  7) [KlipperScreen]       | "
  quit_footer
}

backup_menu(){
  print_header
  print_msg && clear_msg
  backup_ui
  while true; do
    read -p "${cyan}Perform action:${default} " action; echo
    case "$action" in
      0)
        clear
        print_header
        backup_klipper_config_dir
        print_msg && clear_msg
        backup_ui;;
      1)
        clear
        print_header
        backup_klipper
        print_msg && clear_msg
        backup_ui;;
      2)
        clear
        print_header
        backup_moonraker
        print_msg && clear_msg
        backup_ui;;
      3)
        clear
        print_header
        backup_mainsail
        print_msg && clear_msg
        backup_ui;;
      4)
        clear
        print_header
        backup_fluidd
        print_msg && clear_msg
        backup_ui;;
      5)
        clear
        print_header
        backup_dwc2
        print_msg && clear_msg
        backup_ui;;
      6)
        clear
        print_header
        backup_octoprint
        print_msg && clear_msg
        backup_ui;;
      7)
        clear
        print_header
        backup_klipperscreen
        print_msg && clear_msg
        backup_ui;;
      Q|q)
        clear; main_menu; break;;
      *)
        clear
        print_header
        print_unkown_cmd
        print_msg && clear_msg
        backup_ui;;
    esac
  done
  backup_menu
}
