#!/bin/bash
clear
set -e

### init color variables
green="\e[92m"
yellow="\e[93m"
red="\e[91m"
cyan="\e[96m"
default="\e[39m"

### setup repos
KLIPPER_REPO=https://github.com/KevinOConnor/klipper.git
#DWC2FK_REPO=https://github.com/Stephan3/dwc2-for-klipper.git
#DWC2FK_REPO=https://github.com/pluuuk/dwc2-for-klipper.git
DWC2FK_REPO=https://github.com/th33xitus/dwc2-for-klipper.git

## setup some file and folder paths
KLIPPER_DIR=${HOME}/klipper
DWC2FK_DIR=${HOME}/dwc2-for-klipper
DWC2FK_SYSDIR=${HOME}/klippy-env/lib/python2.7/site-packages/tornado
DWC2_DIR=${HOME}/sdcard/dwc2
BACKUP_DIR=${HOME}/backup
CFG_FILE=${HOME}/printer.cfg
KLIPPER_SYSFILE1=/etc/init.d/klipper
KLIPPER_SYSFILE2=/etc/default/klipper

print_header(){
    echo -e "###################################################"
    echo -e "##   $(title_msg "> > > > > > > > > KIAUH < < < < < < < < <")   ##"
    echo -e "##    $(title_msg "Klipper Installation And Update Helper")     ##"
    echo -e "## --------------------------------------------- ##"
    echo -e "##          Install, update and backup:          ##"
    echo -e "##   Klipper | DWC2-for-Klipper | DWC2 web UI    ##"
    echo -e "## --------------------------------------------- ##"
    echo -e "##                 by th33xitus                  ##"
    echo -e "##             credits to: lixxbox               ##"
    echo -e "###################################################"
}

main_menu(){
    echo
    echo -e "/=================================================\ "
    echo -e "|  $(title_msg "Please choose the action you want to perform:")  |"
    echo -e "|-------------------------------------------------|"
    echo -e "| 0) Check system status                          |"
    echo -e "|                                                 |"
    echo -e "| 1) ${green}[Install]${default}    2) ${yellow}[Advanced]${default}    3) ${red}[Uninstall]${default} |"
    echo -e "|------------------------+------------------------|"
    echo -e "|         Update         |         Backup         |"
    echo -e "|------------------------+------------------------|"
    echo -e "| 4) Update all          |  8) Backup all         |"
    echo -e "| 5) Klipper             |  9) Klipper            |"
    echo -e "| 6) dwc2-for-klipper    | 10) dwc2-for-klipper   |"
    echo -e "| 7) DWC2                | 11) DWC2               |"
    echo -e "|------------------------+------------------------|"
    echo -e "|                     $(warn_msg "Q) Quit")                     |"
    echo -e "\=================================================/"
    read -p "Perform action: " action; echo
    action
}

### declare some functions
warn_msg(){
    echo -e "${red}$1${default}"
}
status_msg(){
    echo -e "${yellow}## $1${default}"
}
confirm_msg(){
    echo -e "${green}>> $1${default}"
}
title_msg(){
    echo -e "${cyan}$1${default}"
}
get_date(){
    current_date=`date +"%Y-%m-%d_%H%M%S"`
}

### checking for root
check_euid(){
    if [ "$EUID" -eq 0 ]
    then
        echo -e "/=================================================\ "
        echo -e "|          $(warn_msg "DON'T RUN THIS SCRIPT AS ROOT!")         |"
        echo -e "\=================================================/ "; exit 1
    fi
}

### checking for existing installations on startup
start_check(){
    check_files
    echo; status_msg "Klipper installation: $klipper_status"
    echo; status_msg "DWC2 web UI installation: $dwc2_status"
    echo; status_msg "DWC2-for-Klipper installation: $dwc2fk_status"
}
check_files(){
    if [[ -f $KLIPPER_SYSFILE1 && -f $KLIPPER_SYSFILE2 ]]
    then
        if [ -d $KLIPPER_DIR ]
        then
            klipper_status="${green}Found!${default}"
        else
            klipper_status="${yellow}Incomplete!${default}"
        fi
    else
        klipper_status="${red}Not found!${default}"
    fi
    if [ -d $DWC2FK_SYSDIR ]
    then
        if [ -d $DWC2FK_DIR ]
        then
            dwc2fk_status="${green}Found!${default}"
        else
            dwc2fk_status="${yellow}Incomplete!${default}"
        fi
    else
        dwc2fk_status="${red}Not found!${default}"
    fi
    if [ -d $DWC2_DIR/web ]
    then
        dwc2_status="${green}Found!${default}"
    else
        dwc2_status="${red}Not found!${default}"
    fi
}

### functions for writing to printer.cfg
write_printid_cfg(){
    echo
    while true; do
        read -p "Do you want to write this ID to your printer.cfg now? (Y/n): " yn
        case "$yn" in
            Y|y|Yes|yes|"")
                backup_cfg
                echo -e "\n#############################\n### AUTO CREATED by KIAUH ###\n#############################\n[mcu]\nserial: $usb_id" >> $CFG_FILE
                echo; confirm_msg "Config written!"
                break
            ;;
            N|n|No|no)
                break
            ;;
            *)
                echo; warn_msg "Unknown parameter: $yn"
        esac
    done
}
write_dwc2fk_cfg(){
    echo
    while true; do
    echo -n -e "Do you want to write the configuration example\nto your printer.cfg? (Y/n): "
    read yn
    case "$yn" in
    Y|y|Yes|yes|"")
        backup_cfg
        echo -e "\n#############################\n### AUTO CREATED by KIAUH ###\n#############################\n[virtual_sdcard]\npath: ~/sdcard\n\n[web_dwc2]\n# optional - defaulting to Klipper\nprinter_name: Reiner Calmund\n# optional - defaulting to 127.0.0.1\nlisten_adress: 0.0.0.0\n# needed - use above 1024 as nonroot\nlisten_port: 4750\n#optional defaulting to dwc2/web. Its a folder relative to your virtual sdcard.\nweb_path: dwc2/web" >> $CFG_FILE
        echo; confirm_msg "Config written!"; echo; break
    ;;
    N|n|No|no)
        break
    ;;
    *)
        warn_msg "Unknown parameter: $yn"; echo
    esac
    done
}

### grab the printers id
get_usb_id(){
    echo; status_msg "Identifying the correct USB port ..."
    warn_msg "Make sure your printer is the only USB device connected!"
    usb_id=`ls /dev/serial/by-id/*`
    if [ -L /dev/serial/by-id/* ]
    then
        echo; status_msg "The ID of your printer is:"
        title_msg "$usb_id"; echo
    else
        echo; warn_msg "Could not retrieve ID!"
    fi
}

build_fw(){
    status_msg "--- Starting Klipper Firmware Configuration ---"
    if [ -d $KLIPPER_DIR ]
    then
        cd $KLIPPER_DIR && make menuconfig
        status_msg "Building firmware ..."
        make clean && make && confirm_msg "Firmware built!"
    else
        warn_msg "Can not build firmware without a Klipper directory!"
    fi
}

flash_routine(){
    echo; status_msg "--- Flashing MCU ---"
    echo
    echo -e "/=================================================\ "
    echo -e "|                    $(warn_msg "WARNING!")                     |"
    echo -e "| $(warn_msg "Flashing a Smoothie based board for the first")   |"
    echo -e "| $(warn_msg "time with this script will certainly fail".)      |"
    echo -e "| This applies to boards like the BTT SKR V1.3 or |"
    echo -e "| the newer SKR V1.4 and SKR V1.4 Turbo. You have |"
    echo -e "| to copy the firmware file to the microSD card   |"
    echo -e "| manually and rename it to 'firmware.bin'.       |"
    echo -e "| You find the file in: ~/klipper/out/klipper.bin |"
    echo -e "\=================================================/ "
    echo
    while true; do
        read -p "Do you want to continue? (Y/n): " yn
        case "$yn" in
            Y|y|Yes|yes|"")
            get_usb_id
            write_printid_cfg
            flash_mcu
            break
            ;;
            N|n|No|no) break;;
            *) warn_msg "Unknown parameter: $yn"; echo;;
        esac
    done
}

flash_mcu(){
    echo; status_msg "Stopping Klipper service ..."
    sudo service klipper stop && confirm_msg "Klipper service stopped!"; echo
    if ! make flash FLASH_DEVICE="$usb_id";
    then
        echo; warn_msg "Flashing failed!"
        warn_msg "Please read the log above!"
    else
        echo; confirm_msg "Flashing successfull!"
    fi
    echo; status_msg "Starting Klipper service ..."
    sudo service klipper start && confirm_msg "Klipper service started!"; echo
}

### check system for service, dirs, files and updates
system_check(){
    echo
    status_msg "--- Klipper service status:"
    if systemctl is-active -q klipper
    then
        confirm_msg "Klipper service running!"
    else
        if [ ! -f $KLIPPER_SYSFILE1 ]
        then
            warn_msg "Klipper service not installed!"
        else
            warn_msg "Klipper service inactive!"
        fi
    fi
    echo; status_msg "--- Klipper system files:"
    if [[ -f $KLIPPER_SYSFILE1 && -f $KLIPPER_SYSFILE2 ]]
    then
        confirm_msg "Klipper system files found!"
    else
        warn_msg "No Klipper system files were found!"
        warn_msg "Run the installer to create them."
    fi
    echo; status_msg "--- DWC2-for-Klipper system files:"
    if [ -d $DWC2FK_SYSDIR ]
    then
        confirm_msg "DWC2-for-Klipper system files found!"
    else
        warn_msg "No DWC2-for-Klipper system files (Tornado 5.1.1)\nwere found! Run the installer to create them."
    fi
    echo; status_msg "--- Klipper update check:"
    check_klipper_ver
    if [ -d $KLIPPER_DIR ]
    then
        if [ "$klipper_local_ver" == "$klipper_remote_ver" ]
        then
            confirm_msg "Klipper is up to date!"
        else
            warn_msg "Klipper is outdated!"
        fi
    fi
    echo; status_msg "--- DWC2-for-Klipper update check:"
    check_dwc2fk_ver
    if [ -d $DWC2FK_DIR ]
    then
        if [ "$dwc2fk_local_ver" == "$dwc2fk_remote_ver" ]
        then
            confirm_msg "DWC2-for-Klipper is up to date!"
        else
            warn_msg "DWC2-for-Klipper is outdated!"
        fi
    fi
    echo; status_msg "--- DWC2 update check:"
    check_dwc2_ver
    if [ -d $DWC2_DIR ]
    then
        if [ "$dwc2_remote_ver" == "$dwc2_local_ver" ]
        then
            confirm_msg "DWC2 is up to date!"
        else
            warn_msg "DWC2 is outdated!"
        fi
    fi
}
### version checks
check_klipper_ver(){
    if [ -d $KLIPPER_DIR ]
    then
        cd $KLIPPER_DIR
        git fetch -q
        klipper_local_ver=`git rev-parse --short=8 HEAD`
        klipper_remote_ver=`git rev-parse --short=8 origin/master`
        echo -e "Local : $klipper_local_ver"
        echo -e "Remote: $klipper_remote_ver"
    else
        warn_msg "No Klipper directory found!"
        warn_msg "Run Klipper update to create it."
    fi
}
check_dwc2fk_ver(){
    if [ -d $DWC2FK_DIR ]
    then
        cd $DWC2FK_DIR
        git fetch -q
        dwc2fk_local_ver=`git rev-parse --short=8 HEAD`
        dwc2fk_remote_ver=`git rev-parse --short=8 origin/master`
        echo -e "Local : $dwc2fk_local_ver"
        echo -e "Remote: $dwc2fk_remote_ver"
    else
        warn_msg "No DWC2-for-Klipper directory found!"
        warn_msg "Run DWC2-for-Klipper update to create it."
    fi
}
check_dwc2_ver(){
    if [ -d $DWC2_DIR/web ]
    then
        if [ -f $DWC2_DIR/web/version ]
        then
            dwc2_local_ver=`head -n 1 $DWC2_DIR/web/version`
            echo -e "Local : $dwc2_local_ver"
        else
            echo -e "Local : Can't read current version. Please update!"
        fi
        dwc2_remote_ver=`curl -s https://api.github.com/repositories/28820678/releases/latest | grep tag_name | cut -d'"' -f4`
        echo -e "Remote: $dwc2_remote_ver"
    else
        warn_msg "No DWC2 directory found!"
        warn_msg "Run DWC2 update to create it."
    fi
}

### install functions
inst_klipper(){
    if [[ -f $KLIPPER_SYSFILE1 || -f $KLIPPER_SYSFILE2 ]]
    then
        confirm_msg "Klipper is already installed!"
    else
        status_msg "--- Installing dependencies ---"
        sudo apt update && sudo apt install git wget gzip tar build-essential libjpeg8-dev imagemagick libv4l-dev cmake -y
        confirm_msg "Dependencies installed!"
        echo; status_msg "--- Installing Klipper ---"
        update_klipper
        cd $KLIPPER_DIR/scripts
        ./install-octopi.sh
        if systemctl is-active -q klipper
        then
        confirm_msg "Klipper service running!" && confirm_msg "Klipper successfully installed!"
        fi
        echo
        while true; do
            read -p "Do you want to flash your MCU now? (Y/n): " yn; echo
            case "$yn" in
            Y|y|Yes|yes|"")
            build_fw
            flash_routine
            break
            ;;
            N|n|No|no) break;;
            *) warn_msg "Unknown parameter: $yn"; echo;;
            esac
        done
    fi
}
inst_dwc2fk(){
    if [ -d $DWC2FK_SYSDIR ]
    then
        echo; confirm_msg "DWC2-for-Klipper system files (Tornado 5.1.1)\nare already installed!"
    else
        echo; status_msg "--- Installing DWC2-for-Klipper ---"
        if [ $(systemctl is-active klipper) = "active" ]
        then
            echo; status_msg "Stopping Klipper service ..."
            sudo systemctl stop klipper && confirm_msg "Klipper service stopped!"; echo
        fi
        echo; status_msg "Installing Tornado 5.1.1 ..."
        cd ${HOME}
        PYTHONDIR="${HOME}/klippy-env"
        virtualenv ${PYTHONDIR}
        ${PYTHONDIR}/bin/pip install tornado==5.1.1 && confirm_msg "Tornado 5.1.1 installed!"
        update_dwc2fk && confirm_msg "DWC2-for-Klipper installed!"
        write_dwc2fk_cfg
        if [ $(systemctl is-active klipper) = "inactive" ]
        then
            echo; status_msg "Starting Klipper service ..."
            sudo systemctl start klipper && confirm_msg "Klipper service running!"
        fi
    fi
}
inst_dwc2(){
    if [ -d $DWC2_DIR ]
    then
        echo; confirm_msg "DWC2 web UI is already installed!"
    else
        echo; status_msg "--- Installing DWC2 web UI ---"
        update_dwc2 && confirm_msg "DWC2 web UI installed!"
    fi
}
### update functions
update_full(){
    status_msg "Full update ..."
    update_klipper && confirm_msg "Klipper updated!"
    update_dwc2fk && confirm_msg "DWC2-for-Klipper updated!"
    update_dwc2 && confirm_msg "DWC2 web UI updated!"
}
update_klipper(){
    echo; status_msg "--- Klipper Update ---"
    if [ -f $KLIPPER_SYSFILE1 ]
    then
        echo; status_msg "Stopping Klipper service ..."
        sudo systemctl stop klipper && confirm_msg "Klipper service stopped!";echo
    fi
    if [ -d $KLIPPER_DIR ]
    then
        get_date
        mkdir -p $BACKUP_DIR/klipper-backup/"$current_date"
        mv $KLIPPER_DIR $_
    fi
    cd ${HOME} && git clone $KLIPPER_REPO
    if [ -f $DWC2FK_DIR/web_dwc2.py ]
    then
        echo; status_msg "Creating necessary symlink ..."
        ln -s $DWC2FK_DIR/web_dwc2.py $KLIPPER_DIR/klippy/extras/web_dwc2.py && confirm_msg "Symlink created!"
    fi
    if [ -f $KLIPPER_SYSFILE1 ]
    then
        echo; status_msg "Starting Klipper service ..."
        sudo systemctl start klipper && confirm_msg "Klipper service started!"
    fi
}
update_dwc2fk(){
    echo; status_msg "--- DWC2-for-Klipper Update ---"
    if [ -d $DWC2FK_DIR ]
    then
        get_date
        mkdir -p $BACKUP_DIR/dwc2fk-backup/"$current_date"
        mv $DWC2FK_DIR $_
    fi
    cd ${HOME} && git clone $DWC2FK_REPO
    if [[ -d $KLIPPER_DIR/klippy/extras && ! -f $KLIPPER_DIR/klippy/extras/web_dwc2.py ]]
    then
        echo; status_msg "Creating necessary symlink ..."
        ln -s $DWC2FK_DIR/web_dwc2.py $KLIPPER_DIR/klippy/extras/web_dwc2.py && confirm_msg "Symlink created!"
    fi
}
update_dwc2(){
    echo; status_msg "--- DWC2 web UI Update ---"
    get_url=`curl -s https://api.github.com/repositories/28820678/releases/latest | grep browser_download_url | cut -d'"' -f4`
    if [ -d $DWC2_DIR/web ]
    then
        get_date
        mkdir -p $BACKUP_DIR/dwc2-backup/"$current_date"/sdcard/dwc2/web/
        mv $DWC2_DIR/web/* $_
    else
        mkdir -p $DWC2_DIR/web
    fi
    cd $DWC2_DIR/web
    wget -q $get_url
    unzip -q *.zip && for f_ in $(find . | grep '.gz');do gunzip ${f_};done
    echo $get_url | cut -d/ -f8 > $DWC2_DIR/web/version
    rm -rf DuetWebControl-SD.zip
}

### backup functions
backup_msg(){
    status_msg "Running $1 backup ..."
}
backup_cfg(){
    if [ ! -d $BACKUP_DIR ]
    then
        mkdir -p ${HOME}/backup
    fi
    if [ -f $CFG_FILE ]
    then
        get_date
        cp $CFG_FILE $BACKUP_DIR/printer.cfg."$current_date".backup
    fi
}
backup_full(){
    if [[ -d $KLIPPER_DIR && -d $DWC2FK_DIR && -d $DWC2_DIR ]]
    then
        backup_klipper_only && confirm_msg "Klipper done ..."
        backup_dwc2fk_only && confirm_msg "dwc2-for-klipper done ..."
        backup_dwc2_only && confirm_msg "DWC2 done ..."
    else
        warn_msg "Can not create full backup."
        warn_msg "One or more directories not found!"
    fi
}
backup_klipper_only(){
    if [ -d $KLIPPER_DIR ]
    then
        get_date
        mkdir -p $BACKUP_DIR/klipper-backup/"$current_date" && cp -rf $KLIPPER_DIR $_
    else
        warn_msg "Can not backup Klipper."
        warn_msg "No Klipper directory found!"
    fi
}
backup_dwc2fk_only(){
    if [ -d $DWC2FK_DIR ]
    then
        get_date
        mkdir -p $BACKUP_DIR/dwc2fk-backup/"$current_date" && cp -rf $DWC2FK_DIR $_
    else
        warn_msg "Can not backup dwc2-for-klipper."
        warn_msg "No dwc2-for-klipper directory found!"
    fi
}
backup_dwc2_only(){
    if [ -d $DWC2_DIR ]
    then
        get_date
        mkdir -p $BACKUP_DIR/dwc2-backup/"$current_date" && cp -rf $DWC2_DIR $_
    else
        warn_msg "Can not backup DWC2."
        warn_msg "No DWC2 directory found!"
    fi
}

### remove functions
rm_klipper(){
    echo; warn_msg "Removing Klipper + klippy-env will make any\nDWC2-for-Klipper installation inoperable!"
    while true; do
        read -p "Do you really want to continue? (Y/n): " yn
        case "$yn" in
            Y|y|Yes|yes|"")
            echo; status_msg "Removing Klipper ..."
            echo; status_msg "Stopping Klipper service ..."
            sudo service klipper stop && confirm_msg "Klipper service stopped!"
            echo; status_msg "Removing Klipper from startup ..."
            sudo update-rc.d -f klipper remove && confirm_msg "Removed!"
            echo; status_msg "Removing Klipper service ..."
            sudo rm -rf $KLIPPER_SYSFILE1 $KLIPPER_SYSFILE2 && confirm_msg "Removed!"
            echo; status_msg "Removing Klipper files from system ..."
            rm -rf $KLIPPER_DIR ${HOME}/klippy-env && confirm_msg "Removed!"; echo
            break
            ;;
            N|n|No|no) break;;
            *) warn_msg "Unknown parameter: $yn"; echo;;
        esac
    done
}
rm_dwc2fk(){
    echo; status_msg "Removing DWC2-for-Klipper..."
    rm -rf $DWC2FK_DIR $DWC2_DIR $DWC2FK_SYSDIR && confirm_msg "Removed!"
}
rm_dwc2(){
    echo; status_msg "Removing DWC2 web UI..."
    rm -rf $DWC2_DIR && confirm_msg "Removed!"
}

### install menu
inst_menu(){
    echo
    echo -e "/=================================================\ "
    echo -e "|        ${green} Welcome to the installation menu!${default}       | "
    echo -e "|-------------------------------------------------| "
    echo -e "| You need this menu usually only for installing  | "
    echo -e "| to a completely fresh system or if you used the | "
    echo -e "| uninstaller for Klipper or DWC2-for-Klipper.    | "
    echo -e "\=================================================/ "
    echo
    echo -e "What do you want to install?"; echo
    echo "1) Install all"
    echo "2) Klipper"
    echo "3) DWC2-for-Klipper"
    echo "4) DWC2 web UI"
    echo
    warn_msg "Q) Exit"
    echo
    while true; do
        read -p "Please select: " choice; echo
        case "$choice" in
            1) inst_klipper && inst_dwc2fk && inst_dwc2; break;;
            2) inst_klipper; break;;
            3) inst_dwc2fk; break;;
            4) inst_dwc2; break;;
            Q|q) main_menu;;
            *) warn_msg "Unknown parameter: $choice"; echo;;
        esac
    done
    inst_menu
}

### advanced menu
adv_menu(){
    echo
    echo -e "/=================================================\ "
    echo -e "|          ${yellow}Welcome to the advanced menu!${default}          | "
    echo -e "|-------------------------------------------------| "
    echo -e "| Before flashing or getting the printer ID make  | "
    echo -e "| sure that the printer is the only USB device    | "
    echo -e "| connected to your Raspberry Pi.                 | "
    echo -e "\=================================================/ "
    echo
    echo -e "What do you want to do?"; echo
    echo "1) Build Firmware"
    echo "2) Flash MCU"
    echo "3) Get printer ID"
    echo "4) Write printer ID to printer.cfg"
    echo -e "5) Write DWC2-for-klipper configuration\n   example to printer.cfg"
    echo
    warn_msg "Q) Exit"
    echo
    while true; do
        read -p "Please select: " choice; echo
        case "$choice" in
            1) build_fw; break;;
            2) flash_routine; break;;
            3) get_usb_id; break;;
            4) get_usb_id && write_printid_cfg; break;;
            5) write_dwc2fk_cfg; break;;
            Q|q) main_menu;;
            *) warn_msg "Unknown parameter: $choice"; echo;;
        esac
    done
    adv_menu
}

### remove menu
rm_menu(){
    echo
    echo -e "/=================================================\ "
    echo -e "|       ${red}Welcome to the uninstallation menu!${default}       | "
    echo -e "|-------------------------------------------------| "
    echo -e "|                  $(warn_msg ">>> Warning <<<")                | "
    echo -e "|  $(warn_msg "You are about to remove Klipper, all of its")    | "
    echo -e "|  $(warn_msg "components and/or extensions!")                  | "
    echo -e "|                                                 | "
    echo -e "|  Files and directories which remain untouched:  | "
    echo -e "|  --> ~/printer.cfg                              | "
    echo -e "|  --> ~/backup                                   | "
    echo -e "|  You need remove them manually if you wish so.  | "
    echo -e "\=================================================/ "
    echo
    echo -e "What do you want to remove?"; echo
    echo "1) Remove all"
    echo "2) Klipper (incl. klippy-env)"
    echo "3) DWC2-for-Klipper"
    echo "4) DWC2 web UI"
    echo
    warn_msg "Q) Exit"
    echo
    while true; do
        read -p "Please select: " choice
        case "$choice" in
            1) rm_klipper && rm_dwc2fk && rm_dwc2; break;;
            2) rm_klipper; break;;
            3) rm_dwc2fk; break;;
            4) rm_dwc2; break;;
            Q|q) main_menu;;
            *) warn_msg "Unknown parameter: $choice"; echo;;
        esac
    done
    rm_menu
}

action(){
    case "$action" in
    0)
    clear
    print_header
    system_check
    main_menu
    ;;
    1)
    clear
    print_header
    inst_menu
    main_menu
    ;;
    2)
    clear
    print_header
    adv_menu
    ;;
    3)
    clear
    print_header
    rm_menu
    ;;
    4)
    clear
    print_header
    update_full
    main_menu
    ;;
    5)
    clear
    print_header
    update_klipper
    confirm_msg "Klipper updated!"
    main_menu
    ;;
    6)
    clear
    print_header
    update_dwc2fk
    confirm_msg "DWC2-for-Klipper updated!"
    main_menu
    ;;
    7)
    clear
    print_header
    update_dwc2
    confirm_msg "DWC2 web UI updated!"
    main_menu
    ;;
    8)
    clear
    print_header
    backup_msg "Full"
    backup_full
    main_menu
    ;;
    9)
    clear
    print_header
    backup_msg "Klipper"
    backup_klipper_only
    main_menu
    ;;
    10)
    clear
    print_header
    backup_msg "dwc2-for-klipper"
    backup_dwc2fk_only
    main_menu
    ;;
    11)
    clear
    print_header
    backup_msg "DWC2"
    backup_dwc2_only
    main_menu
    ;;
    Q|q)
    confirm_msg "Happy printing! ...\n"; exit 1
    ;;
    *)
    warn_msg "Unknown parameter: $action"
    main_menu
    ;;
    esac
}

print_header
check_euid
start_check
main_menu
