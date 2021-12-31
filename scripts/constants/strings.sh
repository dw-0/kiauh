KIAUH_TITLE="KIAUH - Klipper Installation And Update Helper"

#names
declare -A READABLE_NAMES
READABLE_NAMES["$KLIPPER"]="Klipper"
READABLE_NAMES["$MOONRAKER"]="Moonraker"
READABLE_NAMES["$MAINSAIL"]="Mainsail"
READABLE_NAMES["$FLUIDD"]="Fluidd"
READABLE_NAMES["$KLIPPERSCREEN"]="KlipperScreen"
READABLE_NAMES["$DWC2FK"]="DWC-for-Klipper"
READABLE_NAMES["$DWC2"]="DWC2 Web UI"
READABLE_NAMES["$DWC"]="Duet Web Control" #Addressing DWC2 and DWC2FK
READABLE_NAMES["$PGC"]="PrettyGCode"
READABLE_NAMES["$MOONRAKER_TELEGRAM_BOT"]="Telegram Bot"
READABLE_NAMES["$SYSTEM"]="System"
READABLE_NAMES["$OCTOPRINT"]="OctoPrint"
READABLE_NAMES["$MJPG_STREAMER"]="Webcam MJPG-Streamer"
READABLE_NAMES["$NGINX"]="Nginx"
readonly NOT_INSTALLED="Not installed!"
readonly INCOMPLETE="Incomplete!"
readonly INSTALLED="Installed!"

#display this as placeholder if no version/commit could be fetched
readonly NONE="None"