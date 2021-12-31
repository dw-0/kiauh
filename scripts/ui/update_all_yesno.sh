update_all_yesno(){
  source_kiauh_ini
    if [ "${#update_arr[@]}" = "0" ]; then
        whiptail --title "Update All" --ok-button "Back" --msgbox \
        "Everything is already up to date!" 12 $KIAUH_WHIPTAIL_NORMAL_WIDTH
    else
        local update_list="The following installations will be updated:\n"

        if [ "$KLIPPER_UPDATE_AVAIL" = "true" ]; then
            update_list+="● ${READABLE_NAMES["$KLIPPER"]}: ${update_message[$KLIPPER]}\n"
        fi
        if [ "$DWC2FK_UPDATE_AVAIL" = "true" ]; then
            update_list+="● ${READABLE_NAMES["$DWC2FK"]}: ${update_message[$DWC2FK]}\n"
        fi
        if [ "$DWC2_UPDATE_AVAIL" = "true" ]; then
            update_list+="● ${READABLE_NAMES[$DWC2]}: ${update_message[$DWC2]}\n"
        fi
        if [ "$MOONRAKER_UPDATE_AVAIL" = "true" ]; then
            update_list+="● ${READABLE_NAMES[$MOONRAKER]}: ${update_message[$MOONRAKER]}\n"
        fi
        if [ "$MAINSAIL_UPDATE_AVAIL" = "true" ]; then
            update_list+="● ${READABLE_NAMES[$MAINSAIL]}: ${update_message[$MAINSAIL]}\n"
        fi
        if [ "$FLUIDD_UPDATE_AVAIL" = "true" ]; then
            update_list+="● ${READABLE_NAMES[$FLUIDD]}: ${update_message[$FLUIDD]}\n"
        fi
        if [ "$KLIPPERSCREEN_UPDATE_AVAIL" = "true" ]; then
            update_list+="● ${READABLE_NAMES[$KLIPPERSCREEN]}: ${update_message[$KLIPPERSCREEN]}\n"
        fi
        if [ "$PGC_UPDATE_AVAIL" = "true" ]; then
            update_list+="● ${READABLE_NAMES[$PGC]}: ${update_message[$PGC]}\n"
        fi
        if [ "$MOONRAKER_TELEGRAM_BOT_UPDATE_AVAIL" = "true" ]; then
            update_list+="$● ${READABLE_NAMES[$MOONRAKER_TELEGRAM_BOT]}: ${update_message[$MOONRAKER_TELEGRAM_BOT]}\n"  
        fi
        if [ "$SYS_UPDATE_AVAIL" = "true" ]; then
         "● System"
        fi

        whiptail --title "Update All" --yesno "$update_list" $KIAUH_WHIPTAIL_NORMAL_HEIGHT $KIAUH_WHIPTAIL_NORMAL_WIDTH

        local out=$?
        if [ $out -eq 0 ]; then
            do_action "update_all"
        else
            return
        fi
    fi
}
