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

  ### find all suitable logfiles for klipper
  logfiles=()
  klipper_logs="${HOME}/klipper_logs/klippy*.log"
  moonraker_logs="${HOME}/klipper_logs/moonraker*.log"

  if ls $klipper_logs 2>/dev/null 1>&2; then
    for kl_log in $(find $klipper_logs); do
      logfiles+=($kl_log)
    done
  fi
  if ls $moonraker_logs 2>/dev/null 1>&2; then
    for mr_log in $(find $moonraker_logs); do
      logfiles+=($mr_log)
    done
  fi
  if ls /tmp/dwc2*.log 2>/dev/null 1>&2; then
    for dwc_log in $(find /tmp/dwc2*.log); do
      logfiles+=($dwc_log)
    done
  fi

  ### draw interface
  i=0
  top_border
  echo -e "|     ${yellow}~~~~~~~~~~~~~~~ [ Log Upload ] ~~~~~~~~~~~~~~${default}     |"
  hr
  echo -e "|  You can choose the following files for uploading:    |"
  for log in ${logfiles[@]}; do
    printf "|  $i) %-50s|\n" "${logfiles[$i]}"
    i=$((i + 1))
  done
  back_footer
  while true; do
    read -p "${cyan}Please select:${default} " choice
    if [ $choice = "b" ] || [ $choice = "B" ]; then
      clear && main_menu && break
    elif [ $choice -le ${#logfiles[@]} ]; then
      upload_log "${logfiles[$choice]}"
      upload_selection
    else
      clear && print_header
      ERROR_MSG="File not found!" && print_msg && clear_msg
      upload_selection
    fi
  done
}

upload_log(){
  if [ -f "$1" ]; then
    clear && print_header
    status_msg "Uploading $1 ..."
    LINK=$(curl -s --upload-file $1 'http://paste.c-net.org/')
    [ ! -z "$LINK" ] && ok_msg "$1 upload successfull!"
    echo -e "\n${cyan}###### Here is your link:${default}"
    echo -e ">>>>>> $LINK\n"
    unset LINK
  else
    clear && print_header
    ERROR_MSG="File not found!" && print_msg && clear_msg
    upload_selection
  fi
}
