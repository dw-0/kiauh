install_klipperscreen(){
  python3_check
  if [ $py_chk_ok = "true" ]; then
    source_kiauh_ini
    system_check_klipperscreen
    #ask user for customization
    get_user_selections_klipperscreen
    #KlipperScreen main installation
    klipperscreen_setup
    #execute customizations
    symlinks_klipperscreen
    #after install actions
    restart_klipperscreen
  else
    ERROR_MSG="Python 3.7 or above required!\n Please upgrade your Python version first."
    print_msg && clear_msg
  fi
}

python3_check(){
  status_msg "Your Python 3 version is: $(python3 --version)"
  major=$(python3 --version | cut -d" " -f2 | cut -d"." -f1)
  minor=$(python3 --version | cut -d"." -f2)
  if [ $major -ge 3 ] && [ $minor -ge 7 ]; then
    ok_msg "Python version ok!"
    py_chk_ok="true"
  else
    py_chk_ok="false"
  fi
}

system_check_klipperscreen(){
  if [ ! -e ${HOME}/klipper_config/KlipperScreen.log ]; then
    KLIPPERSCREEN_SL_FOUND="false"
  else
    KLIPPERSCREEN_SL_FOUND="true"
  fi
}

get_user_selections_klipperscreen(){
  #user selection for KlipperScreen.log symlink
  if [ "$KLIPPERSCREEN_SL_FOUND" = "false" ]; then
    while true; do
      echo
      read -p "${cyan}###### Create KlipperScreen.log symlink? (y/N):${default} " yn
      case "$yn" in
        Y|y|Yes|yes)
          echo -e "###### > Yes"
          SEL_KSLOG_SL="true"
          break;;
        N|n|No|no|"")
          echo -e "###### > No"
          SEL_KSLOG_SL="false"
          break;;
        *)
          print_unkown_cmd
          print_msg && clear_msg;;
      esac
    done
  fi
}

klipperscreen_setup(){
  dep=(wget curl unzip dfu-util)
  dependency_check
  status_msg "Downloading KlipperScreen ..."
  #force remove existing KlipperScreen dir
  [ -d $KLIPPERSCREEN_DIR ] && rm -rf $KLIPPERSCREEN_DIR
  #clone into fresh KlipperScreen dir
  cd ${HOME} && git clone $KLIPPERSCREEN_REPO
  ok_msg "Download complete!"
  status_msg "Installing KlipperScreen ..."
  $KLIPPERSCREEN_DIR/scripts/KlipperScreen-install.sh
  echo; ok_msg "KlipperScreen successfully installed!"
}

symlinks_klipperscreen(){
  #create a KlipperScreen.log symlink in klipper_config-dir just for convenience
  if [ "$SEL_KSLOG_SL" = "true" ] && [ ! -e $klipper_cfg_loc/KlipperScreen.log ]; then
    status_msg "Creating KlipperScreen.log symlink ..."
    ln -s /tmp/KlipperScreen.log $klipper_cfg_loc
    ok_msg "Symlink created!"
  fi
}
