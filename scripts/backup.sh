backup_printer_cfg(){
  if [ ! -d $BACKUP_DIR ]; then
    status_msg "Create backup directory ..."
    mkdir -p $BACKUP_DIR && ok_msg "Directory created!"
  fi
  if [ -f $PRINTER_CFG ]; then
    get_date
    status_msg "Create backup of printer.cfg ..."
    cp $PRINTER_CFG $BACKUP_DIR/printer.cfg."$current_date".backup && ok_msg "Backup created!"
  else
    ok_msg "No printer.cfg found! Skipping backup ..."
  fi
}

read_bb4u_stat(){
  source_ini
  if [ ! "$backup_before_update" = "true" ]; then
    BB4U_STATUS="${green}[Enable]${default} backups before updating                  "
  else
    BB4U_STATUS="${red}[Disable]${default} backups before updating                 "
  fi
}

toggle_backups(){
  source_ini
  if [ "$backup_before_update" = "true" ]; then
    sed -i '/backup_before_update=/s/true/false/' $INI_DIR
    BB4U_STATUS="${green}[Enable]${default} backups before updating                  "
    CONFIRM_MSG=" Backups before updates are now >>> DISABLED <<< !"
  fi
  if [ "$backup_before_update" = "false" ]; then
    sed -i '/backup_before_update=/s/false/true/' $INI_DIR
    BB4U_STATUS="${red}[Disable]${default} backups before updating                 "
    CONFIRM_MSG=" Backups before updates are now >>> ENABLED <<< !"
  fi
}

bb4u_klipper(){
  source_ini
  if [ -d $KLIPPER_DIR ] && [ "$backup_before_update" = "true" ]; then
    get_date
    status_msg "Creating Klipper backup ..."
    mkdir -p $BACKUP_DIR/klipper-backups/"$current_date"
    cp -r $KLIPPER_DIR $_ && cp -r $KLIPPY_ENV_DIR $_ && ok_msg "Backup complete!"
  fi
}

bb4u_dwc2fk(){
  source_ini
  if [ -d $DWC2FK_DIR ] && [ "$backup_before_update" = "true" ]; then
    get_date
    status_msg "Creating DWC2-for-Klipper backup ..."
    mkdir -p $BACKUP_DIR/dwc2-for-klipper-backups/"$current_date"
    cp -r $DWC2FK_DIR $_ && ok_msg "Backup complete!"
  fi
}

bb4u_dwc2(){
  source_ini
  if [ -d $DWC2_DIR ] && [ "$backup_before_update" = "true" ]; then
    get_date
    status_msg "Creating DWC2 Web UI backup ..."
    mkdir -p $BACKUP_DIR/dwc2-backups/"$current_date"
    cp -r $DWC2_DIR $_ && ok_msg "Backup complete!"
  fi
}

bb4u_mainsail(){
  source_ini
  if [ -d $MAINSAIL_DIR ] && [ "$backup_before_update" = "true" ]; then
    get_date
    status_msg "Creating Mainsail backup ..."
    mkdir -p $BACKUP_DIR/mainsail-backups/"$current_date"
    cp -r $MAINSAIL_DIR $_ && ok_msg "Backup complete!"
  fi
}