update_ui(){
  top_border
  echo -e "|     ${green}~~~~~~~~~~~~~~ [ Update Menu ] ~~~~~~~~~~~~~~${default}     | "
  hr
  echo -e "|  Check the following website for important software   | "
  echo -e "|  changes to the config file before updating Klipper:  | "
  echo -e "|                                                       | "
  echo -e "|  ${yellow}https://www.klipper3d.org/Config_Changes.html${default}        | "
  bottom_border
  top_border
  echo -e "|  0) $BB4U_STATUS| "
  hr
  echo -e "|  a) [Update all]       |  Local Vers:  | Remote Vers: | "
  echo -e "|                        |               |              | "
  echo -e "|  Firmware:             |               |              | "
  echo -e "|  1) [Klipper]          |  $LOCAL_COMMIT     | $REMOTE_COMMIT     | "
  echo -e "|                        |               |              | "
  echo -e "|  Webinterface:         |---------------|--------------| "
  echo -e "|  2) [DWC2-for-Klipper] |  $LOCAL_DWC2FK_COMMIT     | $REMOTE_DWC2FK_COMMIT     | "
  echo -e "|  3) [DWC2 Web UI]      |  $DWC2_LOCAL_VER | $DWC2_REMOTE_VER | "
  echo -e "|                        |---------------|--------------| "
  echo -e "|  4) [Moonraker]        |  $LOCAL_MOONRAKER_COMMIT     | $REMOTE_MOONRAKER_COMMIT     | "
  echo -e "|  5) [Mainsail]         |  $MAINSAIL_LOCAL_VER | $MAINSAIL_REMOTE_VER | "
  echo -e "|  6) [Fluidd]           |  $FLUIDD_LOCAL_VER | $FLUIDD_REMOTE_VER | "
  echo -e "|                        |               |              | "
  echo -e "|  HDMI Screen:          |---------------|--------------| "
  echo -e "|  7) [KlipperScreen]    |  $LOCAL_KLIPPERSCREEN_COMMIT | $REMOTE_KLIPPERSCREEN_COMMIT | "
  quit_footer
}

update_menu(){
  print_header
  #compare versions
    ui_print_versions
  print_msg && clear_msg
  read_bb4u_stat
  update_ui
  while true; do
    read -p "${cyan}Perform action:${default} " action; echo
    case "$action" in
      0)
        clear
        print_header
        toggle_backups
        print_msg && clear_msg
        update_ui;;
      1)
        clear
        print_header
        update_klipper && ui_print_versions
        print_msg && clear_msg
        update_ui;;
      2)
        clear
        print_header
        update_dwc2fk && ui_print_versions
        print_msg && clear_msg
        update_ui;;
      3)
        clear
        print_header
        update_dwc2 && ui_print_versions
        print_msg && clear_msg
        update_ui;;
      4)
        clear
        print_header
        update_moonraker && ui_print_versions
        print_msg && clear_msg
        update_ui;;
      5)
        clear
        print_header
        update_mainsail && ui_print_versions
        print_msg && clear_msg
        update_ui;;
      6)
        clear
        print_header
        update_fluidd && ui_print_versions
        print_msg && clear_msg
        update_ui;;
      7)
        clear
        print_header
        update_klipperscreen && ui_print_versions
        print_msg && clear_msg
        update_ui;;
      a)
        clear
        print_header
        update_all && ui_print_versions
        print_msg && clear_msg
        update_ui;;
      Q|q)
        clear; main_menu; break;;
      *)
        clear
        print_header
        print_unkown_cmd
        print_msg && clear_msg
        ui_print_versions
        update_ui;;
    esac
  done
  update_menu
}
