# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
"""
Pure helpers for inspecting nginx config text. Side-effect free (no file or
process access) so they can be shared between the webui_client component and
the https extension and unit-tested without a running nginx.
"""

from __future__ import annotations

import re

# matches an active TLS listen on port 443 regardless of how the parameters are
# ordered: nginx accepts "listen 443 ssl", "listen 443 http2 ssl",
# "listen 443 default_server ssl" and "listen [::]:443 ssl". The directive is
# bounded to a single line (comments already stripped) by excluding ';'/'#', and
# the \b around 443 keeps "listen 8443 ssl;" from matching.
_HTTPS_LISTEN_RE = re.compile(r"\blisten\b[^#;]*\b443\b[^#;]*\bssl\b")


def config_enables_https(config_text: str) -> bool:
    """
    Return True if the config has an ACTIVE ``listen ... 443 ssl`` directive.

    Comments are ignored: each line is truncated at the first ``#`` before the
    check, so neither a full-line comment nor a trailing comment that merely
    mentions ``listen 443 ssl`` is mistaken for an enabled TLS server block.

    :param config_text: the full nginx config text
    :return: True if an active TLS listen directive is present, else False
    """
    for raw_line in config_text.splitlines():
        code = raw_line.split("#", 1)[0]
        if _HTTPS_LISTEN_RE.search(code):
            return True
    return False


def listen_ports(config_text: str) -> set[int]:
    """
    Return the set of ports of every ACTIVE (non-commented) ``listen``
    directive in the config, across all server blocks.

    The port is taken from the address token right after ``listen``, keeping the
    part after the last ``:`` so ``listen 80;``, ``listen [::]:443 ssl;`` and
    ``listen 443 ssl http2;`` all yield the numeric port. Unlike scanning only
    the last listen per file, this sees a 443 directive that is followed by
    another listen - and unlike the ssl-aware check it also catches a plain,
    non-TLS ``listen 443;`` that would still collide on the socket.

    :param config_text: the full nginx config text
    :return: the set of active listen ports
    """
    ports: set[int] = set()
    for raw_line in config_text.splitlines():
        code = raw_line.split("#", 1)[0].strip()
        if not code.startswith("listen"):
            continue
        fields = code[len("listen") :].strip().rstrip(";").split()
        if not fields:
            continue
        token = fields[0].split(":")[-1].strip("[]")
        if token.isdigit():
            ports.add(int(token))
    return ports
