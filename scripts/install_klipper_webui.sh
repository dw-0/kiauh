check_moonraker(){
  status_msg "Checking for Moonraker service ..."
  if [ "$(systemctl list-units --full -all -t service --no-legend | grep -F "moonraker.service")" ] || [ "$(systemctl list-units --full -all -t service --no-legend | grep -E "moonraker-[[:digit:]].service")" ]; then
    ok_msg "Moonraker service found!"; echo
    MOONRAKER_SERVICE_FOUND="true"
  else
    warn_msg "Moonraker service not found!"
    warn_msg "Please install Moonraker first!"; echo
    MOONRAKER_SERVICE_FOUND="false"
  fi
}

# get_user_selection_webui(){
#   #ask user for webui default macros
#   while true; do
#     unset ADD_WEBUI_MACROS
#     echo
#     top_border
#     echo -e "| It is recommended to have some important macros to    |"
#     echo -e "| have full functionality of the web interface.         |"
#     blank_line
#     echo -e "| If you do not have such macros, you can choose to     |"
#     echo -e "| install the suggested default macros now.             |"
#     bottom_border
#     read -p "${cyan}###### Add the recommended macros? (Y/n):${default} " yn
#     case "$yn" in
#       Y|y|Yes|yes|"")
#         echo -e "###### > Yes"
#         ADD_WEBUI_MACROS="true"
#         break;;
#       N|n|No|no)
#         echo -e "###### > No"
#         ADD_WEBUI_MACROS="false"
#         break;;
#       *)
#         print_unkown_cmd
#         print_msg && clear_msg;;
#     esac
#   done
# }

install_mainsail(){
  ###! outdated dialog, see comment below regarding webui macros
  #get_user_selection_webui

  ### check if moonraker is already installed
  check_moonraker

  if [ "$MOONRAKER_SERVICE_FOUND" = "true" ]; then
    ### check for other enabled web interfaces
    unset SET_LISTEN_PORT
    detect_enabled_sites

    ### check if another site already listens to port 80
    mainsail_port_check

    ### ask user to enable the moonraker update manager
    enable_update_manager "mainsail"

    ### creating the mainsail nginx cfg
    set_nginx_cfg "mainsail"

    ###! outdated way of locating the printer.cfg. need a new way to install the webui-macros
    ###! especially for multi instances, therefore disabling this function for now...
    #locate_printer_cfg && read_printer_cfg "mainsail"
    #install_webui_macros

    ### install mainsail
    mainsail_setup
  fi
}

install_fluidd(){
  ###! outdated dialog, see comment below regarding webui macros
  #get_user_selection_webui

  ### check if moonraker is already installed
  check_moonraker

  if [ "$MOONRAKER_SERVICE_FOUND" = "true" ]; then
    ### check for other enabled web interfaces
    unset SET_LISTEN_PORT
    detect_enabled_sites

    ### check if another site already listens to port 80
    fluidd_port_check

    ### ask user to enable the moonraker update manager
    enable_update_manager "fluidd"

    ### creating the fluidd nginx cfg
    set_nginx_cfg "fluidd"

    ###! outdated way of locating the printer.cfg. need a new way to install the webui-macros
    ###! especially for multi instances, therefore disabling this function for now...
    #locate_printer_cfg && read_printer_cfg "fluidd"
    #install_webui_macros

    ### install fluidd
    fluidd_setup
  fi
}

# install_webui_macros(){
#   #copy webui_macros.cfg
#   if [ "$ADD_WEBUI_MACROS" = "true" ]; then
#     status_msg "Create webui_macros.cfg ..."
#     if [ ! -f ${HOME}/klipper_config/webui_macros.cfg ]; then
#       cp ${HOME}/kiauh/resources/webui_macros.cfg ${HOME}/klipper_config
#       ok_msg "File created!"
#     else
#       warn_msg "File already exists! Skipping ..."
#     fi
#   fi
#   write_printer_cfg
# }

mainsail_port_check(){
  if [ "$MAINSAIL_ENABLED" = "false" ]; then
    if [ "$SITE_ENABLED" = "true" ]; then
      status_msg "Detected other enabled interfaces:"
      [ "$OCTOPRINT_ENABLED" = "true" ] && echo -e "   ${cyan}● OctoPrint - Port: $OCTOPRINT_PORT${default}"
      [ "$FLUIDD_ENABLED" = "true" ] && echo -e "   ${cyan}● Fluidd - Port: $FLUIDD_PORT${default}"
      [ "$DWC2_ENABLED" = "true" ] && echo -e "   ${cyan}● DWC2 - Port: $DWC2_PORT${default}"
      if [ "$FLUIDD_PORT" = "80" ] || [ "$DWC2_PORT" = "80" ] || [ "$OCTOPRINT_PORT" = "80" ]; then
        PORT_80_BLOCKED="true"
        select_mainsail_port
      fi
    else
      DEFAULT_PORT=$(grep listen ${SRCDIR}/kiauh/resources/mainsail_nginx.cfg | head -1 | sed 's/^\s*//' | cut -d" " -f2 | cut -d";" -f1)
      SET_LISTEN_PORT=$DEFAULT_PORT
    fi
    SET_NGINX_CFG="true"
  else
    SET_NGINX_CFG="false"
  fi
}

fluidd_port_check(){
  if [ "$FLUIDD_ENABLED" = "false" ]; then
    if [ "$SITE_ENABLED" = "true" ]; then
      status_msg "Detected other enabled interfaces:"
      [ "$OCTOPRINT_ENABLED" = "true" ] && echo "   ${cyan}● OctoPrint - Port: $OCTOPRINT_PORT${default}"
      [ "$MAINSAIL_ENABLED" = "true" ] && echo "   ${cyan}● Mainsail - Port: $MAINSAIL_PORT${default}"
      [ "$DWC2_ENABLED" = "true" ] && echo "   ${cyan}● DWC2 - Port: $DWC2_PORT${default}"
      if [ "$MAINSAIL_PORT" = "80" ] || [ "$DWC2_PORT" = "80" ] || [ "$OCTOPRINT_PORT" = "80" ]; then
        PORT_80_BLOCKED="true"
        select_fluidd_port
      fi
    else
      DEFAULT_PORT=$(grep listen ${SRCDIR}/kiauh/resources/fluidd_nginx.cfg | head -1 | sed 's/^\s*//' | cut -d" " -f2 | cut -d";" -f1)
      SET_LISTEN_PORT=$DEFAULT_PORT
    fi
    SET_NGINX_CFG="true"
  else
    SET_NGINX_CFG="false"
  fi
}

select_mainsail_port(){
  if [ "$PORT_80_BLOCKED" = "true" ]; then
    echo
    top_border
    echo -e "|                    ${red}!!!WARNING!!!${default}                      |"
    echo -e "| ${red}You need to choose a different port for Mainsail!${default}     |"
    echo -e "| ${red}The following web interface is listening at port 80:${default}  |"
    blank_line
    [ "$OCTOPRINT_PORT" = "80" ] && echo "|  ● OctoPrint                                          |"
    [ "$FLUIDD_PORT" = "80" ] && echo "|  ● Fluidd                                             |"
    [ "$DWC2_PORT" = "80" ] && echo "|  ● DWC2                                               |"
    blank_line
    echo -e "| Make sure you don't choose a port which was already   |"
    echo -e "| assigned to one of the other web interfaces!          |"
    blank_line
    echo -e "| Be aware: there is ${red}NO${default} sanity check for the following  |"
    echo -e "| input. So make sure to choose a valid port!           |"
    bottom_border
    while true; do
      read -p "${cyan}Please enter a new Port:${default} " NEW_PORT
      if [ "$NEW_PORT" != "$FLUIDD_PORT" ] && [ "$NEW_PORT" != "$DWC2_PORT" ] && [ "$NEW_PORT" != "$OCTOPRINT_PORT" ]; then
        echo "Setting port $NEW_PORT for Mainsail!"
        SET_LISTEN_PORT=$NEW_PORT
        break
      else
        echo "That port is already taken! Select a different one!"
      fi
    done
  fi
}

select_fluidd_port(){
  if [ "$PORT_80_BLOCKED" = "true" ]; then
    echo
    top_border
    echo -e "|                    ${red}!!!WARNING!!!${default}                      |"
    echo -e "| ${red}You need to choose a different port for Fluidd!${default}       |"
    echo -e "| ${red}The following web interface is listening at port 80:${default}  |"
    blank_line
    [ "$OCTOPRINT_PORT" = "80" ] && echo "|  ● OctoPrint                                          |"
    [ "$MAINSAIL_PORT" = "80" ] && echo "|  ● Mainsail                                           |"
    [ "$DWC2_PORT" = "80" ] && echo "|  ● DWC2                                               |"
    blank_line
    echo -e "| Make sure you don't choose a port which was already   |"
    echo -e "| assigned to one of the other web interfaces!          |"
    blank_line
    echo -e "| Be aware: there is ${red}NO${default} sanity check for the following  |"
    echo -e "| input. So make sure to choose a valid port!           |"
    bottom_border
    while true; do
      read -p "${cyan}Please enter a new Port:${default} " NEW_PORT
      if [ "$NEW_PORT" != "$MAINSAIL_PORT" ] && [ "$NEW_PORT" != "$DWC2_PORT" ] && [ "$NEW_PORT" != "$OCTOPRINT_PORT" ]; then
        echo "Setting port $NEW_PORT for Fluidd!"
        SET_LISTEN_PORT=$NEW_PORT
        break
      else
        echo "That port is already taken! Select a different one!"
      fi
    done
  fi
}

get_mainsail_ver(){
  MAINSAIL_VERSION=$(curl -s https://api.github.com/repositories/240875926/releases | grep tag_name | cut -d'"' -f4 | cut -d"v" -f2 | head -1)
}

get_fluidd_ver(){
  FLUIDD_VERSION=$(curl -s https://api.github.com/repositories/295836951/releases | grep tag_name | cut -d'"' -f4 | cut -d"v" -f2 | head -1)
}

mainsail_setup(){
  ### get mainsail download url
  MAINSAIL_DL_URL=$(curl -s https://api.github.com/repositories/240875926/releases | grep browser_download_url | cut -d'"' -f4 | head -1)

  ### remove existing and create fresh mainsail folder, then download mainsail
  [ -d $MAINSAIL_DIR ] && rm -rf $MAINSAIL_DIR
  mkdir $MAINSAIL_DIR && cd $MAINSAIL_DIR
  status_msg "Downloading Mainsail $MAINSAIL_VERSION ..."
  wget $MAINSAIL_DL_URL && ok_msg "Download complete!"

  ### extract archive
  status_msg "Extracting archive ..."
  unzip -q -o *.zip && ok_msg "Done!"

  ### delete downloaded zip
  status_msg "Remove downloaded archive ..."
  rm -rf *.zip && ok_msg "Done!" && ok_msg "Mainsail installation complete!"
  echo
}

fluidd_setup(){
  ### get fluidd download url
  FLUIDD_DL_URL=$(curl -s https://api.github.com/repositories/295836951/releases/latest | grep browser_download_url | cut -d'"' -f4)

  ### remove existing and create fresh fluidd folder, then download fluidd
  [ -d $FLUIDD_DIR ] && rm -rf $FLUIDD_DIR
  mkdir $FLUIDD_DIR && cd $FLUIDD_DIR
  status_msg "Downloading Fluidd $FLUIDD_VERSION ..."
  wget $FLUIDD_DL_URL && ok_msg "Download complete!"

  ### extract archive
  status_msg "Extracting archive ..."
  unzip -q -o *.zip && ok_msg "Done!"

  ###! this will be difficult to achieve for multi instances, so i will disable those functions for now....
  ###! will be probably easier to tell the user to simply re-install moonraker, those entries will be there then.
  ### patch moonraker.conf to apply cors domains if needed
  #backup_moonraker_conf
  #patch_moonraker

  ### delete downloaded zip
  status_msg "Remove downloaded archive ..."
  rm -rf *.zip && ok_msg "Done!" && ok_msg "Fluidd installation complete!"
  echo
}

enable_update_manager(){
  source_kiauh_ini
  ### ask user if he wants to enable the moonraker update manager
  while true; do
    echo
    top_border
    echo -e "| Do you want to enable the Moonraker Update Manager    | "
    echo -e "| for the selected webinterface?                        | "
    hr
    echo -e "| ${yellow}Please note:${default}                                          | "
    echo -e "| Entries for an already enabled update manager will be | "
    echo -e "| overwritten if you decide to choose 'Yes'!            | "
    bottom_border
    echo
    read -p "${cyan}###### Enable Update Manager? (Y/n):${default} " yn
    case "$yn" in
      Y|y|Yes|yes|"")
        echo -e "###### > Yes"
        if [ $1 = "mainsail" ]; then
          MOONRAKER_UPDATE_MANAGER="[update_manager]\nclient_repo: meteyou/mainsail\nclient_path: /home/${USER}/mainsail"
        elif [ $1 = "fluidd" ]; then
          MOONRAKER_UPDATE_MANAGER="[update_manager]\nclient_repo: cadriel/fluidd\nclient_path: /home/${USER}/fluidd"
        else
          unset MOONRAKER_UPDATE_MANAGER
        fi
        ### handle single moonraker install
        if [ -f /etc/systemd/system/moonraker.service ]; then
          ### delete existing entries
          sed -i "/update_manager/d" $klipper_cfg_loc/moonraker.conf
          sed -i "/client_repo/d" $klipper_cfg_loc/moonraker.conf
          sed -i "/client_path/d" $klipper_cfg_loc/moonraker.conf
          echo -e $MOONRAKER_UPDATE_MANAGER >> $klipper_cfg_loc/moonraker.conf
        fi
        ### handle multi moonraker installs
        if ls /etc/systemd/system/moonraker-*.service 2>/dev/null 1>&2; then
          for moonraker_conf in $(find $klipper_cfg_loc/printer_*/moonraker.conf); do
            ### delete existing entries
            sed -i "/update_manager/d" $moonraker_conf
            sed -i "/client_repo/d" $moonraker_conf
            sed -i "/client_path/d" $moonraker_conf
            echo -e $MOONRAKER_UPDATE_MANAGER >> $moonraker_conf
          done
        fi
        moonraker_service "restart"
        break;;
      N|n|No|no)
        echo -e "###### > No"
        unset MOONRAKER_UPDATE_MANAGER
        break;;
      *)
        print_unkown_cmd
        print_msg && clear_msg;;
    esac
  done
}

# patch_moonraker(){
#   status_msg "Patching moonraker.conf ..."
#   mr_conf=${HOME}/moonraker.conf
#   # remove the now deprecated enable_cors option from moonraker.conf if it still exists
#   if [ "$(grep "^enable_cors:" $mr_conf)" ]; then
#     line="$(grep -n "^enable_cors:" ~/moonraker.conf | cut -d":" -f1)d"
#     sed -i "$line" $mr_conf && mr_restart="true"
#   fi
#   # looking for a cors_domain entry in moonraker.conf
#   if [ ! "$(grep "^cors_domains:$" $mr_conf)" ]; then
#     #find trusted_clients line number and subtract one, to insert cors_domains later
#     line="$(grep -n "^trusted_clients:$" $mr_conf | cut -d":" -f1)i"
#     sed -i "$line cors_domains:" $mr_conf && mr_restart="true"
#   fi
#   if [ "$(grep "^cors_domains:$" $mr_conf)" ]; then
#     hostname=$(hostname -I | cut -d" " -f1)
#     url1="\ \ \ \ http://*.local"
#     url2="\ \ \ \ http://app.fluidd.xyz"
#     url3="\ \ \ \ https://app.fluidd.xyz"
#     url4="\ \ \ \ http://$hostname:*"
#     #find cors_domains line number and add one, to insert urls later
#     line="$(expr $(grep -n "cors_domains:" $mr_conf | cut -d":" -f1) + 1)i"
#     [ ! "$(grep -E '^\s+http:\/\/\*\.local$' $mr_conf)" ] && sed -i "$line $url1" $mr_conf && mr_restart="true"
#     [ ! "$(grep -E '^\s+http:\/\/app\.fluidd\.xyz$' $mr_conf)" ] && sed -i "$line $url2" $mr_conf && mr_restart="true"
#     [ ! "$(grep -E '^\s+https:\/\/app\.fluidd\.xyz$' $mr_conf)" ] && sed -i "$line $url3" $mr_conf && mr_restart="true"
#     [ ! "$(grep -E '^\s+http:\/\/([0-9]{1,3}\.){3}[0-9]{1,3}' $mr_conf)" ] && sed -i "$line $url4" $mr_conf && mr_restart="true"
#   fi
#   #restart moonraker service if mr_restart was set to true
#   if [[ $mr_restart == "true" ]]; then
#     ok_msg "Patching done!" && restart_moonraker
#   else
#     ok_msg "No patching was needed!"
#   fi
# }
