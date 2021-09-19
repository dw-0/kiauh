install_MoonrakerTelegramBot(){
    source_kiauh_ini
    system_check_MoonrakerTelegramBot
    #ask user for customization
    get_user_selections_MoonrakerTelegramBot
    #MoonrakerTelegramBot main installation
    MoonrakerTelegramBot_setup
    #after install actions
    restart_MoonrakerTelegramBot
}

MoonrakerTelegramBot_setup(){
  dep=(virtualenv)
  dependency_check
  status_msg "Downloading MoonrakerTelegramBot ..."
  #force remove existing MoonrakerTelegramBot dir
  [ -d $MOONRAKERTELEGRAMBOT_DIR ] && rm -rf $MOONRAKERTELEGRAMBOT_DIR
  #clone into fresh MoonrakerTelegramBot dir
  cd ${HOME} && git clone $NLEF_REPO
  ok_msg "Download complete!"
  status_msg "Installing MoonrakerTelegramBot ..."
  $MOONRAKERTELEGRAMBOT_DIR/scripts/install.sh 
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
