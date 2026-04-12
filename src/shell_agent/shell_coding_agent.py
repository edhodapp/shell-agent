"""Shell coding agent entry point (scaffold).

The functional implementation will mirror aofire-python-agent's
coding_agent: build a target-specific system prompt from CLAUDE.md
plus shell target rules (sh-default, bash opt-out, zsh-refusal, Kate
Ward library allowlist, shellcheck/shfmt gates), run the
claude_agent_sdk query loop with a tool_guard, and escalate to Opus
on failure.

Enforces shellcheck auto-detected by shebang and shfmt in POSIX mode
(`-p -d`) for sh scripts, bash mode (`-d`) for bash scripts. Rejects
any task requesting zsh output with an explicit error.
"""

from __future__ import annotations

import sys


SCAFFOLD_MESSAGE = (
    "aofire-shell-coding-agent: scaffold only, not yet implemented"
)


def main() -> int:
    """Entry point for the aofire-shell-coding-agent CLI (scaffold)."""
    print(SCAFFOLD_MESSAGE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
