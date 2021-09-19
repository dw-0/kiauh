settings_ui(){
  source_kiauh_ini
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~ [ KIAUH Settings ] ~~~~~~~~~~~~~")     | "
  hr
  echo -e "| ${red}Caution:${default}                                              | "
  echo -e "| When you change the config folder, be aware that ALL  | "
  echo -e "| Klipper and Moonraker services will be STOPPED,       | "
  echo -e "| reconfigured and then restarted again.                | "
  blank_line
  echo -e "| ${red}DO NOT change the folder during printing!${default}             | "
  hr
  blank_line
  echo -e "|  ${cyan}● Current Klipper config folder:${default}                     | "
  printf "|%-55s|\n" "    $klipper_cfg_loc"
  blank_line
  hr
  if [ -z $klipper_cfg_loc ]; then
  echo -e "|  ${red}N/A) Install Klipper with KIAUH first to unlock!${default}     | "
  else
  echo -e "|  1) Change config folder                              | "
  fi
  back_footer
}

settings_menu(){
  do_action "" "settings_ui"
  while true; do
    read -p "${cyan}Perform action:${default} " action; echo
    case "$action" in
      1)
        if [ ! -z $klipper_cfg_loc ]; then
          do_action "change_klipper_cfg_path" "settings_ui"
        else
          deny_action "settings_ui"
        fi;;
      B|b)
        clear; main_menu; break;;
      *)
        deny_action "settings_ui";;
    esac
  done
  settings_ui
}
