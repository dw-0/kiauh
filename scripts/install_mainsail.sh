mainsail_install_routine(){
  ERROR="0" #reset error state
  if [ -d $KLIPPER_DIR ]; then
    #disable octoprint service if installed
      if systemctl is-enabled octoprint.service -q 2>/dev/null; then
        disable_octoprint_service
      fi
    disable_haproxy_lighttpd
    remove_haproxy_lighttpd
    install_moonraker
    if [ "$ERROR" != "1" ]; then
      check_printer_cfg
      restart_moonraker
      restart_klipper
      create_reverse_proxy "mainsail"
      test_api
      test_nginx
      install_mainsail
      create_custom_hostname
      ok_msg "Mainsail installation complete!"; echo
    fi
  else
    ERROR_MSG=" Please install Klipper first!\n Skipping..."
  fi
}

install_moonraker(){
  cd $KLIPPER_DIR
  if [[ $(git describe --all) = "remotes/Arksine/dev-moonraker-testing" ]]; then
    dep=(wget curl unzip)
    dependency_check
    status_msg "Downloading Moonraker ..."
    cd ${HOME} && git clone $MOONRAKER_REPO
    ok_msg "Download complete!"
    status_msg "Installing Moonraker ..."
    $MOONRAKER_DIR/scripts/install-moonraker.sh && ok_msg "Moonraker successfully installed!"
    #create sdcard folder if it doesn't exists yet
    if [ ! -d ${HOME}/sdcard ]; then
      mkdir ${HOME}/sdcard
    fi
    #create a moonraker.log symlink in home-dir just for convenience
    if [ ! -e ${HOME}/moonraker.log ]; then
      status_msg "Creating moonraker.log symlink ..."
      ln -s /tmp/moonraker.log ${HOME}/moonraker.log && ok_msg "Symlink created!"
    fi
  else
    ERROR_MSG="You are not using the Moonraker fork!\n Please switch to the Moonraker fork first! Aborting ..."
    ERROR=1
  fi
}

check_printer_cfg(){
  if [ -e $PRINTER_CFG ]; then
    check_vsdcard_section
    check_api_section
  else
    echo; warn_msg "No printer.cfg found!"
    while true; do
      echo -e "${cyan}"
      read -p "###### Do you want to create a default config now? (Y/n): " yn
      echo -e "${default}"
      case "$yn" in
        Y|y|Yes|yes|"") create_default_cfg; break;;
        N|n|No|no) break;;
      esac
    done
  fi
}

check_vsdcard_section(){
  # check if virtual sdcard is present in printer.cfg
  status_msg "Checking for virtual_sdcard configuration ..."
  if [ $(grep '^\[virtual_sdcard\]$' $PRINTER_CFG) ]; then
    ok_msg "Virtual sdcard already configured!"
  else
    status_msg "No virtual sdcard entry found."
    ok_msg "Virtual sdcard entry added to printer.cfg!"
# append the following lines to printer.cfg
cat <<VSDCARD >> $PRINTER_CFG

##########################
### CREATED WITH KIAUH ###
##########################
[virtual_sdcard]
path: ~/sdcard
##########################
##########################
VSDCARD
  fi
}

check_api_section(){
  status_msg "Checking for moonraker configuration ..."
  # check if api server is present in printer.cfg
  if [[ $(grep '^\[moonraker\]$' $PRINTER_CFG) ]]; then
    ok_msg "Moonraker already configured"
  else
    status_msg "No Moonraker entry found."
    ok_msg "Moonraker entry added to printer.cfg!"
# append the following lines to printer.cfg
cat <<API >> $PRINTER_CFG

##########################
### CREATED WITH KIAUH ###
##########################
[moonraker]
trusted_clients:
 192.168.0.0/24
 192.168.1.0/24
 127.0.0.0/24
##########################
##########################
API
  fi
}

create_default_cfg(){
cat <<DEFAULT_CFG >> $PRINTER_CFG

##########################
### CREATED WITH KIAUH ###
##########################
[virtual_sdcard]
path: ~/sdcard

[moonraker]
trusted_clients:
 192.168.0.0/24
 192.168.1.0/24
 127.0.0.0/24

[pause_resume]

[gcode_macro CANCEL]
default_parameter_X: 230
default_parameter_Y: 230
default_parameter_Z: 10
gcode:
    M104 S0
    M140 S0
    M141 S0
    M106 S0
    CLEAR_PAUSE
    RESET_SD

[gcode_macro CANCEL_PRINT]
gcode:
    CANCEL

[gcode_macro PAUSE]
rename_existing: BASE_PAUSE
default_parameter_X: 230
default_parameter_Y: 230
default_parameter_Z: 10
gcode:
    SAVE_GCODE_STATE NAME=PAUSE_state
    BASE_PAUSE
    G91
    G1 E-1.7 F2100
    G1 Z{Z}
    G90
    G1 X{X} Y{Y} F6000
    G91

[gcode_macro RESUME]
rename_existing: BASE_RESUME
gcode:
    G91
    G1 E1.7 F2100
    G91
    RESTORE_GCODE_STATE NAME=PAUSE_state MOVE=1
    BASE_RESUME
##########################
##########################
DEFAULT_CFG
}

disable_haproxy_lighttpd(){
  if systemctl is-active haproxy -q; then
    status_msg "Stopping haproxy service ..."
    sudo /etc/init.d/haproxy stop && ok_msg "Service stopped!"
  fi
  if systemctl is-active lighttpd -q; then
    status_msg "Stopping lighttpd service ..."
    sudo /etc/init.d/lighttpd stop && ok_msg "Service stopped!"
  fi
}

remove_haproxy_lighttpd(){
  rem=(haproxy lighttpd)
  for remove in "${rem[@]}"
  do
    if [[ $(dpkg-query -f'${Status}' --show $remove 2>/dev/null) = *\ installed ]]; then
      delete+=($remove)
    fi
  done
  if ! [ ${#delete[@]} -eq 0 ]; then
    sudo apt-get remove ${delete[@]} -y
  fi
}

test_api(){
  status_msg "Testing API ..."
  sleep 5
  status_msg "API response from http://localhost:7125/printer/info:"
  API_RESPONSE="$(curl -sG4 http://localhost:7125/printer/info)"
  echo -e "${cyan}$API_RESPONSE${default}"
  if [ $(curl -sG4 "http://localhost:7125/printer/info" | grep '^{"result"' -c) -eq 1 ]; then
    echo; ok_msg "Klipper API is working correctly!"; echo
  else
    echo; warn_msg "Klipper API not working correctly!"; echo
  fi
}

test_nginx(){
  sudo /etc/init.d/nginx restart
  status_msg "Testing Nginx ..."
  sleep 5
  status_msg "API response from http://localhost/printer/info:"
  API_RESPONSE="$(curl -sG4 http://localhost/printer/info)"
  echo -e "${cyan}$API_RESPONSE${default}"
  if [ $(curl -sG4 "http://localhost/printer/info" | grep '^{"result"' -c) -eq 1 ]; then
    echo; ok_msg "Nginx is working correctly!"; echo
  else
    echo; warn_msg "Nginx is not working correctly!"; echo
  fi
}

get_mainsail_ver(){
  MAINSAIL_VERSION=$(curl -s https://api.github.com/repositories/240875926/tags | grep name | cut -d'"' -f4 | cut -d"v" -f2 | head -1)
}

mainsail_dl_url(){
  get_mainsail_ver
  MAINSAIL_URL=https://github.com/meteyou/mainsail/releases/download/v"$MAINSAIL_VERSION"/mainsail-beta-"$MAINSAIL_VERSION".zip
}

install_mainsail(){
  mainsail_dl_url
  if [ ! -d $MAINSAIL_DIR ]; then
    mkdir $MAINSAIL_DIR
  fi
  cd $MAINSAIL_DIR
  status_msg "Downloading Mainsail v$MAINSAIL_VERSION ..."
  wget -q -O mainsail.zip $MAINSAIL_URL && status_msg "Extracting archive ..." && unzip -o mainsail.zip && rm mainsail.zip
  ### write mainsail version to file for update check reasons
  echo "$MAINSAIL_VERSION" > $MAINSAIL_DIR/version
  echo
}