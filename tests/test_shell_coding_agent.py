"""Tests for the shell_coding_agent scaffold."""

from __future__ import annotations

import pytest

from shell_agent import shell_coding_agent


def test_scaffold_message_is_not_mutated() -> None:
    """SCAFFOLD_MESSAGE contains the expected substrings and no mutmut 'XX' wrapping."""
    msg = shell_coding_agent.SCAFFOLD_MESSAGE
    assert "XX" not in msg
    assert "scaffold" in msg
    assert "not yet implemented" in msg


def test_main_returns_zero_and_prints_message(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """main() prints the scaffold message and returns 0."""
    rc = shell_coding_agent.main()
    captured = capsys.readouterr()
    assert rc == 0
    assert shell_coding_agent.SCAFFOLD_MESSAGE in captured.out
