accept_upload_conditions(){
  while true; do
    top_border
    echo -e "|     ${red}~~~~~~~~~~~ [ Upload Agreement ] ~~~~~~~~~~~~${default}     |"
    hr
    echo -e "| The following function will help to quickly upload    |"
    echo -e "| logs for debugging purposes. With confirming this     |"
    echo -e "| dialog, you agree that during that process your logs  |"
    echo -e "| will be uploaded to: ${yellow}http://paste.c-net.org/${default}          |"
    hr
    echo -e "| ${red}PLEASE NOTE:${default}                                          |"
    echo -e "| Be aware that logs can contain network information,   |"
    echo -e "| private data like usernames, filenames, or other      |"
    echo -e "| information you may not want to make public.          |"
    blank_line
    echo -e "| Do ${red}NOT${default} use this function if you don't agree!          |"
    bottom_border
    read -p "${cyan}Do you accept? (Y/n):${default} " yn
    case "$yn" in
      Y|y|Yes|yes|"")
        sed -i "/logupload_accepted=/s/false/true/" $INI_FILE
        clear && print_header && upload_selection
        ;;
      N|n|No|no)
        clear
        main_menu
        break
        ;;
      *)
        clear
        print_header
        print_unkown_cmd
        print_msg && clear_msg
        accept_upload_conditions;;
    esac
  done
}

upload_selection(){
  source_kiauh_ini
  [ "$logupload_accepted" = "false" ] && accept_upload_conditions
  KLIPPY_LOG=/tmp/klippy.log
  MOONRAKER_LOG=/tmp/moonraker.log
  DWC2_LOG=/tmp/dwc2.log
  top_border
  echo -e "|     ${yellow}~~~~~~~~~~~~~~~ [ Log Upload ] ~~~~~~~~~~~~~~${default}     |"
  hr
  echo -e "|  You can choose the following files for uploading:    |"
  echo -e "|  1) klippy.log                                        |"
  echo -e "|  2) moonraker.log                                     |"
  echo -e "|  3) dwc2.log                                          |"
  quit_footer
  while true; do
    read -p "${cyan}Please select:${default} " choice
    case "$choice" in
    1)
      clear && print_header
      upload_log "$KLIPPY_LOG"
      upload_selection
      ;;
    2)
      clear && print_header
      upload_log "$MOONRAKER_LOG"
      upload_selection
      ;;
    3)
      clear && print_header
      upload_log "$DWC2_LOG"
      upload_selection
      ;;
    q | Q) clear; main_menu; break;;
    esac
  done
}

upload_log(){
  if [ -f "$1" ]; then
    status_msg "Uploading $1 ..."
    LINK=$(curl -s --upload-file $1 'http://paste.c-net.org/')
    [ ! -z "$LINK" ] && ok_msg "$1 upload successfull!"
    echo -e "\n${cyan}###### Here is your link:${default}"
    echo -e ">>>>>> $LINK\n"
    unset LINK
  else
    clear && print_header
    ERROR_MSG="$1 not found!" && print_msg && clear_msg
    upload_selection
  fi
}