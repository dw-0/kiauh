settings_ui(){
  source_kiauh_ini
  [ -z $klipper_cfg_loc ] && klipper_cfg_loc="----------"
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~ [ KIAUH Settings ] ~~~~~~~~~~~~~")     | "
  hr
  echo -e "| ${red}Caution:${default}                                              | "
  echo -e "| Changing the path below will COPY the config files    | "
  echo -e "| to the new location. During that process ALL Klipper  | "
  echo -e "| and Moonraker services get stopped and reconfigured.  | "
  blank_line
  echo -e "| ${red}DO NOT change the folder location during printing!${default}    | "
  hr
  blank_line
  echo -e "|  ${yellow}● Current Klipper configuration folder:${default}              | "
  printf "|%-55s|\n" "    $klipper_cfg_loc"
  blank_line
  hr
  echo -e "|  1) Change configuration folder                       | "
  quit_footer
}

settings_menu(){
  print_header
  print_msg && clear_msg
  settings_ui
  while true; do
    read -p "${cyan}Perform action:${default} " action; echo
    case "$action" in
      1)
        clear
        print_header
        change_klipper_cfg_path
        print_msg && clear_msg
        settings_ui;;
      Q|q)
        clear; main_menu; break;;
      *)
        clear
        print_header
        print_unkown_cmd
        print_msg && clear_msg
        settings_ui;;
    esac
  done
  settings_ui
}
