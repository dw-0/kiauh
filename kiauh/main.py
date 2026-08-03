# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import io
import sys

from core.cli import run_cli
from core.i18n import _tr, setup_i18n
from core.logger import Logger
from core.menus.main_menu import MainMenu
from core.settings.kiauh_settings import KiauhSettings
from core.spinner import Spinner


def ensure_encoding() -> None:
    if sys.stdout.encoding == "UTF-8" or not isinstance(sys.stdout, io.TextIOWrapper):
        return
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    rc = run_cli()
    if rc == -1:
        try:
            settings = KiauhSettings()
            setup_i18n(settings.kiauh.language)
            ensure_encoding()
            MainMenu().run()
        except KeyboardInterrupt:
            # in case any spinner is still running, stop it before exiting
            Spinner.stop_all()
            Logger.print_ok(_tr("###### Happy printing!"), False)
    elif rc > 0:
        sys.exit(rc)


if __name__ == "__main__":
    main()
