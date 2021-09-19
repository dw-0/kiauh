install_MoonrakerTelegramBot(){
    source_kiauh_ini
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
