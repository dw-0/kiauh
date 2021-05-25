ms_theme_ui(){
  top_border
  echo -e "|     ${red}~~~~~~~~ [ Mainsail Theme Installer ] ~~~~~~~${default}     | "
  hr
  echo -e "|  Please note:                                         | "
  echo -e "|  Installing a theme from this menu will overwrite an  | "
  echo -e "|  already installed theme or modified custom.css file! | "
  hr
  echo -e "|  Theme:                                               | "
  echo -e "|  1) [Dracula]                                         | "
  echo -e "|  2) [Cyberpunk]                                       | "
  echo -e "|                                                       | "
  echo -e "|  R) [Remove Theme]                                    | "
  echo -e "|                                                       | "
  quit_footer
}

ms_theme_menu(){
  do_action "" "ms_theme_ui"
  while true; do
    read -p "${cyan}Perform action:${default} " action; echo
    case "$action" in
      1) do_action "ms_theme_dracula" "ms_theme_ui";;
      2) do_action "ms_theme_cyberpunk" "ms_theme_ui";;
      R|r) do_action "ms_theme_delete" "ms_theme_ui";;
      Q|q) clear; advanced_menu; break;;
      *) deny_action "ms_theme_ui";;
    esac
  done
  ms_theme_menu
}