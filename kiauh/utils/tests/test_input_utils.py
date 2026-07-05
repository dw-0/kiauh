from __future__ import annotations

from typing import Any, List
from unittest.mock import patch

import pytest
from utils.input_utils import (
    format_question,
    get_confirm,
    get_number_input,
    get_secret_input,
    get_selection_input,
    get_string_input,
    validate_number_input,
)


def _input_sequence(answers: List[str]):
    it = iter(answers)

    def _input(_prompt: str = "") -> str:
        return next(it)

    return _input


class TestGetConfirm:
    def test_accepts_yes(self, monkeypatch) -> None:
        monkeypatch.setattr("builtins.input", _input_sequence(["y"]))
        assert get_confirm("go?") is True

    def test_accepts_no(self, monkeypatch) -> None:
        monkeypatch.setattr("builtins.input", _input_sequence(["n"]))
        assert get_confirm("go?") is False

    def test_default_yes_on_empty(self, monkeypatch) -> None:
        monkeypatch.setattr("builtins.input", _input_sequence([""]))
        assert get_confirm("go?", default_choice=True) is True

    def test_default_no_on_empty(self, monkeypatch) -> None:
        monkeypatch.setattr("builtins.input", _input_sequence([""]))
        assert get_confirm("go?", default_choice=False) is False

    def test_handles_invalid_then_valid(self, monkeypatch) -> None:
        monkeypatch.setattr("builtins.input", _input_sequence(["maybe", "yes"]))
        assert get_confirm("go?") is True

    def test_go_back_returns_none(self, monkeypatch) -> None:
        monkeypatch.setattr("builtins.input", _input_sequence(["b"]))
        assert get_confirm("go?", allow_go_back=True) is None


class TestGetNumberInput:
    def test_returns_valid(self, monkeypatch) -> None:
        monkeypatch.setattr("builtins.input", _input_sequence(["5"]))
        assert get_number_input("count?", 1, 10) == 5

    def test_uses_default(self, monkeypatch) -> None:
        monkeypatch.setattr("builtins.input", _input_sequence([""]))
        assert get_number_input("count?", 1, default=3) == 3

    def test_enforces_minimum(self, monkeypatch) -> None:
        monkeypatch.setattr("builtins.input", _input_sequence(["0", "2"]))
        assert get_number_input("count?", 1) == 2

    def test_enforces_maximum(self, monkeypatch) -> None:
        monkeypatch.setattr("builtins.input", _input_sequence(["11", "9"]))
        assert get_number_input("count?", 1, 10) == 9

    def test_go_back_returns_none(self, monkeypatch) -> None:
        monkeypatch.setattr("builtins.input", _input_sequence(["b"]))
        assert get_number_input("count?", 1, allow_go_back=True) is None


class TestGetStringInput:
    def test_accepts_alphanumeric(self, monkeypatch) -> None:
        monkeypatch.setattr("builtins.input", _input_sequence(["abc123"]))
        assert get_string_input("name?") == "abc123"

    def test_rejects_empty(self, monkeypatch) -> None:
        monkeypatch.setattr("builtins.input", _input_sequence(["", "value"]))
        assert get_string_input("name?") == "value"

    def test_uses_default(self, monkeypatch) -> None:
        monkeypatch.setattr("builtins.input", _input_sequence([""]))
        assert get_string_input("name?", default="fallback") == "fallback"

    def test_validates_regex(self, monkeypatch) -> None:
        monkeypatch.setattr("builtins.input", _input_sequence(["@", "#"]))
        assert get_string_input("name?", regex=r"^#+$") == "#"

    def test_rejects_excluded(self, monkeypatch) -> None:
        monkeypatch.setattr("builtins.input", _input_sequence(["taken", "free"]))
        assert get_string_input("name?", exclude=["taken"]) == "free"

    def test_allows_special_chars(self, monkeypatch) -> None:
        monkeypatch.setattr("builtins.input", _input_sequence(["a-b_c"]))
        assert get_string_input("name?", allow_special_chars=True) == "a-b_c"

    def test_allows_empty_with_special_chars(self, monkeypatch) -> None:
        monkeypatch.setattr("builtins.input", _input_sequence([""]))
        assert (
            get_string_input("name?", allow_empty=True, allow_special_chars=True) == ""
        )


class TestGetSelectionInput:
    def test_from_list(self, monkeypatch) -> None:
        monkeypatch.setattr("builtins.input", _input_sequence(["b"]))
        assert get_selection_input("pick?", ["a", "b", "c"]) == "b"

    def test_from_dict(self, monkeypatch) -> None:
        monkeypatch.setattr("builtins.input", _input_sequence(["two"]))
        assert get_selection_input("pick?", {"one": 1, "two": 2}) == "two"

    def test_invalid_then_valid(self, monkeypatch) -> None:
        monkeypatch.setattr("builtins.input", _input_sequence(["z", "a"]))
        assert get_selection_input("pick?", ["a", "b"]) == "a"

    def test_invalid_type_raises(self, monkeypatch) -> None:
        monkeypatch.setattr("builtins.input", _input_sequence(["x"]))
        with pytest.raises(ValueError):
            get_selection_input("pick?", 123)  # type: ignore[arg-type]


class TestFormatQuestion:
    def test_includes_default(self) -> None:
        assert "default=5" in format_question("count", 5)

    def test_no_default(self) -> None:
        assert "count" in format_question("count")
        assert "default" not in format_question("count")


class TestValidateNumberInput:
    @pytest.mark.parametrize(
        "value,min_count,max_count,expected",
        [
            ("5", 1, 10, 5),
            ("1", 1, 10, 1),
            ("10", 1, 10, 10),
            ("3", 1, None, 3),
        ],
    )
    def test_valid(
        self, value: str, min_count: int, max_count: Any, expected: int
    ) -> None:
        assert validate_number_input(value, min_count, max_count) == expected

    @pytest.mark.parametrize(
        "value,min_count,max_count",
        [
            ("0", 1, 10),
            ("11", 1, 10),
            ("-1", 0, None),
        ],
    )
    def test_raises(self, value: str, min_count: int, max_count: Any) -> None:
        with pytest.raises(ValueError):
            validate_number_input(value, min_count, max_count)


class TestGetSecretInput:
    def test_returns_value(self) -> None:
        with patch("utils.input_utils.getpass", return_value="s3cr3t-token") as gp:
            assert get_secret_input("Token") == "s3cr3t-token"
        gp.assert_called_once()

    def test_reprompts_on_empty(self) -> None:
        with patch("utils.input_utils.getpass", side_effect=["", "  ", "tok"]) as gp:
            assert get_secret_input("Token") == "tok"
        assert gp.call_count == 3

    def test_allows_empty_when_requested(self) -> None:
        with patch("utils.input_utils.getpass", return_value="") as gp:
            assert get_secret_input("Token", allow_empty=True) == ""
        gp.assert_called_once()

    def test_uses_getpass_not_input(self) -> None:
        # a secret must never go through input() (which echoes to the terminal)
        with patch("utils.input_utils.getpass", return_value="tok"):
            with patch("builtins.input", side_effect=AssertionError("must not echo")):
                assert get_secret_input("Token") == "tok"
