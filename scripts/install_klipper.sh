install_klipper(){
  if [ -e /etc/init.d/klipper ] && [ -e /etc/default/klipper ]; then
    ERROR_MSG=" Looks like Klipper is already installed!\n Skipping ..."
  else
    #check for dependencies
    dep=(git)
    dependency_check
    #execute operation
    cd ${HOME}
    status_msg "Cloning Klipper repository ..."
    git clone $KLIPPER_REPO && ok_msg "Klipper successfully cloned!"
    status_msg "Installing Klipper Service ..."
    $KLIPPER_DIR/scripts/install-octopi.sh && sleep 2 && ok_msg "Klipper installation complete!"
    #create a klippy.log symlink in home-dir just for convenience
    if [ ! -e ${HOME}/klippy.log ]; then
      status_msg "Creating klippy.log Symlink ..."
      ln -s /tmp/klippy.log ${HOME}/klippy.log && ok_msg "Symlink created!"
    fi
    while true; do
      echo -e "${cyan}"
      read -p "###### Do you want to flash your MCU now? (Y/n): " yn
      echo -e "${default}"
      case "$yn" in
        Y|y|Yes|yes|"") build_fw && flash_routine; break;;
        N|n|No|no) break;;
    esac
  done
  fi
}