import pytest

from src.simple_config_parser.simple_config_parser import SimpleConfigParser


@pytest.fixture
def parser():
    parser = SimpleConfigParser()
    parser._header = ["header1\n", "header2\n"]
    parser._config = {
        "section1": {
            "_raw": "[section1]\n",
            "body": [
                {
                    "_raw": "option1: value1\n",
                    "_raw_value": "value1\n",
                    "is_multiline": False,
                    "option": "option1",
                    "value": "value1",
                },
                {
                    "_raw": "option2: value2\n",
                    "_raw_value": "value2\n",
                    "is_multiline": False,
                    "option": "option2",
                    "value": "value2",
                },
            ],
        },
        "section2": {
            "_raw": "[section2]\n",
            "body": [
                {
                    "_raw": "option3: value3\n",
                    "_raw_value": "value3\n",
                    "is_multiline": False,
                    "option": "option3",
                    "value": "value3",
                },
            ],
        },
        "section3": {
            "_raw": "[section3]\n",
            "body": [
                {
                    "_raw": "option4:\n",
                    "_raw_value": ["    value4\n", "    value5\n", "    value6\n"],
                    "is_multiline": True,
                    "option": "option4",
                    "value": ["value4", "value5", "value6"],
                },
            ],
        },
    }
    return parser


def test_construct_content(parser):
    content = parser._construct_content()
    assert (
        content == "header1\nheader2\n"
        "[section1]\n"
        "option1: value1\n"
        "option2: value2\n"
        "[section2]\n"
        "option3: value3\n"
        "[section3]\n"
        "option4:\n"
        "    value4\n"
        "    value5\n"
        "    value6\n"
    )


def test_construct_content_no_header(parser):
    parser._header = None
    content = parser._construct_content()
    assert (
        content == "[section1]\n"
        "option1: value1\n"
        "option2: value2\n"
        "[section2]\n"
        "option3: value3\n"
        "[section3]\n"
        "option4:\n"
        "    value4\n"
        "    value5\n"
        "    value6\n"
    )


def test_construct_content_no_sections(parser):
    parser._config = {}
    content = parser._construct_content()
    assert content == "".join(parser._header)
