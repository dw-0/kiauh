flash_method_help_msg(){
    # While it is possible to scroll by force enable scroll, two pages look better
    local text="Regular flashing method:

The default method to flash controller boards which are connected and \
updated over USB and not by placing a compiled firmware file onto an internal \
SD-Card. 

Common controllers that get flashed that way are:

* Arduino Mega 2560
* Fysetc F6 / S6 (used without a Display + SD-Slot)"

    whiptail --title "Help: MCU Flashing" --ok-button "Next" --msgbox "$text" "$KIAUH_WHIPTAIL_NORMAL_HEIGHT"\
    "$KIAUH_WHIPTAIL_NORMAL_WIDTH"
    local text="Updating via SD-Card Update:

Many popular controller boards ship with a bootloader capable of updating the \
firmware via SD-Card. Choose this method if your controller board supports this \
way of updating. This method ONLY works for upgrading firmware. The initial \
flashing procedure must be done manually per the instructions that apply to \
your controller board.

Common controllers that can be flashed that way are:

* BigTreeTech SKR 1.3 / 1.4 (Turbo) / E3 / Mini E3
* Fysetc F6 / S6 (used with a Display + SD-Slot)
* Fysetc Spider"
    whiptail --title "Help: MCU Flashing" --ok-button "Return" --msgbox "$text" "$KIAUH_WHIPTAIL_NORMAL_HEIGHT"\
    "$KIAUH_WHIPTAIL_NORMAL_WIDTH"
}