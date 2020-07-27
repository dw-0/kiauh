save_klipper_state(){
  source_ini
  #read current klipper state
  COMMIT_STATE=$(git rev-parse --short HEAD)
  if [ $GET_BRANCH = origin/master ]; then
    ORI_OLD=$previous_origin_state
    ORI_NEW=$COMMIT_STATE
    sed -i "/previous_origin_state=/s/$ORI_OLD/$ORI_NEW/" $INI_FILE
  elif [ $GET_BRANCH = dmbutyugin/scurve-shaping ]; then
    SHA_OLD=$previous_shaping_state
    SHA_NEW=$COMMIT_STATE
    sed -i "/previous_shaping_state=/s/$SHA_OLD/$SHA_NEW/" $INI_FILE
  elif [ $GET_BRANCH = dmbutyugin/scurve-smoothing ]; then
    SMO_OLD=$previous_smoothing_state
    SMO_NEW=$COMMIT_STATE
    sed -i "/previous_smoothing_state=/s/$SMO_OLD/$SMO_NEW/" $INI_FILE
  elif [ $GET_BRANCH = Arksine/work-web_server-20200131 ]; then
    WWS_OLD=$previous_moonraker_state
    WWS_NEW=$COMMIT_STATE
    sed -i "/previous_moonraker_state=/s/$WWS_OLD/$WWS_NEW/" $INI_FILE
  elif [ $GET_BRANCH = Arksine/dev-moonraker-testing ]; then
    DMT_OLD=$previous_dev_moonraker_state
    DMT_NEW=$COMMIT_STATE
    sed -i "/previous_dev_moonraker_state=/s/$DMT_OLD/$DMT_NEW/" $INI_FILE
  fi
}

load_klipper_state(){
  source_ini
  print_branch
  CURR_COMM=$(git rev-parse --short=8 HEAD)
  if [ "$GET_BRANCH" == "origin/master" ]; then
    PREV_COMM=$previous_origin_state
  elif [ "$GET_BRANCH" == "dmbutyugin/scurve-shaping" ]; then
    PREV_COMM=$previous_shaping_state
  elif [ "$GET_BRANCH" == "dmbutyugin/scurve-smoothing" ]; then
    PREV_COMM=$previous_smoothing_state
  elif [ "$GET_BRANCH" == "Arksine/work-web_server-20200131" ]; then
    PREV_COMM=$previous_moonraker_state
  elif [ "$GET_BRANCH" == "Arksine/dev-moonraker-testing" ]; then
    PREV_COMM=$previous_dev_moonraker_state
  fi
  PREV_COMM_DATE=$(git show -s --format=%cd --date=short $PREV_COMM)
  CURR_COMM_DATE=$(git show -s --format=%cd --date=short $CURR_COMM)
  if [ $CURR_COMM = $PREV_COMM ]; then
    CURR_UI=$(echo -e "${green}$CURR_COMM from $CURR_COMM_DATE${default}")
    PREV_UI=$(echo -e "${green}$PREV_COMM from $PREV_COMM_DATE${default}")
  else
    CURR_UI=$(echo -e "${yellow}$CURR_COMM from $CURR_COMM_DATE${default}")
    PREV_UI=$(echo -e "${yellow}$PREV_COMM from $PREV_COMM_DATE${default}")
  fi
  rollback_ui
  rollback_klipper
}

rollback_klipper(){
  if [ "$CURR_COMM" != "$PREV_COMM" ]; then
    while true; do
        echo -e "${cyan}"
        read -p "###### Do you want to rollback to $PREV_COMM? (Y/n): " yn
        echo -e "${default}"
        case "$yn" in
          Y|y|Yes|yes|"")
            clear
            print_header
              status_msg "Rolling back to $PREV_COMM ..."
              git reset --hard $PREV_COMM -q
              ok_msg "Rollback complete!"; echo
            load_klipper_state
            break;;
          N|n|No|no) clear; advanced_menu; break;;
          Q|q) clear; advanced_menu; break;;
      esac
    done
  else
    while true; do
      echo -e "${cyan}"
      read -p "Perform action: " action; echo
      echo -e "${default}"
      case "$action" in
        Q|q)
          clear; advanced_menu; break;;
        *)
          clear
          print_header
          print_unkown_cmd
          print_msg && clear_msg
          rollback_ui;;
      esac
    done
  fi
}