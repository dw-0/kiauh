# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from pathlib import Path

import pytest

ASSETS_DIR = Path(__file__).parent.joinpath("assets")


@pytest.fixture()
def http_config_text() -> str:
    """The nginx config KIAUH generates for a Mainsail install on port 80."""
    return ASSETS_DIR.joinpath("mainsail_http_cfg").read_text()


@pytest.fixture()
def expected_https_text() -> str:
    """Golden output of build_https_config for the http_config_text fixture."""
    return ASSETS_DIR.joinpath("expected_https_cfg").read_text()
