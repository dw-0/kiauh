# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
"""
Pure (side-effect free) helpers that rewrite a KIAUH-generated nginx site
from plain HTTP into an HTTP->HTTPS redirect plus a TLS server block.

Nothing in this module touches the filesystem, subprocess, sudo or certbot.
That keeps the actual config transformation fully unit-testable without a
running nginx or a Debian host. The orchestration (certbot, sudo writes,
nginx reload) lives in the surrounding extension modules.
"""

from __future__ import annotations

import re
from typing import Optional

from utils.nginx_utils import config_enables_https

_SERVER_OPEN_RE = re.compile(r"\bserver\b[^{]*\{")
_SERVER_NAME_RE = re.compile(r"^\s*server_name\s+(\S+)", re.MULTILINE)
_LISTEN_PORT_RE = re.compile(r"^\s*listen\s+(\d+)\b", re.MULTILINE)
_TLS_DIRECTIVE_RE = re.compile(
    r"^\s*(ssl_certificate|ssl_certificate_key|ssl_protocols)\b"
)


class AlreadyHttpsError(Exception):
    """Raised when the given config already contains a TLS server block."""


def _mask_comments(config_text: str) -> str:
    """
    Return a copy of the config with every ``#`` comment (``#`` to end of line)
    replaced by spaces, preserving length so offsets still map to the original.
    Used to find block delimiters without matching ``server {`` or braces that
    live inside a comment.
    """
    out = []
    in_comment = False
    for char in config_text:
        if char == "\n":
            in_comment = False
            out.append(char)
        elif char == "#":
            in_comment = True
            out.append(" ")
        elif in_comment:
            out.append(" ")
        else:
            out.append(char)
    return "".join(out)


def _server_bodies(config_text: str) -> list[str]:
    """
    Return the inner body of every top-level ``server { ... }`` block, in order
    (the content between each block's outermost braces, exclusive). Nested
    ``location { ... }`` blocks are preserved verbatim via depth counting, and
    ``server {`` or braces appearing inside comments are ignored.

    :raises ValueError: if a server block has unbalanced braces
    """
    # match delimiters on a comment-masked copy (same length, so indices map
    # back), but slice the bodies from the original text to keep their comments.
    masked = _mask_comments(config_text)
    bodies: list[str] = []
    pos = 0
    while True:
        match = _SERVER_OPEN_RE.search(masked, pos)
        if match is None:
            return bodies

        open_idx = match.end() - 1  # index of the opening brace
        depth = 0
        end = None
        for i in range(open_idx, len(masked)):
            char = masked[i]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end is None:
            raise ValueError("Unbalanced braces in server block.")
        bodies.append(config_text[open_idx + 1 : end])
        pos = end + 1


def extract_server_body(config_text: str) -> str:
    """
    Return the inner body of the FIRST top-level ``server { ... }`` block.

    :param config_text: the full nginx config text
    :return: the inner body of the first server block
    :raises ValueError: if no balanced server block can be found
    """
    bodies = _server_bodies(config_text)
    if not bodies:
        raise ValueError("No 'server { ... }' block found in config.")
    return bodies[0]


def extract_tls_server_body(config_text: str) -> str:
    """
    Return the inner body of the first top-level server block that has an
    active ``listen ... 443 ssl`` directive - i.e. the TLS block in a
    build_https_config output, as opposed to the :80 redirect block.

    :param config_text: the full nginx config text
    :return: the inner body of the TLS server block
    :raises ValueError: if no TLS server block can be found
    """
    for body in _server_bodies(config_text):
        if config_enables_https(body):
            return body
    raise ValueError("No TLS ('listen 443 ssl') server block found in config.")


def strip_listen_directives(server_body: str) -> str:
    """
    Remove the directives that the new wrapper blocks supply themselves:
    every ``listen ...;`` line (including the commented IPv6 variant KIAUH
    emits and its helper comment) and the bare catch-all ``server_name _;``.

    Leading and trailing blank lines are trimmed; interior formatting is kept.

    :param server_body: the inner body of an nginx server block
    :return: the cleaned body
    """
    kept = []
    for line in server_body.splitlines():
        stripped = line.strip()
        if stripped.startswith("listen") or stripped.startswith("# listen"):
            continue
        if stripped == "# uncomment the next line to activate IPv6":
            continue
        if stripped == "server_name _;":
            continue
        kept.append(line)

    return "\n".join(kept).strip("\n")


def build_https_config(
    original_config_text: str,
    fqdn: str,
    cert_path: str,
    key_path: str,
    redirect_port: int = 80,
) -> str:
    """
    Rewrite a plain-HTTP KIAUH nginx site into two server blocks:

      * a ``listen <redirect_port>`` block that does nothing but
        ``return 301 https://$host$request_uri;`` (no location blocks, so
        EVERY path redirects), and
      * a ``listen 443 ssl http2`` block carrying the original body
        (root + all proxy/location blocks) with the TLS directives injected.

    Only the FIRST top-level ``server`` block is rewritten and its body is
    carried over verbatim (gzip, proxy and webcam directives included); any
    content outside it is dropped. This holds for KIAUH's single-block
    template - the source of this config - but is worth knowing if that
    template ever grows a second server block.

    :param original_config_text: the current (HTTP) nginx config text
    :param fqdn: the fully qualified domain name for the certificate/site
    :param cert_path: path to the fullchain.pem
    :param key_path: path to the privkey.pem
    :param redirect_port: the port the redirect block listens on (default 80)
    :return: the rewritten config text
    :raises AlreadyHttpsError: if the input already has a TLS server block
    :raises ValueError: if no server block can be extracted
    """
    if config_enables_https(original_config_text):
        raise AlreadyHttpsError("Config already contains a 'listen 443 ssl' block.")

    body = strip_listen_directives(extract_server_body(original_config_text))

    # IPv6 listen is emitted commented-out, mirroring KIAUH's own site
    # template: an active 'listen [::]' aborts nginx -t on hosts where IPv6 is
    # disabled. Users who want IPv6 uncomment it in both blocks.
    # Redirect to the validated FQDN, not $host: the block also answers the
    # catch-all server_name '_', so reflecting an attacker-supplied Host header
    # through $host would be an open redirect. The certificate is only valid for
    # fqdn anyway, so the canonical target is always correct.
    redirect_block = (
        "server {\n"
        f"    listen {redirect_port};\n"
        "    # uncomment the next line to activate IPv6\n"
        f"    # listen [::]:{redirect_port};\n"
        f"    server_name {fqdn} _;\n"
        f"    return 301 https://{fqdn}$request_uri;\n"
        "}\n"
    )

    tls_block = (
        "server {\n"
        "    listen 443 ssl http2;\n"
        "    # uncomment the next line to activate IPv6\n"
        "    # listen [::]:443 ssl http2;\n"
        f"    server_name {fqdn} _;\n"
        "\n"
        f"    ssl_certificate {cert_path};\n"
        f"    ssl_certificate_key {key_path};\n"
        "    ssl_protocols TLSv1.2 TLSv1.3;\n"
        "\n"
        f"{body}\n"
        "}\n"
    )

    return f"{redirect_block}\n{tls_block}"


def build_http_config(https_config_text: str, port: int = 80) -> str:
    """
    Reverse of build_https_config: rebuild a single plain-HTTP server block
    from an HTTPS config, carrying the body (root, proxy/location blocks, gzip,
    any custom directives) back over verbatim.

    The transform is purely subtractive: from the TLS server block it drops only
    the directives this extension injected - the ``listen ... 443 ssl`` lines
    (and the commented IPv6 variant), the ``ssl_certificate``/
    ``ssl_certificate_key``/``ssl_protocols`` lines, and the catch-all
    ``server_name <fqdn> _;`` it added - and keeps everything else. So disabling
    HTTPS no longer resets the site to KIAUH's stock template and preserves a
    user's customizations. The :80 redirect block is discarded.

    :param https_config_text: the current HTTPS nginx config text
    :param port: the plain-HTTP listen port to restore
    :return: the rebuilt HTTP config text
    :raises ValueError: if no TLS server block can be found
    """
    fqdn = extract_fqdn(https_config_text)
    tls_body = extract_tls_server_body(https_config_text)
    injected_server_name = f"server_name {fqdn} _;" if fqdn else None

    kept = []
    for line in tls_body.splitlines():
        stripped = line.strip()
        if stripped.startswith("listen") or stripped.startswith("# listen"):
            continue
        if stripped == "# uncomment the next line to activate IPv6":
            continue
        if _TLS_DIRECTIVE_RE.match(line):
            continue
        if injected_server_name is not None and stripped == injected_server_name:
            continue
        kept.append(line)
    body = "\n".join(kept).strip("\n")

    return (
        "server {\n"
        f"    listen {port};\n"
        "    # uncomment the next line to activate IPv6\n"
        f"    # listen [::]:{port};\n"
        "\n"
        f"{body}\n"
        "}\n"
    )


def extract_fqdn(config_text: str) -> Optional[str]:
    """
    Return the first concrete ``server_name`` token (the FQDN) from a config,
    skipping the catch-all ``_``. Returns None if only the catch-all is set,
    as in a freshly generated HTTP site.

    :param config_text: the full nginx config text
    :return: the FQDN, or None if not present
    """
    for match in _SERVER_NAME_RE.finditer(config_text):
        name = match.group(1).rstrip(";")
        if name and name != "_":
            return name
    return None


def extract_redirect_port(config_text: str) -> Optional[int]:
    """
    Return the listen port of the FIRST server block. In a config produced by
    build_https_config that is the HTTP redirect block, so this recovers the
    port the site was on before HTTPS - used to restore it on disable. Returns
    None if the first block has no numeric listen.

    :param config_text: the full nginx config text
    :return: the redirect (original HTTP) port, or None
    """
    try:
        body = extract_server_body(config_text)
    except ValueError:
        return None
    match = _LISTEN_PORT_RE.search(body)
    return int(match.group(1)) if match else None
