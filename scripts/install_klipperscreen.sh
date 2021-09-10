install_klipperscreen(){
  python3_check
  if [ $py_chk_ok = "true" ]; then
    source_kiauh_ini
    #KlipperScreen main installation
    klipperscreen_setup
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

klipperscreen_setup(){
  dep=(wget curl unzip dfu-util)
  dependency_check
  status_msg "Downloading KlipperScreen ..."
  # force remove existing KlipperScreen dir
  [ -d $KLIPPERSCREEN_DIR ] && rm -rf $KLIPPERSCREEN_DIR
  # clone into fresh KlipperScreen dir
  cd ${HOME} && git clone $KLIPPERSCREEN_REPO
  ok_msg "Download complete!"
  status_msg "Installing KlipperScreen ..."
  $KLIPPERSCREEN_DIR/scripts/KlipperScreen-install.sh
  ok_msg "KlipperScreen successfully installed!"
}
