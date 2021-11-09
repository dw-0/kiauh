#!/bin/bash

### Gettext Configuration
alias GETTEXT='gettext "KIAUH"'

clear
set -e

### set color variables
green=$(echo -en "\e[92m")
yellow=$(echo -en "\e[93m")
red=$(echo -en "\e[91m")
cyan=$(echo -en "\e[96m")
default=$(echo -en "\e[39m")

### sourcing all additional scripts
SRCDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/.. && pwd )"
for script in "${SRCDIR}/kiauh/scripts/constants/"*.sh; do . $script; done
for script in "${SRCDIR}/kiauh/scripts/"*.sh; do . $script; done
for script in "${SRCDIR}/kiauh/scripts/ui/"*.sh; do . $script; done

### set some messages
warn_msg(){
  echo -e "${red}<!!!!> $1${default}"
}
status_msg(){
  echo; echo -e "${yellow}###### $1${default}"
}
ok_msg(){
  echo -e "${green}>>>>>> $1${default}"
}
title_msg(){
  echo -e "${cyan}$1${default}"
}
get_date(){
  current_date=$(date +"%y%m%d-%H%M")
}
print_unkown_cmd(){
  ERROR_MSG="Invalid command!"
}

print_msg(){
  if [[ "$ERROR_MSG" != "" ]]; then
    echo -e "${red}"
    echo -e "#########################################################"
    echo -e " $ERROR_MSG "
    echo -e "#########################################################"
    echo -e "${default}"
  fi
  if [ "$CONFIRM_MSG" != "" ]; then
    echo -e "${green}"
    echo -e "#########################################################"
    echo -e " $CONFIRM_MSG "
    echo -e "#########################################################"
    echo -e "${default}"
  fi
}

clear_msg(){
  unset CONFIRM_MSG
  unset ERROR_MSG
}

check_euid
init_ini
kiauh_status
main_menu
