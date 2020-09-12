#!/bin/sh
# System startup script for dwc2-for-klipper-socket

### BEGIN INIT INFO
# Provides:          dwc2-for-klipper-socket
# Required-Start:    $local_fs
# Required-Stop:
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: dwc2-for-klipper-socket daemon
# Description:       Starts the dwc2-for-klipper-socket daemon.
### END INIT INFO

PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
DESC="dwc2-for-klipper-socket daemon"
NAME="dwc2-for-klipper-socket"
DEFAULTS_FILE=/etc/default/dwc
PIDFILE=/var/run/dwc.pid

. /lib/lsb/init-functions

# Read defaults file
[ -r $DEFAULTS_FILE ] && . $DEFAULTS_FILE

case "$1" in
start)  log_daemon_msg "Starting dwc2-for-klipper-socket" $NAME
        start-stop-daemon --start --quiet --exec $DWC_EXEC \
                          --background --pidfile $PIDFILE --make-pidfile \
                          --chuid $DWC_USER --user $DWC_USER \
                          -- $DWC_ARGS
        log_end_msg $?
        ;;
stop)   log_daemon_msg "Stopping dwc2-for-klipper-socket" $NAME
        killproc -p $PIDFILE $DWC_EXEC
        RETVAL=$?
        [ $RETVAL -eq 0 ] && [ -e "$PIDFILE" ] && rm -f $PIDFILE
        log_end_msg $RETVAL
        ;;
restart) log_daemon_msg "Restarting dwc2-for-klipper-socket" $NAME
        $0 stop
        $0 start
        ;;
reload|force-reload)
        log_daemon_msg "Reloading configuration not supported" $NAME
        log_end_msg 1
        ;;
status)
        status_of_proc -p $PIDFILE $DWC_EXEC $NAME && exit 0 || exit $?
        ;;
*)      log_action_msg "Usage: /etc/init.d/dwc {start|stop|status|restart|reload|force-reload}"
        exit 2
        ;;
esac
exit 0