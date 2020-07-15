mainsail_install_routine(){
  if [ -d $KLIPPER_DIR ]; then
    #check for dependencies
    dep=(wget curl unzip)
    dep_check
    #execute operation
    disable_wrong_webserver
    remove_wrong_webserver
    install_moonraker
    if [ $ERROR != 1 ]; then
      check_printer_cfg
      restart_moonraker
      restart_klipper
      install_nginx
      test_api
      test_nginx
      install_mainsail && ok_msg "Mainsail install complete!"; echo
    fi
  else
    ERROR_MSG=" Please install Klipper first!\n Skipping..."
  fi
}

install_moonraker(){
  cd $KLIPPER_DIR
  if [[ $(git describe --all) = "remotes/Arksine/work-web_server-20200131" || $(git describe --all) = "remotes/Arksine/dev-moonraker-testing" ]]; then
    status_msg "Installing Moonraker ..."
    $KLIPPER_DIR/scripts/install-moonraker.sh && ok_msg "Moonraker successfully installed!"
    if [ ! -d ${HOME}/sdcard ]; then
      mkdir ${HOME}/sdcard
    fi
    #create a moonraker.log symlink in home-dir just for convenience
    if [ ! -e ${HOME}/moonraker.log ]; then
      status_msg "Creating moonraker.log symlink ..."
      ln -s /tmp/moonraker.log ${HOME}/moonraker.log && ok_msg "Symlink created!"
    fi
  else
    ERROR_MSG=" You are not using a moonraker fork\n Please switch to a moonraker fork first! Aborting ..."
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
    status_msg "Configuring virtual sdcard..."
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
  status_msg "Checking for api_server configuration ..."
  # check if api server is present in printer.cfg
  if [ $(grep '^\[api_server\]$' $PRINTER_CFG) ]; then
    ok_msg "API server already configured"
  else
    status_msg "No API server entry found."
    status_msg "Configuring API server..."
# append the following lines to printer.cfg
cat <<API >> $PRINTER_CFG

##########################
### CREATED WITH KIAUH ###
##########################
[api_server]
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

[api_server]
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

disable_wrong_webserver(){
  if systemctl is-active haproxy -q; then
    status_msg "Stopping haproxy service ..."
    sudo /etc/init.d/haproxy stop && ok_msg "Service stopped!"
  fi
  if systemctl is-active lighttpd -q; then
    status_msg "Stopping lighttpd service ..."
    sudo /etc/init.d/lighttpd stop && ok_msg "Service stopped!"
  fi
}

remove_wrong_webserver(){
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

install_nginx(){
  if ! [[ $(dpkg-query -f'${Status}' --show nginx 2>/dev/null) = *\ installed ]]; then
    status_msg "Installing Nginx ..."
    sudo apt-get install nginx -y && ok_msg "Nginx successfully installed!"
  fi
  if [ ! -d $MAINSAIL_DIR ]; then
    mkdir $MAINSAIL_DIR
  fi
  status_msg "Configure Nginx ..."
  create_mainsail_cfgfile && sudo mv $MAINSAIL_DIR/mainsail /etc/nginx/sites-available/
  if [ -e /etc/nginx/sites-enabled/default ]; then
    sudo rm /etc/nginx/sites-enabled/default
  fi
  if [ ! -e /etc/nginx/sites-enabled/mainsail ]; then
    sudo ln -s /etc/nginx/sites-available/mainsail /etc/nginx/sites-enabled/
  fi
  ok_msg "Nginx configured!"
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
  MAINSAIL_VERSION=`curl -s https://api.github.com/repositories/240875926/tags | grep name | cut -d'"' -f4 | cut -d"v" -f2 | head -1`
}

mainsail_dl_url(){
  get_mainsail_ver
  MAINSAIL_URL=https://github.com/meteyou/mainsail/releases/download/v"$MAINSAIL_VERSION"/mainsail-alpha-"$MAINSAIL_VERSION".zip
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
}

create_mainsail_cfgfile(){
  cat <<MAINSAIL_CFG > $MAINSAIL_DIR/mainsail
map \$http_upgrade \$connection_upgrade {
    default upgrade;
    '' close;
}

upstream apiserver {
    #edit your api port here
    ip_hash;
    server 127.0.0.1:7125;
}

server {
    listen 80 default_server;
    listen [::]:80 default_server;

    access_log /var/log/nginx/mainsail-access.log;
    error_log /var/log/nginx/mainsail-error.log;

    #web_path from mainsail static files
    root /home/pi/mainsail;

    index index.html;
    server_name _;

    #max upload size for gcodes
    client_max_body_size 200M;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /printer {
        proxy_pass http://apiserver/printer;
        proxy_set_header Host \$http_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme \$scheme;
    }

    location /api {
        proxy_pass http://apiserver/api;
        proxy_set_header Host \$http_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme \$scheme;
    }

    location /access {
        proxy_pass http://apiserver/access;
        proxy_set_header Host \$http_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme \$scheme;
    }

    location /websocket {
        proxy_pass http://apiserver/websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \$connection_upgrade;
        proxy_set_header Host \$http_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }

    location /machine {
        proxy_pass http://apiserver/machine;
        proxy_set_header Host \$http_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme \$scheme;
    }

    location /server {
        proxy_pass http://apiserver/server;
        proxy_set_header Host \$http_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme \$scheme;
    }
}
MAINSAIL_CFG
}