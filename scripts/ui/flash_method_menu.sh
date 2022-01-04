flash_method_menu(){
    local menu_options=(
	    "1" "Regular flash method"
		"2" "Update via SD-Card Update"
        "3" "Help"
		)

    local menu_str="Please select the flashing method to flash your MCU. Make sure to only select a method your \
MCU supports. Not all MCUs support both methods!"

    while true; do
        local menu
        menu=$(whiptail --title "Flash MCU" --cancel-button "Back" --notags --menu "$menu_str\n\nPerform Action:" \
            "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 8 "${menu_options[@]}" 3>&1 1>&2 2>&3)
        local out=$?
        if [ $out -eq 1 ]; then
    	break
        elif [ $out -eq 0 ]; then
			case "$menu" in
				1) 
                    select_mcu_connection
                    select_mcu_id
                    [ CONFIRM_FLASH ] && flash_mcu
                    ;;
                2) 
                    select_mcu_connection
                    select_mcu_id
                    [ CONFIRM_FLASH ] && flash_mcu_sd
                    break;;
				3) 
                    clear && print_header
                    flash_method_help_msg
                    ;;
			esac
		else
			# Unexpected event, no clue what happened
			exit 1
		fi
  done
}