rollback_menu(){
    load_klipper_state
    if [ "$PREVIOUS_COMMIT" != "0" ] && [ "$CURRENT_COMMIT" != "$PREVIOUS_COMMIT" ]; then

        local text="If serious errors occured after updating Klipper, \
you can use this menu to return to the previously used commit from which you have updated.\n
Active branch: $PRINT_BRANCH
Currently on commit: $CURR_UI
Commit last updated from: $PREV_UI\n
Do you want to rollback to $PREVIOUS_COMMIT?"
        whiptail --title "Rollback menu" --yesno \
            "$text" \
            "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH"

        local out=$?
        if [ $out -eq 0 ]; then
            status_msg "Rolling back to $PREVIOUS_COMMIT ..."
            git reset --hard $PREVIOUS_COMMIT -q
            ok_msg "Rollback complete!"; echo
            load_klipper_state
        fi
    else
        whiptail --title "Rollback menu" --msgbox "Rollback unavailable" "$KIAUH_WHIPTAIL_NORMAL_HEIGHT"\
        "$KIAUH_WHIPTAIL_NORMAL_WIDTH"
    fi
}
