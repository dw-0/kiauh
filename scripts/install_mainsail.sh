install_mainsail(){
  if [ "$INST_MAINSAIL" = "true" ]; then
    disable_haproxy_lighttpd
    unset SET_REVERSE_PROXY && SET_REVERSE_PROXY="true" #quick and dirty hack to make mainsail reverse proxy install, needs polish
    create_reverse_proxy "mainsail"
    mainsail_setup
    test_nginx
    ok_msg "Mainsail installation complete!"; echo
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

test_nginx(){
  status_msg "Testing Nginx ..."
  sleep 5
  status_msg "API response from http://localhost/printer/info :"
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