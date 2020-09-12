stop_service() {
    # Stop DWC Service
    echo "#### Stopping DWC Service.."
    sudo service dwc stop
}

remove_service() {
    # Remove DWC from Startup
    echo
    echo "#### Removing DWC from Startup.."
    sudo update-rc.d -f dwc remove

    # Remove DWC from Services
    echo
    echo "#### Removing DWC Service.."
    sudo rm -f /etc/init.d/dwc /etc/default/dwc

}

remove_files() {
    # Remove virtualenv
    if [ -d ~/dwc-env ]; then
        echo "Removing virtualenv..."
        rm -rf ~/dwc-env
    else
        echo "No DWC virtualenv found"
    fi

    # Notify user of method to remove DWC source code
    echo
    echo "The DWC system files and virtualenv have been removed."
}

verify_ready()
{
    if [ "$EUID" -eq 0 ]; then
        echo "This script must not run as root"
        exit -1
    fi
}

verify_ready
stop_service
remove_service
remove_files