#!/bin/bash
remove_ui(){
  top_border
  echo -e "|     ${red}~~~~~~~~~~~~~~ [ Remove Menu ] ~~~~~~~~~~~~~~${default}     | "
  hr
  echo -e "|  Directories which remain untouched:                  | "
  echo -e "|  --> Your printer configuration directory             | "
  echo -e "|  --> ~/kiauh-backups                                  | "
  echo -e "|  You need remove them manually if you wish so.        | "
  hr
  echo -e "|  Firmware:                |  Touchscreen GUI:         | "
  echo -e "|  1) [Klipper]             |  5) [KlipperScreen]       | "
  echo -e "|                           |                           | "
  echo -e "|  Klipper API:             |  Other:                   | "
  echo -e "|  2) [Moonraker]           |  6) [Duet Web Control]    | "
  echo -e "|                           |  7) [OctoPrint]           | "
  echo -e "|  Klipper Webinterface:    |  8) [PrettyGCode]         | "
  echo -e "|  3) [Mainsail]            |  9) [Telegram Bot]        | "
  echo -e "|  4) [Fluidd]              |                           | "
  echo -e "|                           |  10) [MJPG-Streamer]      | "
  echo -e "|                           |  11) [NGINX]              | "
  back_footer
}

remove_menu(){
	#TODO Currently it's a "dumb" remove page, looking for a "smart" one
	local menu_options=(
		"1" "Klipper"
		"2" "Klipper API(Moonraker)"
		"3" "Interfaces"
		"4" "Other"
	)
  local menu_str="Directories which remain untouched:

Your printer configuration directory
~/kiauh-backups

You need remove them manually if you wish so."

  while true; do
    local menu
    menu=$(whiptail --title "Remove Menu" --cancel-button "Back" --notags --menu "$menu_str\n\nPerform Action:" \
      "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 8 "${menu_options[@]}" 3>&1 1>&2 2>&3)
    local out=$?
    if [ $out -eq 1 ]; then
    	break
    elif [ $out -eq 0 ]; then
			case "$menu" in
				1) do_action "remove_klipper";;
      	2) do_action "remove_moonraker";;
      	3) remove_interface_menu;;
      	4) remove_other_menu;;
				esac
		else
			# Unexpected event, no clue what happened
			exit 1
		fi
  done
}
