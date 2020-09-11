install_mainsail(){
  if [ "$INST_MAINSAIL" = "true" ]; then
    unset SET_REVERSE_PROXY && SET_REVERSE_PROXY="true" #quick and dirty hack to make mainsail reverse proxy install, needs polish
    create_reverse_proxy "mainsail"
    mainsail_setup
    test_nginx
    ok_msg "Mainsail installation complete!"; echo
  fi
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
  #clean up an existing mainsail folder
  if [ -d $MAINSAIL_DIR ]; then
    rm -rf $MAINSAIL_DIR
  fi
  #create fresh mainsail folder and download mainsail
  mkdir $MAINSAIL_DIR
  cd $MAINSAIL_DIR
  status_msg "Downloading Mainsail v$MAINSAIL_VERSION ..."
  wget -q -O mainsail.zip $MAINSAIL_URL && status_msg "Extracting archive ..." && unzip -o mainsail.zip && rm mainsail.zip
  ### write mainsail version to file for update check reasons
  echo "$MAINSAIL_VERSION" > $MAINSAIL_DIR/version
  echo
}