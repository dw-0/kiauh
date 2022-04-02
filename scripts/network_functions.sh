function set_nginx_cfg(){
  if [ "$SET_NGINX_CFG" = "true" ]; then
    #check for dependencies
    dep=(nginx)
    dependency_check
    #execute operations
    status_msg "Creating Nginx configuration for $1 ..."
    #copy content from resources to the respective nginx config file
    cat ${SRCDIR}/kiauh/resources/klipper_webui_nginx.cfg > ${SRCDIR}/kiauh/resources/$1
    ##edit the nginx config file before moving it
    sed -i "s/<<UI>>/$1/g" ${SRCDIR}/kiauh/resources/$1
    if [ "$SET_LISTEN_PORT" != "$DEFAULT_PORT" ]; then
      status_msg "Configuring port for $1 ..."
      #set listen port ipv4
      sed -i "s/listen\s[0-9]*;/listen $SET_LISTEN_PORT;/" ${SRCDIR}/kiauh/resources/$1
      #set listen port ipv6
      sed -i "s/listen\s\[\:*\]\:[0-9]*;/listen \[::\]\:$SET_LISTEN_PORT;/" ${SRCDIR}/kiauh/resources/$1
    fi
    #set correct user
    if [ "$1" = "mainsail" ] || [ "$1" = "fluidd" ]; then
      sudo sed -i "/root/s/pi/${USER}/" ${SRCDIR}/kiauh/resources/$1
    fi
    #moving the config file into correct directory
    sudo mv ${SRCDIR}/kiauh/resources/$1 /etc/nginx/sites-available/$1
    ok_msg "Nginx configuration for $1 was set!"
    if [ "$SET_LISTEN_PORT" != "" ]; then
      ok_msg "$1 listening on port $SET_LISTEN_PORT!"
    else
      ok_msg "$1 listening on default port $DEFAULT_PORT!"
    fi
    #remove nginx default config
    [ -e /etc/nginx/sites-enabled/default ] && sudo rm /etc/nginx/sites-enabled/default
    #create symlink for own sites
    [ ! -e /etc/nginx/sites-enabled/$1 ] && sudo ln -s /etc/nginx/sites-available/$1 /etc/nginx/sites-enabled/
    restart_nginx
  fi
}

function read_listen_port(){
  LISTEN_PORT=$(grep listen /etc/nginx/sites-enabled/$1 | head -1 | sed 's/^\s*//' | cut -d" " -f2 | cut -d";" -f1)
}

function detect_enabled_sites(){
  #check if there is another UI config already installed
  #and reads the port they are listening on
  if [ -e /etc/nginx/sites-enabled/mainsail ]; then
    SITE_ENABLED="true" && MAINSAIL_ENABLED="true"
    read_listen_port "mainsail"
    MAINSAIL_PORT=$LISTEN_PORT
    #echo "debug: Mainsail listens on port: $MAINSAIL_PORT"
  else
    MAINSAIL_ENABLED="false"
  fi
  if [ -e /etc/nginx/sites-enabled/fluidd ]; then
    SITE_ENABLED="true" && FLUIDD_ENABLED="true"
    read_listen_port "fluidd"
    FLUIDD_PORT=$LISTEN_PORT
    #echo "debug: Fluidd listens on port: $FLUIDD_PORT"
  else
    FLUIDD_ENABLED="false"
  fi
  if [ -e /etc/nginx/sites-enabled/octoprint ]; then
    SITE_ENABLED="true" && OCTOPRINT_ENABLED="true"
    read_listen_port "octoprint"
    OCTOPRINT_PORT=$LISTEN_PORT
    #echo "debug: OctoPrint listens on port: $OCTOPRINT_PORT"
  else
    OCTOPRINT_ENABLED="false"
  fi
}

function create_custom_hostname(){
  echo
  top_border
  echo -e "|  You can change the hostname of this machine to use   |"
  echo -e "|  that name to open the Interface in your browser.     |"
  echo -e "|                                                       |"
  echo -e "|  E.g.: If you set the hostname to 'my-printer' you    |"
  echo -e "|        can open Mainsail / Fluidd / Octoprint by      |"
  echo -e "|        browsing to: http://my-printer.local           |"
  bottom_border
  while true; do
    read -p "${cyan}###### Do you want to change the hostname? (y/N):${white} " yn
    case "$yn" in
      Y|y|Yes|yes)
        user_input_hostname
        break;;
      N|n|No|no|"") break;;
      *)
        print_unkown_cmd
        print_msg && clear_msg;;
    esac
  done
}

function user_input_hostname(){
    unset NEW_HOSTNAME
    unset HOSTNAME_VALID
    unset HOSTENAME_CONFIRM
    echo
    top_border
    echo -e "|  ${green}Allowed characters: a-z, 0-9 and single '-'${white}          |"
    echo -e "|  ${red}No special characters allowed!${white}                       |"
    echo -e "|  ${red}No leading or trailing '-' allowed!${white}                  |"
    bottom_border
    while true; do
      read -p "${cyan}###### Please set the new hostname:${white} " NEW_HOSTNAME
      if [[ $NEW_HOSTNAME =~ ^[^\-\_]+([0-9a-z]\-{0,1})+[^\-\_]+$ ]]; then
        ok_msg "'$NEW_HOSTNAME' is a valid hostname!"
        HOSTNAME_VALID="true"
        while true; do
          echo
          read -p "${cyan}###### Do you want '$NEW_HOSTNAME' to be the new hostname? (Y/n):${white} " yn
          case "$yn" in
            Y|y|Yes|yes|"")
              echo -e "###### > Yes"
              HOSTENAME_CONFIRM="true"
              break;;
            N|n|No|no)
              echo -e "###### > No"
              echo -e "${red}Skip hostname change ...${white}"
              HOSTENAME_CONFIRM="false"
              break;;
            *)
              print_unkown_cmd
              print_msg && clear_msg;;
          esac
        done
      break
      else
        warn_msg "'$NEW_HOSTNAME' is not a valid hostname!"
      fi
    done
}

function set_hostname(){
  if [ "$HOSTNAME_VALID" = "true" ] && [ "$HOSTENAME_CONFIRM" = "true" ]; then
    #check for dependencies
    dep=(avahi-daemon)
    dependency_check
    #execute operations
    #get current hostname and write to variable
    HOSTNAME=$(hostname)
    #create host file if missing or create backup of existing one with current date&time
    if [ -f /etc/hosts ]; then
      status_msg "Creating backup of hosts file ..."
      get_date
      sudo cp /etc/hosts /etc/hosts."$current_date".bak
      ok_msg "Backup done!"
      ok_msg "File:'/etc/hosts."$current_date".bak'"
    else
      sudo touch /etc/hosts
    fi
    #set hostname in /etc/hostname
    status_msg "Setting hostname to '$NEW_HOSTNAME' ..."
    status_msg "Please wait ..."
    sudo hostnamectl set-hostname "$NEW_HOSTNAME"
    #write new hostname to /etc/hosts
    status_msg "Writing new hostname to /etc/hosts ..."
    echo "127.0.0.1       $NEW_HOSTNAME" | sudo tee -a /etc/hosts &>/dev/null
    ok_msg "New hostname successfully configured!"
    ok_msg "Remember to reboot for the changes to take effect!"
  fi
}
