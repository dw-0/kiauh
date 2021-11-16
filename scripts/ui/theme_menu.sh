#!/bin/bash

ms_theme_ui(){
  top_border
  echo -e "|     ${red}~~~~~~~~ [ Mainsail Theme Installer ] ~~~~~~~${default}     | "
  hr
  echo -e "|  ${green}A preview of each Mainsail theme can be found here:${default}  | "
  echo -e "|  https://docs.mainsail.xyz/theming/themes             | "
  blank_line
  echo -e "|  ${yellow}Important note:${default}                                      | "
  echo -e "|  Installing a theme from this menu will overwrite an  | "
  echo -e "|  already installed theme or modified custom.css file! | "
  hr
  #echo -e "|  Theme:                                               | "
  # dynamically generate the themelist from a csv file
  get_theme_list
  echo -e "|                                                       | "
  echo -e "|  R) [Remove Theme]                                    | "
  #echo -e "|                                                       | "
  back_footer
}

ms_theme_menu(){
	
	local menu_options=(
		"1" "Migrate MainsailOS"
		"2" "Migrate FluiddPi"
	)
  local menu_str="This function will help you to migrate a vanilla MainsailOS or FluiddPi image to a newer state.
Only use this function if you use MainsailOS 0.4.0 or lower, or FluiddPi v1.13.0 or lower.
Please have a look at the KIAUH changelog for more details on what this function will do."

  while true; do
    local menu
    menu=$(whiptail --title "Mainsail Theme Installer" --cancel-button "Back" --notags --menu "$menu_str\n\nInstall/Remove Theme:" \
      "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 8 "${menu_options[@]}" 3>&1 1>&2 2>&3)
    local out=$?
    if [ $out -eq 1 ]; then
    	break
    elif [ $out -eq 0 ]; then
			case "$menu" in
				1) migrate_custompios "mainsail";;
      	2) migrate_custompios "fluiddpi";;
			esac
		else
			# Unexpected event, no clue what happened
			exit 1
		fi
  done

  ms_theme_ui
  while true; do
    read -p "${cyan}Install theme:${default} " a; echo
    if [ $a = "b" ] || [ $a = "B" ]; then
      clear && advanced_menu && break
    elif [ $a = "r" ] || [ $a = "R" ]; then
      ms_theme_delete
      ms_theme_menu
    elif [ $a -le ${#t_url[@]} ]; then
      ms_theme_install "${t_auth[$a]}" "${t_url[$a]}" "${t_name[$a]}" "${t_note[$a]}"
      ms_theme_menu
    else
      clear && print_header
      ERROR_MSG="Invalid command!" && print_msg && clear_msg
      ms_theme_menu
    fi
  done
  ms_theme_menu
}