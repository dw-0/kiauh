##############################################################################################
#********************************************************************************************#
##############################################################################################

### base variables
SYSTEMDDIR="/etc/systemd/system"
DWC_ENV="${HOME}/dwc-env"
DWC2_DIR="${HOME}/sdcard/web"

system_check_dwc2(){
  ### check system for an installed octoprint service
  if systemctl is-enabled octoprint.service -q 2>/dev/null; then
    OCTOPRINT_ENABLED="true"
  fi
}

dwc_setup_dialog(){
  status_msg "Initializing DWC2 installation ..."

  ### check system for several requirements before initializing the dwc2 installation
  system_check_dwc2

  ### check for existing klipper service installations
  if [ ! "$(systemctl list-units --full -all -t service --no-legend | grep -F "klipper.service")" ] && [ ! "$(systemctl list-units --full -all -t service --no-legend | grep -E "klipper-[[:digit:]].service")" ]; then
    ERROR_MSG="Klipper service not found, please install Klipper first!" && return 0
  fi

  ### count amount of klipper services
  if [ "$(systemctl list-units --full -all -t service --no-legend | grep -F "klipper.service")" ]; then
    INSTANCE_COUNT=1
  else
    INSTANCE_COUNT=$(systemctl list-units --full -all -t service --no-legend | grep -E "klipper-[[:digit:]].service" | wc -l)
  fi

  ### initial config path check
  check_klipper_cfg_path

  ### ask user how to handle OctoPrint, Haproxy and Lighttpd
  process_octoprint_dialog_dwc2
  process_haproxy_lighttpd_dialog

  ### instance confirmation dialog
  while true; do
      echo
      top_border
      if [ $INSTANCE_COUNT -gt 1 ]; then
        printf "|%-55s|\n" " $INSTANCE_COUNT Klipper instances were found!"
      else
        echo -e "| 1 Klipper instance was found!                         | "
      fi
      echo -e "| You need one DWC instance per Klipper instance.       | "
      bottom_border
      echo
      read -p "${cyan}###### Create $INSTANCE_COUNT DWC instances? (Y/n):${default} " yn
      case "$yn" in
        Y|y|Yes|yes|"")
          echo -e "###### > Yes"
          status_msg "Creating $INSTANCE_COUNT DWC instances ..."
          dwc_setup
          break;;
        N|n|No|no)
          echo -e "###### > No"
          warn_msg "Exiting DWC setup ..."
          echo
          break;;
        *)
          print_unkown_cmd
          print_msg && clear_msg;;
    esac
  done
}

###TODO for future: should be some kind of shared function between moonraker and this installer, since it does the same
process_octoprint_dialog_dwc2(){
  ### ask user to disable octoprint when its service was found
  if [ "$OCTOPRINT_ENABLED" = "true" ]; then
    while true; do
      echo
      top_border
      echo -e "|       ${red}!!! WARNING - OctoPrint service found !!!${default}       |"
      hr
      echo -e "|  You might consider disabling the OctoPrint service,  |"
      echo -e "|  since an active OctoPrint service may lead to unex-  |"
      echo -e "|  pected behavior of Duet Web Control for Klipper.     |"
      bottom_border
      read -p "${cyan}###### Do you want to disable OctoPrint now? (Y/n):${default} " yn
      case "$yn" in
        Y|y|Yes|yes|"")
          echo -e "###### > Yes"
          status_msg "Stopping OctoPrint ..."
          sudo systemctl stop octoprint && ok_msg "OctoPrint service stopped!"
          status_msg "Disabling OctoPrint ..."
          sudo systemctl disable octoprint && ok_msg "OctoPrint service disabled!"
          break;;
        N|n|No|no)
          echo -e "###### > No"
          break;;
        *)
          print_unkown_cmd
          print_msg && clear_msg;;
      esac
    done
  fi
  status_msg "Installation will start now! Please wait ..."
}

#############################################################
#############################################################

get_dwc_ver(){
  DWC2_VERSION=$(curl -s https://api.github.com/repositories/28820678/releases/latest | grep tag_name | cut -d'"' -f4)
}

dwc_setup(){
  ### check dependencies
  dep=(git wget gzip tar curl)
  dependency_check

  ### step 1: get dwc2-for-klipper
  status_msg "Downloading DWC2-for-Klipper-Socket ..."
  cd ${HOME} && git clone $DWC2FK_REPO
  ok_msg "Download complete!"

  ### step 2: install dwc2 dependencies and create python virtualenv
  status_msg "Installing dependencies ..."
  install_dwc_packages
  create_dwc_virtualenv

  ### step 3: download Duet Web Control
  download_dwc_webui

  ### step 4: create dwc instances
  INSTANCE=1
  if [ $INSTANCE_COUNT -eq $INSTANCE ]; then
    create_single_dwc_instance
  else
    #create_multi_dwc_instance
    warn_msg "Sorry, at the moment only single instance installations are supported!"
  fi
}

download_dwc_webui(){
  #get Duet Web Control
  GET_DWC2_URL=$(curl -s https://api.github.com/repositories/28820678/releases/latest | grep browser_download_url | cut -d'"' -f4)
  status_msg "Downloading DWC2 Web UI ..."
  [ ! -d $DWC2_DIR ] && mkdir -p $DWC2_DIR
  cd $DWC2_DIR && wget $GET_DWC2_URL
  ok_msg "Download complete!"
  status_msg "Unzipping archive ..."
  unzip -q -o *.zip
  for f_ in $(find . | grep '.gz')
  do
    gunzip -f ${f_}
  done
  ok_msg "Done!"
  status_msg "Writing DWC version to file ..."
  echo $GET_DWC2_URL | cut -d/ -f8 > $DWC2_DIR/.version
  ok_msg "Done!"
  status_msg "Do a little cleanup ..."
  rm -rf DuetWebControl-SD.zip
  ok_msg "Done!"
  ok_msg "DWC2 Web UI installed!"
}

##############################################################################################
#********************************************************************************************#
##############################################################################################

install_dwc_packages()
{
    PKGLIST="python3-virtualenv python3-dev python3-tornado"

    # Update system package info
    status_msg "Running apt-get update..."
    sudo apt-get update

    # Install desired packages
    status_msg "Installing packages..."
    sudo apt-get install --yes ${PKGLIST}
}

create_dwc_virtualenv()
{
    status_msg "Installing python virtual environment..."

    # Create virtualenv if it doesn't already exist
    [ ! -d ${DWC_ENV} ] && virtualenv -p /usr/bin/python3 ${DWC_ENV}

    # Install/update dependencies
    ${DWC_ENV}/bin/pip install tornado==6.0.4
}

create_single_dwc_startscript(){
### create systemd service file
sudo /bin/sh -c "cat > ${SYSTEMDDIR}/dwc.service" << DWC
#Systemd service file for DWC
[Unit]
Description=dwc_webif
After=network.target
[Install]
WantedBy=multi-user.target
[Service]
Type=simple
User=${USER}
RemainAfterExit=yes
ExecStart=${DWC_ENV}/bin/python3 ${DWC2FK_DIR}/web_dwc2.py
Restart=always
RestartSec=10
DWC
}

create_multi_dwc_startscript(){
  ###! atm not possible due to hardcoded log and config files used by dwc2-for-klipper-socket!
  ###! either needs a PR to read start-arguments passed over by the service file or
  ###! every instance needs its own copy of dwc2-for-klipper-socket with a modifief web_dwc2.py
  ###! on line 223, 228 and probably 217 as well
}

##############################################################################################
#********************************************************************************************#
##############################################################################################

print_dwc_ip_list(){
  i=1
  for ip in ${dwc_ip_list[@]}; do
    echo -e "       ${cyan}● Instance $i:${default} $ip"
    i=$((i + 1))
  done
}

create_single_dwc_instance(){
  status_msg "Setting up 1 Duet Web Control instance ..."

  ### single instance variables
  PORT=4750
  DWC_LOG=/tmp/dwc.log

  ### declare empty array for ips which get displayed to the user at the end of the setup
  HOSTNAME=$(hostname -I | cut -d" " -f1)
  dwc_ip_list=()

  ### create instance
  status_msg "Creating single DWC instance ..."
  create_single_dwc_startscript

  ### write the ip and port to the ip list for displaying it later to the user
  dwc_ip_list+=("$HOSTNAME:$PORT")

  ### enable instance
  sudo systemctl enable dwc.service
  ok_msg "Single DWC instance created!"

  ### launching instance
  status_msg "Launching DWC instance ..."
  sudo systemctl start dwc

  ### confirm message
  CONFIRM_MSG="Single DWC instance has been set up!"
  print_msg && clear_msg

  ### display moonraker ip to the user
  print_dwc_ip_list; echo
}

create_multi_dwc_instance(){
  ###! atm not possible due to hardcoded log and config files used by dwc2-for-klipper-socket!
  ###! either needs a PR to read start-arguments passed over by the service file or
  ###! every instance needs its own copy of dwc2-for-klipper-socket with a modifief web_dwc2.py
  ###! on line 223, 228 and probably 217 as well
}