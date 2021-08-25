#!/bin/bash
# This script installs dwc2-for-klipper-socket on a Raspberry Pi machine running
# Raspbian/Raspberry Pi OS based distributions.

# https://github.com/Stephan3/dwc2-for-klipper-socket.git

PYTHONDIR="${HOME}/dwc-env"
SYSTEMDDIR="/etc/systemd/system"
DWC_USER=${USER}

# Step 1:  Verify Klipper has been installed
check_klipper()
{
    if [ "$(systemctl list-units --full -all -t service --no-legend | grep -F "klipper.service")" ]; then
        echo "Klipper service found!"
    else
        echo "Klipper service not found, please install Klipper first"
        exit -1
    fi

}

# Step 2: Install packages
install_packages()
{
    PKGLIST="python3-virtualenv python3-dev python3-tornado"

    # Update system package info
    report_status "Running apt-get update..."
    sudo apt-get update --allow-releaseinfo-change

    # Install desired packages
    report_status "Installing packages..."
    sudo apt-get install --yes ${PKGLIST}
}

# Step 3: Create python virtual environment
create_virtualenv()
{
    report_status "Updating python virtual environment..."

    # Create virtualenv if it doesn't already exist
    [ ! -d ${PYTHONDIR} ] && virtualenv -p /usr/bin/python3 ${PYTHONDIR}

    # Install/update dependencies
    ${PYTHONDIR}/bin/pip install tornado==6.0.4
}

# Step 4: Install startup script
install_script(){
    report_status "Installing system start script..."
    sudo /bin/sh -c "cat > $SYSTEMDDIR/dwc.service" << EOF
#Systemd service file for DWC
[Unit]
Description=dwc_webif
After=network.target

[Install]
WantedBy=multi-user.target

[Service]
Type=simple
User=$DWC_USER
RemainAfterExit=yes
ExecStart=${PYTHONDIR}/bin/python3 ${SRCDIR}/web_dwc2.py
Restart=always
RestartSec=10
EOF
# Use systemctl to enable the klipper systemd service script
    sudo systemctl enable dwc.service
}

# Step 5: Start DWC service
start_software()
{
    report_status "Launching dwc2-for-klipper-socket..."
    sudo systemctl start dwc
}

# Helper functions
report_status()
{
    echo -e "\n\n###### $1"
}

verify_ready()
{
    if [ "$EUID" -eq 0 ]; then
        echo "This script must not run as root"
        exit -1
    fi
}

# Force script to exit if an error occurs
set -e

# Find SRCDIR from the pathname of this script
SRCDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/.. && pwd )"

# Run installation steps defined above
verify_ready
check_klipper
install_packages
create_virtualenv
install_script
start_software