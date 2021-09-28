check_for_backup_dir(){
  if [ ! -d $BACKUP_DIR ]; then
    status_msg "Create KIAUH backup directory ..."
    mkdir -p $BACKUP_DIR && ok_msg "Directory created!"
  fi
}

toggle_backups(){
  source_kiauh_ini
  if [ "$backup_before_update" = "true" ]; then
    sed -i '/backup_before_update=/s/true/false/' $INI_FILE
    BB4U_STATUS="${green}[Enable]${default} backups before updating                  "
    CONFIRM_MSG=" Backups before updates are now >>> DISABLED <<< !"
  fi
  if [ "$backup_before_update" = "false" ]; then
    sed -i '/backup_before_update=/s/false/true/' $INI_FILE
    BB4U_STATUS="${red}[Disable]${default} backups before updating                 "
    CONFIRM_MSG=" Backups before updates are now >>> ENABLED <<< !"
  fi
}

bb4u(){
  source_kiauh_ini
  if [ "$backup_before_update" = "true" ]; then
    backup_$1
  fi
}

read_bb4u_stat(){
  source_kiauh_ini
  if [ ! "$backup_before_update" = "true" ]; then
    BB4U_STATUS="${green}[Enable]${default} backups before updating                  "
  else
    BB4U_STATUS="${red}[Disable]${default} backups before updating                 "
  fi
}

################################################################################
#******************************************************************************#
################################################################################

backup_printer_cfg(){
  check_for_backup_dir
  if [ -f $PRINTER_CFG ]; then
    get_date
    status_msg "Timestamp: $current_date"
    status_msg "Create backup of printer.cfg ..."
    cp $PRINTER_CFG $BACKUP_DIR/printer.cfg."$current_date".backup && ok_msg "Backup complete!"
  else
    ok_msg "No printer.cfg found! Skipping backup ..."
  fi
}

backup_klipper_config_dir(){
  source_kiauh_ini
  check_for_backup_dir
  if [ -d "$klipper_cfg_loc" ]; then
    get_date
    status_msg "Timestamp: $current_date"
    status_msg "Create backup of the Klipper config directory ..."
    config_folder_name="$(echo "$klipper_cfg_loc" | rev | cut -d"/" -f1 | rev)"
    mkdir -p $BACKUP_DIR/$config_folder_name/$current_date
    cp -r "$klipper_cfg_loc" "$_" && ok_msg "Backup complete!"
    echo
  else
    ok_msg "No config directory found! Skipping backup ..."
    echo
  fi
}

backup_moonraker_database(){
  check_for_backup_dir
  if ls -d ${HOME}/.moonraker_database* 2>/dev/null 1>&2; then
    get_date
    status_msg "Timestamp: $current_date"
    mkdir -p "$BACKUP_DIR/mr_db_backup/$current_date"
    for database in $(ls -d ${HOME}/.moonraker_database*)
    do
      status_msg "Create backup of $database ..."
      cp -r $database "$BACKUP_DIR/mr_db_backup/$current_date"
      ok_msg "Done!"
    done
    ok_msg "Backup complete!\n"
  else
    ok_msg "No Moonraker database found! Skipping backup ..."
  fi
}

backup_klipper(){
  if [ -d $KLIPPER_DIR ] && [ -d $KLIPPY_ENV ]; then
    status_msg "Creating Klipper backup ..."
    check_for_backup_dir
    get_date
    status_msg "Timestamp: $current_date"
    mkdir -p $BACKUP_DIR/klipper-backups/"$current_date"
    cp -r $KLIPPER_DIR $_ && cp -r $KLIPPY_ENV $_ && ok_msg "Backup complete!"
  else
    ERROR_MSG=" Can't backup klipper and/or klipper-env directory! Not found!"
  fi
}

backup_dwc2(){
  if [ -d $DWC2FK_DIR ] && [ -d $DWC_ENV_DIR ] && [ -d $DWC2_DIR ]; then
    status_msg "Creating DWC2 Web UI backup ..."
    check_for_backup_dir
    get_date
    status_msg "Timestamp: $current_date"
    mkdir -p $BACKUP_DIR/dwc2-backups/"$current_date"
    cp -r $DWC2FK_DIR $_ && cp -r $DWC_ENV_DIR $_ && cp -r $DWC2_DIR $_
    ok_msg "Backup complete!"
  else
    ERROR_MSG=" Can't backup dwc2-for-klipper-socket and/or dwc2 directory!\n Not found!"
  fi
}

backup_mainsail(){
  if [ -d $MAINSAIL_DIR ]; then
    status_msg "Creating Mainsail backup ..."
    check_for_backup_dir
    get_date
    status_msg "Timestamp: $current_date"
    mkdir -p $BACKUP_DIR/mainsail-backups/"$current_date"
    cp -r $MAINSAIL_DIR $_ && ok_msg "Backup complete!"
  else
    ERROR_MSG=" Can't backup mainsail directory! Not found!"
  fi
}

backup_fluidd(){
  if [ -d $FLUIDD_DIR ]; then
    status_msg "Creating Fluidd backup ..."
    check_for_backup_dir
    get_date
    status_msg "Timestamp: $current_date"
    mkdir -p $BACKUP_DIR/fluidd-backups/"$current_date"
    cp -r $FLUIDD_DIR $_ && ok_msg "Backup complete!"
  else
    ERROR_MSG=" Can't backup fluidd directory! Not found!"
  fi
}

backup_moonraker(){
  if [ -d $MOONRAKER_DIR ] && [ -d $MOONRAKER_ENV ]; then
    status_msg "Creating Moonraker backup ..."
    check_for_backup_dir
    get_date
    status_msg "Timestamp: $current_date"
    mkdir -p $BACKUP_DIR/moonraker-backups/"$current_date"
    cp -r $MOONRAKER_DIR $_ && cp -r $MOONRAKER_ENV $_ && ok_msg "Backup complete!"
  else
    ERROR_MSG=" Can't backup moonraker and/or moonraker-env directory! Not found!"
  fi
}

backup_octoprint(){
  if [ -d $OCTOPRINT_DIR ] && [ -d $OCTOPRINT_CFG_DIR ]; then
    status_msg "Creating OctoPrint backup ..."
    check_for_backup_dir
    get_date
    status_msg "Timestamp: $current_date"
    mkdir -p $BACKUP_DIR/octoprint-backups/"$current_date"
    cp -r $OCTOPRINT_DIR $_ && cp -r $OCTOPRINT_CFG_DIR $_
    ok_msg "Backup complete!"
  else
    ERROR_MSG=" Can't backup OctoPrint and/or .octoprint directory!\n Not found!"
  fi
}

backup_klipperscreen(){
  if [ -d $KLIPPERSCREEN_DIR ] ; then
    status_msg "Creating KlipperScreen backup ..."
    check_for_backup_dir
    get_date
    status_msg "Timestamp: $current_date"
    mkdir -p $BACKUP_DIR/klipperscreen-backups/"$current_date"
    cp -r $KLIPPERSCREEN_DIR $_
    ok_msg "Backup complete!"
  else
    ERROR_MSG=" Can't backup KlipperScreen directory!\n Not found!"
  fi
}

backup_MoonrakerTelegramBot(){
  if [ -d $MOONRAKER_TELEGRAM_BOT_DIR ] ; then
    status_msg "Creating MoonrakerTelegramBot backup ..."
    check_for_backup_dir
    get_date
    status_msg "Timestamp: $current_date"
    mkdir -p $BACKUP_DIR/MoonrakerTelegramBot-backups/"$current_date"
    cp -r $MOONRAKER_TELEGRAM_BOT_DIR $_
    ok_msg "Backup complete!"
  else
    ERROR_MSG=" Can't backup MoonrakerTelegramBot directory!\n Not found!"
  fi
}
