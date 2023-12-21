#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import subprocess
from pathlib import Path


from kiauh.utils.logger import Logger


def remove_file(file_path: Path, sudo=False) -> None:
    try:
        command = f"{'sudo ' if sudo else ''}rm -f {file_path}"
        subprocess.run(command, stderr=subprocess.PIPE, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        log = f"Cannot remove file {file_path}: {e.stderr.decode()}"
        Logger.print_error(log)
        raise
