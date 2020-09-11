create_reverse_proxy(){
  if [ "$SET_REVERSE_PROXY" = "true" ]; then
    #check for dependencies
    dep=(nginx)
    dependency_check
    #execute operations
    status_msg "Creating Nginx configuration for $1 ..."
    cat ${HOME}/kiauh/resources/$1_nginx.cfg > ${HOME}/kiauh/resources/$1
    sudo mv ${HOME}/kiauh/resources/$1 /etc/nginx/sites-available/$1
    #ONLY FOR MAINSAIL: replace username if not "pi"
      if [ "$1" = "mainsail" ]; then
        sudo sed -i "/root/s/pi/${USER}/" /etc/nginx/sites-available/mainsail
      fi
    ok_msg "Nginx configuration for $1 was set!"
    #remove default config
    if [ -e /etc/nginx/sites-enabled/default ]; then
      sudo rm /etc/nginx/sites-enabled/default
    fi
    #create symlink for own configs
    if [ ! -e /etc/nginx/sites-enabled/$1 ]; then
      sudo ln -s /etc/nginx/sites-available/$1 /etc/nginx/sites-enabled/
    fi
    restart_nginx
  fi
}

create_custom_hostname(){
  echo
  top_border
  echo -e "|  You can change the hostname of this machine to use   |"
  echo -e "|  that name to open the Interface in your browser.     |"
  echo -e "|                                                       |"
  echo -e "|  Example: If you set the hostname to 'my-printer'     |"
  echo -e "|           you can open DWC2/Mainsail/Octoprint by     |"
  echo -e "|           browsing to: http://my-printer.local        |"
  bottom_border
  while true; do
    read -p "${cyan}###### Do you want to change the hostname? (y/N):${default} " yn
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

user_input_hostname(){
    unset NEW_HOSTNAME
    unset HOSTNAME_VALID
    unset HOSTENAME_CONFIRM
    echo
    top_border
    echo -e "|  ${green}Allowed characters: a-z, 0-9 and single '-'${default}          |"
    echo -e "|  ${red}No special characters allowed!${default}                       |"
    echo -e "|  ${red}No leading or trailing '-' allowed!${default}                  |"
    bottom_border
    while true; do
      read -p "${cyan}###### Please set the new hostname:${default} " NEW_HOSTNAME
      if [[ $NEW_HOSTNAME =~ ^[^\-\_]+([0-9a-z]\-{0,1})+[^\-\_]+$ ]]; then
        ok_msg "'$NEW_HOSTNAME' is a valid hostname!"
        HOSTNAME_VALID="true"
        while true; do
          echo
          read -p "${cyan}###### Do you want '$NEW_HOSTNAME' to be the new hostname? (Y/n):${default} " yn
          case "$yn" in
            Y|y|Yes|yes|"")
              echo -e "###### > Yes"
              HOSTENAME_CONFIRM="true"
              break;;
            N|n|No|no)
              echo -e "###### > No"
              echo -e "${red}Skip hostname change ...${default}"
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

set_hostname(){
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
    if cat /etc/hosts | grep "###set by kiauh" &>/dev/null; then
      sudo sed -i "/###set by kiauh/s/\<$HOSTNAME\>/$NEW_HOSTNAME/" /etc/hosts
    else
      echo "127.0.0.1     $NEW_HOSTNAME ###set by kiauh" | sudo tee -a /etc/hosts &>/dev/null
    fi
    ok_msg "New hostname successfully configured!"
    ok_msg "Remember to reboot for the changes to take effect!"
  fi
}
