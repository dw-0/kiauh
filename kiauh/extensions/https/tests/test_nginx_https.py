# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import pytest
from extensions.https.nginx_https import (
    AlreadyHttpsError,
    build_http_config,
    build_https_config,
    extract_fqdn,
    extract_redirect_port,
    extract_server_body,
    extract_tls_server_body,
    strip_listen_directives,
)
from utils.nginx_utils import config_enables_https

FQDN = "printer.example.com"
CERT = f"/etc/letsencrypt/live/{FQDN}/fullchain.pem"
KEY = f"/etc/letsencrypt/live/{FQDN}/privkey.pem"


# --------------------------------------------------------------------------- #
# extract_server_body
# --------------------------------------------------------------------------- #
def test_extract_server_body_returns_inner_body(http_config_text):
    body = extract_server_body(http_config_text)
    # the inner body keeps the location blocks ...
    assert "location /websocket" in body
    assert "proxy_pass http://mjpgstreamer4/;" in body
    # ... but not the outermost `server {` wrapper
    assert "server {" not in body


def test_extract_server_body_balances_nested_braces():
    cfg = (
        "server {\n"
        "    location / {\n"
        "        try_files $uri =404;\n"
        "    }\n"
        "    location /a {\n"
        "        nested {\n"
        "            deep {\n"
        "            }\n"
        "        }\n"
        "    }\n"
        "}\n"
    )
    body = extract_server_body(cfg)
    assert "location /a" in body
    assert "deep {" in body
    # every brace in the extracted body is balanced
    assert body.count("{") == body.count("}")
    # the server's own closing brace is excluded
    assert not body.rstrip().endswith("}\n}")


def test_extract_server_body_raises_on_unbalanced():
    with pytest.raises(ValueError):
        extract_server_body("server {\n    location / {\n")


def test_extract_server_body_raises_when_no_server_block():
    with pytest.raises(ValueError):
        extract_server_body("# just a comment, no server block\n")


def test_extract_server_body_ignores_commented_server_keyword():
    # a comment mentioning "server {" before the real block must not be matched
    cfg = "# was: server { dead block }\nserver {\n    listen 80;\n}\n"
    body = extract_server_body(cfg)
    assert "listen 80;" in body
    assert "dead block" not in body


def test_build_https_config_survives_leading_comment_with_brace(http_config_text):
    # a leading comment containing braces must not derail block extraction
    cfg = "# example server { ... } block\n" + http_config_text
    result = build_https_config(cfg, FQDN, CERT, KEY)
    assert config_enables_https(result)
    assert "proxy_pass http://apiserver/websocket;" in result


# --------------------------------------------------------------------------- #
# strip_listen_directives
# --------------------------------------------------------------------------- #
def test_strip_listen_directives_removes_listen_lines(http_config_text):
    body = strip_listen_directives(extract_server_body(http_config_text))
    for line in body.splitlines():
        assert not line.strip().startswith("listen")
        assert not line.strip().startswith("# listen")
    # bare catch-all server_name is dropped so the TLS block sets its own
    assert "server_name _;" not in body
    # the meaningful body survives
    assert "root /home/pi/mainsail;" in body
    assert "location /websocket" in body


# --------------------------------------------------------------------------- #
# build_https_config
# --------------------------------------------------------------------------- #
def test_build_https_config_has_redirect_block(http_config_text):
    result = build_https_config(http_config_text, FQDN, CERT, KEY)
    redirect_block = result.split("listen 443 ssl")[0]
    assert "listen 80;" in redirect_block
    assert "# listen [::]:80;" in redirect_block
    assert "    listen [::]:80;" not in redirect_block
    assert f"return 301 https://{FQDN}$request_uri;" in redirect_block
    # a pure redirect server must carry no proxy/location logic
    assert "location" not in redirect_block


def test_build_https_config_has_tls_block(http_config_text):
    result = build_https_config(http_config_text, FQDN, CERT, KEY)
    assert "listen 443 ssl http2;" in result
    assert f"ssl_certificate {CERT};" in result
    assert f"ssl_certificate_key {KEY};" in result
    assert "ssl_protocols TLSv1.2 TLSv1.3;" in result
    assert f"server_name {FQDN} _;" in result


def test_build_https_config_preserves_original_body(http_config_text):
    result = build_https_config(http_config_text, FQDN, CERT, KEY)
    assert "proxy_pass http://apiserver/websocket;" in result
    for n in ("", "2", "3", "4"):
        assert f"proxy_pass http://mjpgstreamer{n or '1'}/;" in result
    assert "proxy_pass http://apiserver$request_uri;" in result


def test_build_https_config_total_redirect(http_config_text):
    result = build_https_config(http_config_text, FQDN, CERT, KEY)
    # exactly one redirect, and it lives in the port-80 block
    assert result.count("return 301") == 1
    assert "return 301" in result.split("listen 443 ssl")[0]


def test_build_https_config_redirect_target_is_fqdn_not_host(http_config_text):
    # the redirect must target the validated FQDN, never $host: the block
    # answers the catch-all server_name, so $host would be an open redirect
    result = build_https_config(http_config_text, FQDN, CERT, KEY)
    assert f"return 301 https://{FQDN}$request_uri;" in result
    assert "$host" not in result


def test_build_https_config_custom_redirect_port(http_config_text):
    result = build_https_config(http_config_text, FQDN, CERT, KEY, redirect_port=8080)
    redirect_block = result.split("listen 443 ssl")[0]
    assert "listen 8080;" in redirect_block
    assert "# listen [::]:8080;" in redirect_block
    assert "    listen [::]:8080;" not in redirect_block


def test_build_https_config_comments_out_ipv6_listen(http_config_text):
    # an active 'listen [::]' fails nginx -t on IPv6-disabled hosts; KIAUH ships
    # the IPv6 listen commented, so both generated blocks must follow suit
    result = build_https_config(http_config_text, FQDN, CERT, KEY)
    assert "# listen [::]:80;" in result
    assert "# listen [::]:443 ssl http2;" in result
    # no ACTIVE (uncommented) IPv6 listen in either block
    assert "    listen [::]:80;" not in result
    assert "    listen [::]:443" not in result


def test_build_https_config_raises_on_already_https(http_config_text):
    once = build_https_config(http_config_text, FQDN, CERT, KEY)
    with pytest.raises(AlreadyHttpsError):
        build_https_config(once, FQDN, CERT, KEY)


def test_build_https_config_matches_golden(http_config_text, expected_https_text):
    result = build_https_config(http_config_text, FQDN, CERT, KEY)
    assert result == expected_https_text


# --------------------------------------------------------------------------- #
# extract_fqdn
# --------------------------------------------------------------------------- #
def test_extract_fqdn_from_https_config(http_config_text):
    https = build_https_config(http_config_text, FQDN, CERT, KEY)
    assert extract_fqdn(https) == FQDN


def test_extract_fqdn_none_for_plain_http(http_config_text):
    # the generated HTTP site only has the catch-all `server_name _;`
    assert extract_fqdn(http_config_text) is None


# --------------------------------------------------------------------------- #
# build output is recognised as HTTPS (cross-check with the shared detector)
# --------------------------------------------------------------------------- #
def test_plain_http_is_not_detected_as_https(http_config_text):
    assert config_enables_https(http_config_text) is False


def test_build_output_is_detected_as_https(http_config_text):
    https = build_https_config(http_config_text, FQDN, CERT, KEY)
    assert config_enables_https(https) is True


# --------------------------------------------------------------------------- #
# extract_redirect_port
# --------------------------------------------------------------------------- #
def test_extract_redirect_port_default_80(http_config_text):
    https = build_https_config(http_config_text, FQDN, CERT, KEY)
    assert extract_redirect_port(https) == 80


def test_extract_redirect_port_custom(http_config_text):
    https = build_https_config(http_config_text, FQDN, CERT, KEY, redirect_port=8080)
    assert extract_redirect_port(https) == 8080


def test_extract_redirect_port_none_when_absent():
    assert extract_redirect_port("# no server block here\n") is None


# --------------------------------------------------------------------------- #
# extract_tls_server_body / build_http_config (reverse transform)
# --------------------------------------------------------------------------- #
def test_extract_tls_server_body_picks_tls_block(http_config_text):
    https = build_https_config(http_config_text, FQDN, CERT, KEY)
    body = extract_tls_server_body(https)
    assert "listen 443 ssl http2;" in body
    assert "return 301" not in body  # not the redirect block


def test_extract_tls_server_body_raises_for_plain_http(http_config_text):
    with pytest.raises(ValueError):
        extract_tls_server_body(http_config_text)


def test_build_http_config_reverses_to_plain_http(http_config_text):
    https = build_https_config(http_config_text, FQDN, CERT, KEY)
    http = build_http_config(https, port=80)
    assert config_enables_https(http) is False
    assert "listen 80;" in http
    assert "# listen [::]:80;" in http
    assert "ssl_certificate" not in http
    assert "ssl_protocols" not in http
    assert "listen 443" not in http
    assert f"server_name {FQDN} _;" not in http
    assert "return 301" not in http  # the redirect block is discarded
    # the body (root, proxy/location blocks) is preserved verbatim
    assert "proxy_pass http://apiserver/websocket;" in http
    for n in ("", "2", "3", "4"):
        assert f"proxy_pass http://mjpgstreamer{n or '1'}/;" in http
    assert "client_max_body_size 0;" in http


def test_build_http_config_restores_custom_port(http_config_text):
    https = build_https_config(http_config_text, FQDN, CERT, KEY, redirect_port=8080)
    http = build_http_config(https, port=8080)
    assert "listen 8080;" in http
    assert "# listen [::]:8080;" in http


def test_build_http_config_round_trip_allows_reenabling(http_config_text):
    # http -> https -> http -> https must keep working and preserve the body
    https = build_https_config(http_config_text, FQDN, CERT, KEY)
    http = build_http_config(https, port=80)
    again = build_https_config(http, FQDN, CERT, KEY)
    assert config_enables_https(again) is True
    assert "proxy_pass http://mjpgstreamer4/;" in again


def test_build_http_config_raises_without_tls_block(http_config_text):
    with pytest.raises(ValueError):
        build_http_config(http_config_text, port=80)
