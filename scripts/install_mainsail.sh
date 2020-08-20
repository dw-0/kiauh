install_mainsail(){
  if [ -d $KLIPPER_DIR ] && [ "$INST_MAINSAIL" = "true" ]; then
    #disable octoprint service if installed
      if systemctl is-enabled octoprint.service -q 2>/dev/null; then
        disable_octoprint_service
      fi
    disable_haproxy_lighttpd
    #remove_haproxy_lighttpd
    #beginning of mainsail installation
    create_reverse_proxy "mainsail"
    test_api
    test_nginx
    mainsail_setup
    ok_msg "Mainsail installation complete!"; echo
  else
    ERROR_MSG=" Please install Klipper first!\n Skipping..."
  fi
}

disable_haproxy_lighttpd(){
  disable_service=(haproxy lighttpd)
  if systemctl is-active haproxy -q; then
    status_msg "Stopping haproxy service ..."
    sudo /etc/init.d/haproxy stop && ok_msg "Service stopped!"
  fi
  if systemctl is-active lighttpd -q; then
    status_msg "Stopping lighttpd service ..."
    sudo /etc/init.d/lighttpd stop && ok_msg "Service stopped!"
  fi
  for service in "${disable_service[@]}"
  do
    if [[ $(dpkg-query -f'${Status}' --show $service 2>/dev/null) = *\ installed ]]; then
      status_msg "Disabling $service service ..."
      sudo apt-get disable $service
      ok_msg "$service service disabled!"
    fi
  done
}

#remove_haproxy_lighttpd(){
#  rem=(haproxy lighttpd)
#  for remove in "${rem[@]}"
#  do
#    if [[ $(dpkg-query -f'${Status}' --show $remove 2>/dev/null) = *\ installed #]]; then
#      delete+=($remove)
#    fi
#  done
#  if ! [ ${#delete[@]} -eq 0 ]; then
#    sudo apt-get remove ${delete[@]} -y
#  fi
#}

test_api(){
  status_msg "Testing API ..."
  sleep 5
  status_msg "API response from http://localhost:7125/printer/info:"
  API_RESPONSE=$(curl -sG4m5 http://localhost:7125/printer/info)
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
  API_RESPONSE="$(curl -sG4m5 http://localhost/printer/info)"
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

mainsail_setup(){
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