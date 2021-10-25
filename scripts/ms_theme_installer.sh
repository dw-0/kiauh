### base variables
SYSTEMDDIR="/etc/systemd/system"

get_theme_list(){
  theme_csv_url="https://raw.githubusercontent.com/meteyou/mainsail/develop/docs/_data/themes.csv"
  theme_csv=$(curl -s -L $theme_csv_url)
  unset t_name
  unset t_note
  unset t_auth
  unset t_url
  i=0
  while IFS="," read -r col1 col2 col3 col4; do
    t_name+=("$col1")
    t_note+=("$col2")
    t_auth+=("$col3")
    t_url+=("$col4")
    if [ ! "$col1" == "name" ]; then
      printf "|  $i) %-50s|\n" "[$col1]"
    fi
    let i++
  done <<< $theme_csv
}

ms_theme_ui(){
  top_border
  echo -e "|     ${red}~~~~~~~~ [ Mainsail Theme Installer ] ~~~~~~~${default}     | "
  hr
  echo -e "|  ${green}A preview of each Mainsail theme can be found here:${default}  | "
  echo -e "|  https://docs.mainsail.xyz/theming/themes             | "
  blank_line
  echo -e "|  ${yellow}Important note:${default}                                      | "
  echo -e "|  Installing a theme from this menu will overwrite an  | "
  echo -e "|  already installed theme or modified custom.css file! | "
  hr
  #echo -e "|  Theme:                                               | "
  # dynamically generate the themelist from a csv file
  get_theme_list
  echo -e "|                                                       | "
  echo -e "|  R) [Remove Theme]                                    | "
  #echo -e "|                                                       | "
  back_footer
}

ms_theme_menu(){
  ms_theme_ui
  while true; do
    read -p "${cyan}Install theme:${default} " a; echo
    if [ $a = "b" ] || [ $a = "B" ]; then
      clear && advanced_menu && break
    elif [ $a = "r" ] || [ $a = "R" ]; then
      ms_theme_delete
      ms_theme_menu
    elif [ $a -le ${#t_url[@]} ]; then
      ms_theme_install "${t_auth[$a]}" "${t_url[$a]}" "${t_name[$a]}" "${t_note[$a]}"
      ms_theme_menu
    else
      clear && print_header
      ERROR_MSG="Invalid command!" && print_msg && clear_msg
      ms_theme_menu
    fi
  done
  ms_theme_menu
}

check_select_printer(){
  unset printer_num

  ### get klipper cfg loc and set default .theme folder loc
  check_klipper_cfg_path
  THEME_PATH="$klipper_cfg_loc"

  ### check if there is more than one moonraker instance and if yes
  ### ask the user to select the printer he wants to install/remove the theme
  printer_count=$(ls /etc/systemd/system/moonraker*.service | wc -l)
  if [ $printer_count -gt 1 ]; then
    top_border
    echo -e "|  More than one printer was found on this system!      | "
    echo -e "|  Please select the printer to which you want to       | "
    echo -e "|  apply the previously selected action.                | "
    bottom_border
    read -p "${cyan}Select printer:${default} " printer_num

    ### rewrite the .theme path matching the selected printer
    THEME_PATH="$klipper_cfg_loc/printer_$printer_num"
  fi

  ### create the cfg folder if there is none yet
  [ ! -d $THEME_PATH ] && mkdir -p $THEME_PATH
}

ms_theme_install(){
  THEME_URL="https://github.com/$1/$2"

  ### check and select printer if there is more than 1
  check_select_printer

  ### download all files
  status_msg "Installing $3 ..."
  status_msg "Please wait ..."

  [ -d "$THEME_PATH/.theme" ] && rm -rf "$THEME_PATH/.theme"
  cd $THEME_PATH && git clone "$THEME_URL" ".theme"

  ok_msg "Theme installation complete!"
  [ ! -z "$4" ] && echo "${yellow}###### Theme Info: $4${default}"
  ok_msg "Please remember to delete your browser cache!\n"
}

ms_theme_delete(){
  ### check and select printer if there is more than 1
  check_select_printer

  ### remove .theme folder
  if [ -d "$THEME_PATH/.theme" ]; then
    status_msg "Removing Theme ..."
    rm -rf "$THEME_PATH/.theme" && ok_msg "Theme removed!\n"
  else
    status_msg "No Theme installed!\n"
  fi
}
