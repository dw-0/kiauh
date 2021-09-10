install_moonraker-telegram-bot(){
    source_kiauh_ini
    system_check_moonraker-telegram-bot
    #ask user for customization
    get_user_selections_moonraker-telegram-bot
    #moonraker-telegram-bot main installation
    moonraker-telegram-bot_setup
    #execute customizations
    symlinks_moonraker-telegram-bot
    #after install actions
    restart_moonraker-telegram-bot
}

system_check_moonraker-telegram-bot(){
  source_kiauh_ini
  if [ ! -e $klipper_cfg_loc/telegram.log ]; then
    MOONRAKERTELEGRAMBOT_SL_FOUND="false"
  else
    MOONRAKERTELEGRAMBOT_SL_FOUND="true"
  fi
}

get_user_selections_moonraker-telegram-bot(){
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

moonraker-telegram-bot_setup(){
  dep=(wget curl unzip dfu-util)
  dependency_check
  status_msg "Downloading moonraker-telegram-bot ..."
  #force remove existing moonraker-telegram-bot dir
  [ -d $MOONRAKERTELEGRAMBOT_DIR ] && rm -rf $MOONRAKERTELEGRAMBOT_DIR
  #clone into fresh moonraker-telegram-bot dir
  cd ${HOME} && git clone $MOONRAKERTELEGRAMBOT_REPO
  ok_msg "Download complete!"
  status_msg "Installing moonraker-telegram-bot ..."
  $MOONRAKERTELEGRAMBOT_DIR/install.sh
  echo; ok_msg "moonraker-telegram-bot successfully installed!"
}

symlinks_moonraker-telegram-bot(){
  #create a telegram.log symlink in klipper_config-dir
  if [ "$SEL_MTBLOG_SL" = "true" ] && [ ! -e $klipper_cfg_loc/telegram.log ]; then
    status_msg "Creating telegram.log symlink ..."
    ln -s /tmp/telegram.log $klipper_cfg_loc
    ok_msg "Symlink created!"
  fi
}
