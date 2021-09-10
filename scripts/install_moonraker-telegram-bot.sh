install_MoonrakerTelegramBot(){
    source_kiauh_ini
    system_check_MoonrakerTelegramBot
    #ask user for customization
    get_user_selections_MoonrakerTelegramBot
    #MoonrakerTelegramBot main installation
    MoonrakerTelegramBot_setup
    #execute customizations
    symlinks_MoonrakerTelegramBot
    #after install actions
    restart_MoonrakerTelegramBot
}

system_check_MoonrakerTelegramBot(){
  source_kiauh_ini
  if [ ! -e $klipper_cfg_loc/telegram.log ]; then
    MOONRAKERTELEGRAMBOT_SL_FOUND="false"
  else
    MOONRAKERTELEGRAMBOT_SL_FOUND="true"
  fi
}

get_user_selections_MoonrakerTelegramBot(){
  #user selection for telegram.log symlink
  if [ "$KMOONRAKERTELEGRAMBOT_SL_FOUND" = "false" ]; then
    while true; do
      echo
      read -p "${cyan}###### Create telegram.log symlink? (y/N):${default} " yn
      case "$yn" in
        Y|y|Yes|yes)
          echo -e "###### > Yes"
          SEL_MTBLOG_SL="true"
          break;;
        N|n|No|no|"")
          echo -e "###### > No"
          SEL_MTBLOG_SL="false"
          break;;
        *)
          print_unkown_cmd
          print_msg && clear_msg;;
      esac
    done
  fi
}

MoonrakerTelegramBot_setup(){
  status_msg "Downloading MoonrakerTelegramBot ..."
  #force remove existing MoonrakerTelegramBot dir
  [ -d $MOONRAKERTELEGRAMBOT_DIR ] && rm -rf $MOONRAKERTELEGRAMBOT_DIR
  #clone into fresh MoonrakerTelegramBot dir
  cd ${HOME} && git clone $NLEF_REPO
  ok_msg "Download complete!"
  status_msg "Installing MoonrakerTelegramBot ..."
  $MOONRAKERTELEGRAMBOT_DIR/install.sh
  echo; ok_msg "MoonrakerTelegramBot successfully installed!"
}

symlinks_MoonrakerTelegramBot(){
  #create a telegram.log symlink in klipper_config-dir
  if [ "$SEL_MTBLOG_SL" = "true" ] && [ ! -e $klipper_cfg_loc/telegram.log ]; then
    status_msg "Creating telegram.log symlink ..."
    ln -s /tmp/telegram.log $klipper_cfg_loc
    ok_msg "Symlink created!"
  fi
}
