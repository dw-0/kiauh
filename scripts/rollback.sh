#!/bin/bash

save_klipper_state(){
  source_kiauh_ini
  #read current klipper state
  cd $KLIPPER_DIR
  COMMIT_STATE=$(git rev-parse --short HEAD)
  if [ "$GET_BRANCH" = "master" ]; then
    ORI_OLD=$previous_origin_state
    ORI_NEW=$COMMIT_STATE
    sed -i "/previous_origin_state=/s/$ORI_OLD/$ORI_NEW/" $INI_FILE
  elif [ "$GET_BRANCH" = "scurve-shaping" ]; then
    SHA_OLD=$previous_shaping_state
    SHA_NEW=$COMMIT_STATE
    sed -i "/previous_shaping_state=/s/$SHA_OLD/$SHA_NEW/" $INI_FILE
  elif [ "$GET_BRANCH" = "scurve-smoothing" ]; then
    SMO_OLD=$previous_smoothing_state
    SMO_NEW=$COMMIT_STATE
    sed -i "/previous_smoothing_state=/s/$SMO_OLD/$SMO_NEW/" $INI_FILE
  fi
}

load_klipper_state(){
  source_kiauh_ini
  get_branch
  cd $KLIPPER_DIR
  CURRENT_COMMIT=$(git rev-parse --short=8 HEAD)
  if [ "$GET_BRANCH" = "origin/master" ] || [ "$GET_BRANCH" = "master" ]; then
    PREVIOUS_COMMIT=$previous_origin_state
  elif [ "$GET_BRANCH" = "scurve-shaping" ]; then
    PREVIOUS_COMMIT=$previous_shaping_state
  elif [ "$GET_BRANCH" = "scurve-smoothing" ]; then
    PREVIOUS_COMMIT=$previous_smoothing_state
  fi
  CURRENT_COMMIT_DATE=$(git show -s --format=%cd --date=short $CURRENT_COMMIT)
  if [ "$PREVIOUS_COMMIT" != "0" ]; then
    PREVIOUS_COMMIT_DATE=$(git show -s --format=%cd --date=short $PREVIOUS_COMMIT)
  fi
  if [ "$PREVIOUS_COMMIT" = "0" ]; then
    CURR_UI=$(echo -e "${green}$CURRENT_COMMIT from $CURRENT_COMMIT_DATE${default}")
    PREV_UI=$(echo -e "${red}$NONE${default}                    ")
  else
    if [ "$CURRENT_COMMIT" = "$PREVIOUS_COMMIT" ]; then
      CURR_UI=$(echo -e "${green}$CURRENT_COMMIT from $CURRENT_COMMIT_DATE${default}")
      PREV_UI=$(echo -e "${green}$PREVIOUS_COMMIT from $PREVIOUS_COMMIT_DATE${default}")
    else
      CURR_UI=$(echo -e "${yellow}$CURRENT_COMMIT from $CURRENT_COMMIT_DATE${default}")
      PREV_UI=$(echo -e "${yellow}$PREVIOUS_COMMIT from $PREVIOUS_COMMIT_DATE${default}")
    fi
  fi

}
