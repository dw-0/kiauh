### base variables
PGC_FOR_KLIPPER_REPO="https://github.com/Kragrathea/pgcode"
PGC_DIR="${HOME}/pgcode"

install_pgc_for_klipper(){
  pgconfsrc="$PGC_DIR/pgcode.local.conf"
  pgconf="/etc/nginx/sites-available/pgcode.local.conf"
  pgconfsl="/etc/nginx/sites-enabled/pgcode.local.conf"
  pgc_default_port="7136"

  status_msg "Installing PrettyGCode for Klipper ..."
  ### let the user decide which port is used
  echo -e "${cyan}\n###### On which port should PrettyGCode run? (Default: $pgc_default_port)${default} "
  read -e -p "${cyan}###### Port:${default} " -i "$pgc_default_port" pgc_custom_port
  ### check nginx dependency
  dep=(nginx)
  dependency_check
  ### clone repo
  [ -d $PGC_DIR ] && rm -rf $PGC_DIR
  cd ${HOME} && git clone $PGC_FOR_KLIPPER_REPO
  ### copy nginx config into destination directory
  sudo cp $pgconfsrc $pgconf
  ### replace default pi user in case the user is called different
  sudo sed -i "s|/home/pi/pgcode;|/home/${USER}/pgcode;|" $pgconf
  ### replace default port
  if [ $pgc_custom_port != $pgc_default_port ]; then
    sudo sed -i "s|listen $pgc_default_port;|listen $pgc_custom_port;|" $pgconf
    sudo sed -i "s|listen \[::\]:$pgc_default_port;|listen \[::\]:$pgc_custom_port;|" $pgconf
  fi
  ### create symlink
  [ ! -L $pgconfsl ] && sudo ln -s $pgconf $pgconfsl
  sudo systemctl restart nginx
  ### show URI
  pgc_uri="http://$(hostname -I | cut -d" " -f1):$pgc_custom_port"
  echo -e "${cyan}\n● Accessible via:${default} $pgc_uri"
  ok_msg "PrettyGCode for Klipper installed!\n"
}