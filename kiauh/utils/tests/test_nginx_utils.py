# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from utils.nginx_utils import config_enables_https, listen_ports


def test_true_for_active_tls_listen():
    assert config_enables_https("server {\n    listen 443 ssl http2;\n}\n") is True


def test_true_with_only_ssl_flag():
    assert config_enables_https("    listen 443 ssl;\n") is True


def test_true_for_ipv6_only_tls_listen():
    # a hand-written site whose only active TLS listen is IPv6 still counts
    assert config_enables_https("    listen [::]:443 ssl;\n") is True


def test_true_when_ssl_not_immediately_after_port():
    # nginx accepts the ssl parameter in any position after the port
    assert config_enables_https("    listen 443 http2 ssl;\n") is True
    assert config_enables_https("    listen 443 default_server ssl;\n") is True


def test_false_for_higher_port_ending_in_443():
    # 8443 must not be mistaken for 443
    assert config_enables_https("    listen 8443 ssl;\n") is False


def test_false_for_plain_443_without_ssl():
    # a plain HTTP server on 443 (no ssl parameter) is not HTTPS
    assert config_enables_https("    listen 443;\n") is False


def test_false_for_plain_http():
    assert config_enables_https("server {\n    listen 80;\n}\n") is False


def test_ignores_full_line_comment():
    # a commented-out example must not be mistaken for an enabled TLS block
    assert config_enables_https("server {\n    # listen 443 ssl;\n}\n") is False


def test_ignores_trailing_comment():
    # the directive only appears after a '#', so it is not active
    assert config_enables_https("    listen 80;  # e.g. listen 443 ssl\n") is False


def test_false_for_empty_text():
    assert config_enables_https("") is False


# --------------------------------------------------------------------------- #
# listen_ports
# --------------------------------------------------------------------------- #
def test_listen_ports_collects_all_blocks():
    text = "server {\n    listen 443 ssl http2;\n}\nserver {\n    listen 8080;\n}\n"
    assert listen_ports(text) == {443, 8080}


def test_listen_ports_sees_443_even_when_not_last():
    # a plain 'listen 443;' followed by another listen must still be detected
    text = "server {\n    listen 443;\n    listen 8080;\n}\n"
    assert 443 in listen_ports(text)


def test_listen_ports_handles_ipv6_and_address_prefix():
    assert listen_ports("    listen [::]:443 ssl;\n") == {443}


def test_listen_ports_ignores_commented_directives():
    assert listen_ports("    # listen 443 ssl;\n    listen 80;\n") == {80}


def test_listen_ports_empty_for_no_listen():
    assert listen_ports("server {\n    server_name _;\n}\n") == set()
