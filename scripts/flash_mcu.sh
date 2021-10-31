#!/bin/bash

show_flash_method_help(){
  top_border
  echo -e "|     ~~~~~~~~ < ? > Help: Flash MCU < ? > ~~~~~~~~     |"
  hr
  echo -e "| ${cyan}Regular flashing method:${default}                              |"
  echo -e "| The default method to flash controller boards which   |"
  echo -e "| are connected and updated over USB and not by placing |"
  echo -e "| a compiled firmware file onto an internal SD-Card.    |"
  blank_line
  echo -e "| Common controllers that get flashed that way are:     |"
  echo -e "| - Arduino Mega 2560                                   |"
  echo -e "| - Fysetc F6 / S6 (used without a Display + SD-Slot)   |"
  blank_line
  echo -e "| ${cyan}Updating via SD-Card Update:${default}                          |"
  echo -e "| Many popular controller boards ship with a bootloader |"
  echo -e "| capable of updating the firmware via SD-Card.         |"
  echo -e "| Choose this method if your controller board supports  |"
  echo -e "| this way of updating. This method ONLY works for up-  |"
  echo -e "| grading firmware. The initial flashing procedure must |"
  echo -e "| be done manually per the instructions that apply to   |"
  echo -e "| your controller board.                                |"
  blank_line
  echo -e "| Common controllers that can be flashed that way are:  |"
  echo -e "| - BigTreeTech SKR 1.3 / 1.4 (Turbo) / E3 / Mini E3    |"
  echo -e "| - Fysetc F6 / S6 (used with a Display + SD-Slot)      |"
  echo -e "| - Fysetc Spider                                       |"
  blank_line
  back_footer
  while true; do
    read -p "${cyan}###### Please select:${default} " choice
    case "$choice" in
      B|b)
        clear && print_header
        select_flash_method
        break;;
      *)
        print_unkown_cmd
        print_msg && clear_msg;;
    esac
  done
}

select_flash_method(){
  top_border
  echo -e "|        ~~~~~~~~~~~~ [ Flash MCU ] ~~~~~~~~~~~~        |"
  hr
  echo -e "| Please select the flashing method to flash your MCU.  |"
  echo -e "| Make sure to only select a method your MCU supports.  |"
  echo -e "| Not all MCUs support both methods!                    |"
  hr
  blank_line
  echo -e "| 1) Regular flashing method                            |"
  echo -e "| 2) Updating via SD-Card Update                        |"
  blank_line
  back_help_footer
  while true; do
    read -p "${cyan}###### Please select:${default} " choice
    case "$choice" in
      1)
        echo -e "###### > Regular flashing method"
        select_mcu_connection
        select_mcu_id
        [ CONFIRM_FLASH ] && flash_mcu
        break;;
      2)
        echo -e "###### > SD-Card Update"
        select_mcu_connection
        select_mcu_id
        [ CONFIRM_FLASH ] && flash_mcu_sd
        break;;
      B|b)
        advanced_menu
        break;;
      H|h)
        clear && print_header
        show_flash_method_help
        break;;
      *)
        print_unkown_cmd
        print_msg && clear_msg;;
    esac
  done
}

select_mcu_id(){
  if [ ${#mcu_list[@]} -ge 1 ]; then
    top_border
    echo -e "|                   ${red}!!! ATTENTION !!!${default}                   |"
    hr
    echo -e "| Make sure, to select the correct MCU!                 |"
    echo -e "| ${red}ONLY flash a firmware created for the respective MCU!${default} |"
    bottom_border
    echo -e "${cyan}###### List of available MCU:${default}"
    ### list all mcus
    id=0
    for mcu in ${mcu_list[@]}; do
      let id++
      echo -e " $id) $mcu"
    done
    ### verify user input
    sel_index=""
    while [[ ! ($sel_index =~ ^[1-9]+$) ]] || [ $sel_index -gt $id ]; do
      echo
      read -p "${cyan}###### Select MCU to flash:${default} " sel_index
      if [[ ! ($sel_index =~ ^[1-9]+$) ]]; then
        warn_msg "Invalid input!"
      elif [ $sel_index -lt 1 ] || [ $sel_index -gt $id ]; then
        warn_msg "Please select a number between 1 and $id!"
      fi
      mcu_index=$(echo $((sel_index - 1)))
      selected_mcu_id="${mcu_list[$mcu_index]}"
    done
    ### confirm selection
    while true; do
      echo -e "\n###### You selected:\n ● MCU #$sel_index: $selected_mcu_id\n"
      read -p "${cyan}###### Continue? (Y/n):${default} " yn
      case "$yn" in
        Y|y|Yes|yes|"")
          echo -e "###### > Yes"
          status_msg "Flashing $selected_mcu_id ..."
          CONFIRM_FLASH="true"
          break;;
        N|n|No|no)
          echo -e "###### > No"
          CONFIRM_FLASH="false"
          break;;
        *)
          print_unkown_cmd
          print_msg && clear_msg;;
      esac
    done
  fi
}

flash_mcu(){
  do_action_service "stop" "klipper"
  make flash FLASH_DEVICE="${mcu_list[$mcu_index]}"
  ### evaluate exit code of make flash
  if [ ! $? -eq 0 ]; then
    warn_msg "Flashing failed!"
    warn_msg "Please read the console output above!"
  else
    ok_msg "Flashing successfull!"
  fi
  do_action_service "start" "klipper"
}

flash_mcu_sd(){
  flash_script="${HOME}/klipper/scripts/flash-sdcard.sh"

  ### write each supported board to the array to make it selectable
  board_list=()
  for board in $("$flash_script" -l | tail -n +2); do
    board_list+=($board)
  done

  i=0
  top_border
  echo -e "|  Please select the type of board that corresponds to  |"
  echo -e "|  the currently selected MCU ID you chose before.      |"
  blank_line
  echo -e "|  The following boards are currently supported:        |"
  hr
  ### display all supported boards to the user
  for board in ${board_list[@]}; do
    if [ $i -lt 10 ]; then
      printf "|  $i) %-50s|\n" "${board_list[$i]}"
    else
      printf "|  $i) %-49s|\n" "${board_list[$i]}"
    fi
    i=$((i + 1))
  done
  quit_footer

  ### make the user select one of the boards
  while true; do
    read -p "${cyan}###### Please select board type:${default} " choice
    if [ $choice = "q" ] || [ $choice = "Q" ]; then
      clear && advanced_menu && break
    elif [ $choice -le ${#board_list[@]} ]; then
      selected_board="${board_list[$choice]}"
      break
    else
      clear && print_header
      ERROR_MSG="Invalid choice!" && print_msg && clear_msg
      flash_mcu_sd
    fi
  done

  while true; do
    top_border
    echo -e "| If your board is flashed with firmware that connects  |"
    echo -e "| at a custom baud rate, please change it now.          |"
    blank_line
    echo -e "| If you are unsure, stick to the default 250000!       |"
    bottom_border
    echo -e "${cyan}###### Please set the baud rate:${default} "
    unset baud_rate
    while [[ ! $baud_rate =~ ^[0-9]+$ ]]; do
      read -e -i "250000" -e baud_rate
      selected_baud_rate=$baud_rate
      break
    done
    break
  done

  ###flash process
  do_action_service "stop" "klipper"
  "$flash_script" -b "$selected_baud_rate" "$selected_mcu_id" "$selected_board"
  ### evaluate exit code of flash-sdcard.sh execution
  if [ ! $? -eq 0 ]; then
    warn_msg "Flashing failed!"
    warn_msg "Please read the console output above!"
  else
    ok_msg "Flashing successfull!"
  fi
  do_action_service "start" "klipper"
}

build_fw(){
  if [ -d $KLIPPER_DIR ]; then
    cd $KLIPPER_DIR
    status_msg "Initializing firmware build ..."
    dep=(build-essential dpkg-dev make)
    dependency_check
    make clean && make menuconfig
    status_msg "Building firmware ..."
    make && ok_msg "Firmware built!"
  else
    warn_msg "Can not build firmware without a Klipper directory!"
  fi
}

select_mcu_connection(){
  echo
  top_border
  echo -e "| ${yellow}Make sure to have the controller board connected now!${default} |"
  blank_line
  echo -e "| How is the controller board connected to the host?    |"
  echo -e "| 1) USB                                                |"
  echo -e "| 2) UART                                               |"
  bottom_border
  while true; do
    read -p "${cyan}###### Connection method:${default} " choice
    case "$choice" in
      1)
        retrieve_id "USB"
        break;;
      2)
        retrieve_id "UART"
        break;;
      *)
        print_unkown_cmd
        print_msg && clear_msg;;
    esac
  done
  unset mcu_count

  if [[ "${#mcu_list[@]}" -lt 1 ]]; then
    warn_msg "No MCU found!"
    warn_msg "MCU not plugged in or not detectable!"
    echo
  fi
}

retrieve_id(){
  status_msg "Identifying MCU ..."
  sleep 1
  mcu_list=()
  mcu_count=1
  [ "$1" = "USB" ] && path="/dev/serial/by-id/*"
  [ "$1" = "UART" ] && path="/dev/ttyAMA0"
  if [[ "$(ls $path)" != "" ]] ; then
    for mcu in $path; do
      declare "mcu_id_$mcu_count"="$mcu"
      mcu_id="mcu_id_$mcu_count"
      mcu_list+=("${!mcu_id}")
      echo -e " ● ($1) MCU #$mcu_count: ${cyan}$mcu${default}\n"
      let mcu_count++
    done
  fi 2>/dev/null
}
