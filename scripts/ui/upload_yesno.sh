#!/bin/bash

upload_yesno(){
  whiptail --title "Upload Agreement" \
    --yesno \
    "The following function will help to quickly upload logs for debugging purposes. With confirming this dialog, you agree that during that process your logs will be uploaded to: http://paste.c-net.org/

PLEASE NOTE:

Be aware that logs can contain network information, private data like usernames, filenames, or other information you may not want to make public. 

Do ${red}NOT${default} use this function if you don't agree!

Do you accept?" \
    "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH"

  local out=$?
  if [ $out -eq 0 ]; then
    sed -i "/logupload_accepted=/s/false/true/" $INI_FILE
        upload_selection
  else
    return
  fi
}