### base variables
SYSTEMDDIR="/etc/systemd/system"

check_select_printer(){
  unset printer_num

  ### get klipper cfg loc and set default theme loc
  check_klipper_cfg_path
  THEME_PATH="$klipper_cfg_loc/.theme"

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

    ### rewrite the theme path matching the selected printer
    THEME_PATH="$klipper_cfg_loc/printer_$printer_num/.theme"
  fi
}

ms_theme_delete(){
  ### check and select printer if there is more than 1
  check_select_printer

  ### remove .theme folder
  if [ -d $THEME_PATH ]; then
    status_msg "Removing Theme ..."
    rm -rf $THEME_PATH && ok_msg "Theme removed!\n"
  else
    status_msg "No Theme installed!\n"
  fi
}

ms_theme_dracula(){
  THEME_RAW_URL="https://raw.githubusercontent.com/steadyjaw/dracula-mainsail-theme/master/config/.theme/"

  ### check and select printer if there is more than 1
  check_select_printer

  ### list filenames we need to download
  files=(
    custom.css
    favicon-32x32.png
    favicon-64x64.png
    sidebar-background.png
    sidebar-logo.svg
  )

  ### check for .theme folder
  [ ! -d $THEME_PATH ] && mkdir -p $THEME_PATH
  cd $THEME_PATH

  ### download all files
  status_msg "Installing Dracula theme ..."
  status_msg "Please wait ..."
  for file in ${files[@]}
    do
      status_msg "Downloading $file ..."
      wget -q "$THEME_RAW_URL$file" -O $file
      ok_msg "Done!"
  done

  ### check if all files got downloaded
  if [ $(ls | wc -l) = ${#files[@]} ]; then
    echo
    ok_msg "Theme installation complete!"
    ok_msg "Please remember to delete your browser cache!\n"
  else
    echo
    warn_msg "Some files are missing! Please try again!\n"
  fi
}