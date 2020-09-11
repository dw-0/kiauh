save_klipper_state(){
  source_ini
  #read current klipper state
  cd $KLIPPER_DIR
  COMMIT_STATE=$(git rev-parse --short HEAD)
  if [ "$GET_BRANCH" = "origin/master" ]; then
    ORI_OLD=$previous_origin_state
    ORI_NEW=$COMMIT_STATE
    sed -i "/previous_origin_state=/s/$ORI_OLD/$ORI_NEW/" $INI_FILE
  elif [ "$GET_BRANCH" = "origin" ]; then
    ORI_OLD=$previous_origin_state
    ORI_NEW=$COMMIT_STATE
    sed -i "/previous_origin_state=/s/$ORI_OLD/$ORI_NEW/" $INI_FILE
  elif [ "$GET_BRANCH" = "dmbutyugin/scurve-shaping" ]; then
    SHA_OLD=$previous_shaping_state
    SHA_NEW=$COMMIT_STATE
    sed -i "/previous_shaping_state=/s/$SHA_OLD/$SHA_NEW/" $INI_FILE
  elif [ "$GET_BRANCH" = "dmbutyugin/scurve-smoothing" ]; then
    SMO_OLD=$previous_smoothing_state
    SMO_NEW=$COMMIT_STATE
    sed -i "/previous_smoothing_state=/s/$SMO_OLD/$SMO_NEW/" $INI_FILE
  elif [ "$GET_BRANCH" = "Arksine/work-web_server-20200131" ]; then
    WWS_OLD=$previous_moonraker_state
    WWS_NEW=$COMMIT_STATE
    sed -i "/previous_moonraker_state=/s/$WWS_OLD/$WWS_NEW/" $INI_FILE
  elif [ "$GET_BRANCH" = "Arksine/dev-moonraker-testing" ]; then
    DMT_OLD=$previous_dev_moonraker_state
    DMT_NEW=$COMMIT_STATE
    sed -i "/previous_dev_moonraker_state=/s/$DMT_OLD/$DMT_NEW/" $INI_FILE
  fi
}

load_klipper_state(){
  source_ini
  print_branch
  cd $KLIPPER_DIR
  CURRENT_COMMIT=$(git rev-parse --short=8 HEAD)
  if [ "$GET_BRANCH" = "origin/master" ] || [ "$GET_BRANCH" = "origin" ]; then
    PREVIOUS_COMMIT=$previous_origin_state
  elif [ "$GET_BRANCH" = "dmbutyugin/scurve-shaping" ]; then
    PREVIOUS_COMMIT=$previous_shaping_state
  elif [ "$GET_BRANCH" = "dmbutyugin/scurve-smoothing" ]; then
    PREVIOUS_COMMIT=$previous_smoothing_state
  elif [ "$GET_BRANCH" = "Arksine/work-web_server-20200131" ]; then
    PREVIOUS_COMMIT=$previous_moonraker_state
  elif [ "$GET_BRANCH" = "Arksine/dev-moonraker-testing" ]; then
    PREVIOUS_COMMIT=$previous_dev_moonraker_state
  fi
  CURRENT_COMMIT_DATE=$(git show -s --format=%cd --date=short $CURRENT_COMMIT)
  if [ "$PREVIOUS_COMMIT" != "0" ]; then
    PREVIOUS_COMMIT_DATE=$(git show -s --format=%cd --date=short $PREVIOUS_COMMIT)
  fi
  if [ "$PREVIOUS_COMMIT" = "0" ]; then
    CURR_UI=$(echo -e "${green}$CURRENT_COMMIT from $CURRENT_COMMIT_DATE${default}")
    PREV_UI=$(echo -e "${red}None${default}                    ")
  else
    if [ "$CURRENT_COMMIT" = "$PREVIOUS_COMMIT" ]; then
      CURR_UI=$(echo -e "${green}$CURRENT_COMMIT from $CURRENT_COMMIT_DATE${default}")
      PREV_UI=$(echo -e "${green}$PREVIOUS_COMMIT from $PREVIOUS_COMMIT_DATE${default}")
    else
      CURR_UI=$(echo -e "${yellow}$CURRENT_COMMIT from $CURRENT_COMMIT_DATE${default}")
      PREV_UI=$(echo -e "${yellow}$PREVIOUS_COMMIT from $PREVIOUS_COMMIT_DATE${default}")
    fi
  fi
  rollback_ui
  rollback_klipper
}

rollback_klipper(){
  if [ "$PREVIOUS_COMMIT" != "0" ] && [ "$CURRENT_COMMIT" != "$PREVIOUS_COMMIT" ]; then
    while true; do
        echo -e "${cyan}"
        read -p "###### Do you want to rollback to $PREVIOUS_COMMIT? (Y/n): " yn
        echo -e "${default}"
        case "$yn" in
          Y|y|Yes|yes|"")
            clear
            print_header
              status_msg "Rolling back to $PREVIOUS_COMMIT ..."
              git reset --hard $PREVIOUS_COMMIT -q
              ok_msg "Rollback complete!"; echo
            load_klipper_state
            break;;
          N|n|No|no) clear; advanced_menu; break;;
          Q|q) clear; advanced_menu; break;;
          *)
            print_unkown_cmd
            print_msg && clear_msg;;
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