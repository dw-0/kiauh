update_ui(){
  ui_print_versions
  top_border
  echo -e "|     ${green}~~~~~~~~~~~~~~ [ Update Menu ] ~~~~~~~~~~~~~~${default}     | "
  hr
  echo -e "|  0) $BB4U_STATUS| "
  hr
  echo -e "|  a) [Update all]       |               |              | "
  echo -e "|                        |  Local Vers:  | Remote Vers: | "
  echo -e "|  Klipper/Klipper API:  |---------------|--------------| "
  echo -e "|  1) [Klipper]          |  $LOCAL_COMMIT | $REMOTE_COMMIT | "
  echo -e "|  2) [Moonraker]        |  $LOCAL_MOONRAKER_COMMIT | $REMOTE_MOONRAKER_COMMIT | "
  echo -e "|                        |               |              | "
  echo -e "|  Klipper Webinterface: |---------------|--------------| "
  echo -e "|  3) [Mainsail]         |  $MAINSAIL_LOCAL_VER | $MAINSAIL_REMOTE_VER | "
  echo -e "|  4) [Fluidd]           |  $FLUIDD_LOCAL_VER | $FLUIDD_REMOTE_VER | "
  echo -e "|                        |               |              | "
  echo -e "|  Touchscreen GUI:      |---------------|--------------| "
  echo -e "|  5) [KlipperScreen]    |  $LOCAL_KLIPPERSCREEN_COMMIT | $REMOTE_KLIPPERSCREEN_COMMIT | "
  echo -e "|                        |               |              | "
  echo -e "|  Other:                |---------------|--------------| "
  echo -e "|  6) [DWC2-for-Klipper] |  $LOCAL_DWC2FK_COMMIT | $REMOTE_DWC2FK_COMMIT | "
  echo -e "|  7) [DWC2 Web UI]      |  $DWC2_LOCAL_VER | $DWC2_REMOTE_VER | "
  echo -e "|  8) [PrettyGCode]      |  $LOCAL_PGC_COMMIT | $REMOTE_PGC_COMMIT | "
  echo -e "|  9) [Telegram Bot]     |  $LOCAL_MOONRAKER_TELEGRAM_BOT_COMMIT | $REMOTE_MOONRAKER_TELEGRAM_BOT_COMMIT | "
  echo -e "|                        |------------------------------| "
  echo -e "|  10) [System]          |  $DISPLAY_SYS_UPDATE   | "
  back_footer
}

update_menu(){
  read_bb4u_stat
  do_action "" "update_ui"
  while true; do
    read -p "${cyan}Perform action:${default} " action; echo
    case "$action" in
      0)
        do_action "toggle_backups" "update_ui";;
      1)
        do_action "update_klipper" "update_ui";;
      2)
        do_action "update_moonraker" "update_ui";;
      3)
        do_action "update_mainsail" "update_ui";;
      4)
        do_action "update_fluidd" "update_ui";;
      5)
        do_action "update_klipperscreen" "update_ui";;
      6)
        do_action "update_dwc2fk" "update_ui";;
      7)
        do_action "update_dwc2" "update_ui";;
      8)
        do_action "update_pgc_for_klipper" "update_ui";;
      9)
        do_action "update_MoonrakerTelegramBot" "update_ui";;
      10)
        do_action "update_system" "update_ui";;
      a)
        do_action "update_all" "update_ui";;
      B|b)
        clear; main_menu; break;;
      *)
        deny_action "update_ui";;
    esac
  done
  update_menu
}
