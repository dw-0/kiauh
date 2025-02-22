# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import urllib.request
from pathlib import Path
from typing import List

from components.klipper.klipper import Klipper
from components.log_uploads import LogFile
from core.logger import Logger
from utils.instance_utils import get_instances


def get_logfile_list() -> List[LogFile]:
    log_dirs: List[Path] = [
        instance.base.log_dir for instance in get_instances(Klipper)
    ]

    logfiles: List[LogFile] = []
    for _dir in log_dirs:
        for f in _dir.iterdir():
            logfiles.append({"filepath": f, "display_name": get_display_name(f)})

    return logfiles


def get_display_name(filepath: Path) -> str:
    printer = " ".join(filepath.parts[-3].split("_")[:-1])
    name = filepath.name

    return f"{printer}: {name}"


def upload_logfile(logfile: LogFile) -> None:
    file = logfile.get("filepath")
    name = logfile.get("display_name")
    Logger.print_status(f"Uploading the following logfile from {name} ...")

    with open(file, "rb") as f:
        headers = {"x-random": ""}
        req = urllib.request.Request("http://paste.c-net.org/", headers=headers, data=f)
        try:
            response = urllib.request.urlopen(req)
            link = response.read().decode("utf-8")
            Logger.print_ok("Upload successful! Access it via the following link:")
            Logger.print_ok(f">>>> {link}", False)
        except Exception as e:
            Logger.print_error("Uploading logfile failed!")
            Logger.print_error(str(e))
