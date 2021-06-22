### base variables
SYSTEMDDIR="/etc/systemd/system"

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

ms_theme_dracula(){
  THEME_URL="https://github.com/steadyjaw/dracula-mainsail-theme"

  ### check and select printer if there is more than 1
  check_select_printer

  ### download all files
  status_msg "Installing Dracula theme ..."
  status_msg "Please wait ..."

  [ -d "$THEME_PATH/.theme" ] && rm -rf "$THEME_PATH/.theme"
  cd $THEME_PATH && git clone "$THEME_URL" ".theme"

  ok_msg "Theme installation complete!"
  ok_msg "Please remember to delete your browser cache!\n"
}

ms_theme_cyberpunk(){
  THEME_URL="https://github.com/Dario-Ciceri/cp2077-mainsail-theme"

  ### check and select printer if there is more than 1
  check_select_printer

  ### download all files
  status_msg "Installing Cyberpunk theme ..."
  status_msg "Please wait ..."

  [ -d "$THEME_PATH/.theme" ] && rm -rf "$THEME_PATH/.theme"
  cd $THEME_PATH && git clone "$THEME_URL" ".theme"

  ok_msg "Theme installation complete!"
  ok_msg "Please remember to delete your browser cache!\n"
}

ms_theme_voron_toolhead(){
  THEME_URL="https://github.com/eriroh/Mainsail-x-Voron-Toolhead-Theme"

  ### check and select printer if there is more than 1
  check_select_printer

  ### download all files
  status_msg "Installing Mainsail x Voron Toolhead theme ..."
  status_msg "Please wait ..."

  [ -d "$THEME_PATH/.theme" ] && rm -rf "$THEME_PATH/.theme"
  cd $THEME_PATH && git clone "$THEME_URL" ".theme"

  ok_msg "Theme installation complete!"
  ok_msg "Please remember to delete your browser cache!\n"
}