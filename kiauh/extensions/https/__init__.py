# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from pathlib import Path

MODULE_PATH: Path = Path(__file__).resolve().parent

# Root-owned directory holding the DNS provider credentials (chmod 700).
SECRETS_DIR: Path = Path("/root/.secrets")
# Where certbot stores issued certificates, one subdirectory per FQDN.
LE_LIVE_DIR: Path = Path("/etc/letsencrypt/live")
# certbot runs every executable here after a certificate is actually renewed.
RENEWAL_HOOK_DIR: Path = Path("/etc/letsencrypt/renewal-hooks/deploy")

# A conservative hostname matcher: labels of 1-63 chars, at least two of them,
# no leading/trailing hyphen, total length up to 253.
FQDN_REGEX: str = (
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
    r"(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))+$"
)
# A deliberately loose email check; certbot does the authoritative validation.
EMAIL_REGEX: str = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
