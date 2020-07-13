switch_to_origin(){
  cd $KLIPPER_DIR
  status_msg "Switching...Please wait ..."; echo
  git fetch origin -q && git checkout origin/master -q
}

switch_to_scurve_shaping(){
  cd $KLIPPER_DIR
  status_msg "Switching...Please wait ..."; echo
  if ! git remote | grep dmbutyugin -q; then
    git remote add dmbutyugin $DMBUTYUGIN_REPO
  fi
  git fetch dmbutyugin -q && git checkout $BRANCH_SCURVE_SHAPING -q
}

switch_to_scurve_smoothing(){
  cd $KLIPPER_DIR
  status_msg "Switching...Please wait ..."; echo
  if ! git remote | grep dmbutyugin -q; then
    git remote add dmbutyugin $DMBUTYUGIN_REPO
  fi
  git fetch dmbutyugin -q && git checkout $BRANCH_SCURVE_SMOOTHING -q
}

switch_to_moonraker(){
  cd $KLIPPER_DIR
  status_msg "Switching...Please wait ..."; echo
  if ! git remote | grep Arksine -q; then
    git remote add Arksine $ARKSINE_REPO
  fi
  git fetch Arksine -q && git checkout $BRANCH_MOONRAKER -q
}

switch_to_dev_moonraker(){
  cd $KLIPPER_DIR
  status_msg "Switching...Please wait ..."; echo
  if ! git remote | grep Arksine -q; then
    git remote add Arksine $ARKSINE_REPO
  fi
  git fetch Arksine -q && git checkout $BRANCH_DEV_MOONRAKER -q
}