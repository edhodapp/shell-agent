# shell_agent — Project Instructions

## Purpose

`shell_agent` is a **shell script coding agent** that writes new POSIX
sh (or bash where needed) scripts to production standards. It is
**AGPL-3.0-or-later public sister to `python_agent`** and `asm_agent`, and
focuses narrowly on writing **new scripts from scratch** — not
modifying existing scripts in place.

Scripts produced by this agent target automation: pre-commit hooks,
CI helpers, deploy scripts, install probes, container entrypoints,
systemd helpers, and similar utility work. They are **not** intended
for interactive shell customization (`.zshrc`, `.bashrc`, prompt
theming) — that domain is explicitly out of scope.

## Sibling Projects

- **`python_agent`** — `~/python_agent`, AGPL-3.0-or-later, public at
  [github.com/edhodapp/python-agent](https://github.com/edhodapp/python-agent).
  Provides the discovery / divergence / convergence / planning agents,
  the DAG JSON format, `tool_guard`, `frame_data`, and the shared
  `coding_system_prompt` helpers. Installed here as a pip runtime
  dependency (`aofire-python-agent>=0.1.1` from PyPI).
- **`asm_agent`** — `~/asm_agent`, AGPL-3.0-or-later, public. Parallel
  sister project for bare-metal ARM64 / x86_64 / WebAssembly code.
  Same thin-wrapper pattern (pip-installs `aofire-python-agent`,
  adds one target-specific coding agent).
- **Cross-project coordination:** read `~/PRODUCTS.md` at the start
  of every session for the roadmap and code flow rules.

## Relationship to the ontology pipeline (important)

Unlike `python_agent`, `shell_agent` **does not use the discovery
→ divergence → convergence → planning ontology pipeline by default**.
Shell scripts are utility automation with well-defined scopes;
the design-first exploration that pipeline enables is overkill
for the typical shell task.

The agent accepts a task description on the command line and
writes a script. Optional `--plan-file <path>` lets the caller
prepend a plain-text plan as context, but no structured DAG is
required or consumed.

If a complex task genuinely needs the full pipeline, run
`aofire-discovery-agent` / `aofire-divergence-agent` /
`aofire-convergence-agent` from `aofire-python-agent` first,
then pass the resulting DAG JSON via `--dag-file` to
`aofire-shell-coding-agent`. The pipeline is opt-in, not default.

## Shell Target Rules

These rules are **the core of this agent's identity** and belong
in every generated script. They were locked in by the author on
2026-04-11 after discussion of the sh/bash/zsh trade-off space.

### Rule 1 — POSIX sh by default

The default shebang for every script is `#!/bin/sh`. The script
must parse cleanly under `shellcheck -s sh` and `shfmt -p` (POSIX
mode). No bashisms:

- No `[[ ]]` — use `[ ]` with proper quoting.
- No arrays (except `$@` and `$*`, which are POSIX).
- No `$'...'` C-style strings — use `printf` with explicit escapes.
- No `<<<` here-strings — use pipes or process substitution alternatives.
- No `<(cmd)` process substitution — use temp files via `mktemp`.
- No `${var,,}` / `${var^^}` case conversion — use `tr` or `sed`.
- No `${var:offset:length}` substring — use `cut` or `expr`.
- No `local` declarations outside functions (POSIX doesn't specify
  `local`, though most shells accept it; use it carefully inside
  functions and document the portability assumption).
- No `read -a` / `read -p` — use plain `read` and `printf` for prompts.
- No `trap ... RETURN`, no `trap ... DEBUG`, no `set -o pipefail`.
- Prefer `printf` over `echo` for anything that contains escapes,
  leading dashes, or backslashes.
- Always quote variables: `"$var"`, never bare `$var`.
- Exit with meaningful status codes; stderr-print errors before
  non-zero exits.

### Rule 2 — Switch to bash only for a concrete feature

Use `#!/usr/bin/env bash` when, and only when, the task requires a
feature that POSIX sh cannot reasonably provide:

- **Associative arrays** (`declare -A`): no sh equivalent.
- **`set -o pipefail`**: critical for multi-stage pipes in CI
  scripts that must fail on any stage.
- **Process substitution `<(cmd)`**: reasonable when temp files
  would materially complicate the script.
- **`[[ ... =~ ... ]]` regex**: acceptable when grep/sed equivalents
  are significantly less readable.
- **`set -o errtrace`** with `trap ERR`: if robust error handling
  requires it.

When switching to bash, the top of the script must include a
short comment explaining which feature forced the switch:

```bash
#!/usr/bin/env bash
# shell_agent: bash required for associative arrays; sh cannot express this cleanly.
set -euo pipefail
```

**Bash 3.2 compatibility is the default** — stick to features that
work on macOS's ancient stock bash (from 2007). Opt out only when
the task explicitly says "Linux-only, bash 4+ OK." That means:
**no** `declare -A` (bash 4+), `readarray` / `mapfile` (bash 4+),
`${var,,}` (bash 4+), `&>>` (bash 4+), named references
(`declare -n`, bash 4.3+), `$EPOCHSECONDS` (bash 5+).

### Rule 3 — No zsh

`shell_agent` **refuses to generate zsh scripts**. Reasons:

- Zsh's 1-indexed arrays vs. bash's 0-indexed arrays is a landmine.
- Zsh's value is interactive UX, not automation scripting.
- Every Linux CI/container/server is bash or dash, never zsh.
- Testing zsh adds another shell toolchain to the gate suite.

If a task asks for zsh, the agent must refuse explicitly and
suggest the user write it by hand. Do not guess at zsh syntax.

## Library Allowlist (Kate Ward's ecosystem)

Kate Ward's shell libraries at [github.com/kward](https://github.com/kward)
are high-quality, POSIX-friendly, and the right first-choice when
their purpose matches the task. They're Apache 2.0 licensed
(compatible with AGPL-3.0).

### `shunit2` — default test framework

Unit tests go in `shunit2` format. `shunit2` is fully POSIX sh
compatible (unlike `bats-core`, which is bash-only), matches the
sh-default ethos of this project, and has been stable for 15+
years. Test files use the `*_test.sh` naming convention.

A script has "logic worth testing" when it contains any non-trivial
conditional branching, string manipulation, or control flow. Pure
linear "run three commands in order" scripts can skip tests.

### `shflags` — CLI flag parsing for 4+ flags

Use `getopts` for scripts with 0-3 flags; switch to `shflags` at 4+
flags or whenever typed arguments and auto-generated `--help` output
would materially improve the script. `shflags` is POSIX-friendly and
avoids the getopts boilerplate.

### `shlib` — targeted portability utilities

Contents known:
- `shlib_relToAbsPath` — relative-to-absolute path conversion.
  **Use when** the script needs portable path normalization; sh
  has no built-in and BSD `readlink` lacks `-f`.
- `versions` — shell/OS detection. **Use when** a script must branch
  on GNU vs. BSD coreutils or detect bash version.
- `test_runner` — discovers and runs `*_test.sh` shunit2 tests.
  **Use when** setting up a test suite that follows the shunit2
  naming convention.

Don't reach for `shlib_ansi`, `shlib_random`, `sgrep`, or `which`
— POSIX built-ins (`command -v`, `printf`, `$RANDOM` in bash,
`od /dev/urandom` in sh) cover these cases without a dependency.

### `log4sh` — do not use by default

Structured logging is overkill for the utility scripts this agent
produces. Use `printf "ERROR: %s\n" "$msg" >&2` and meaningful exit
codes instead. Only reach for `log4sh` if the task explicitly
describes a long-running daemon-like script with log aggregation
requirements — at which point, consider whether shell is even the
right language.

## Mandatory Quality Gates

Every script produced must pass, before it leaves the agent:

1. **`shellcheck`** — auto-detects dialect from the shebang:
   - `#!/bin/sh` → enforces POSIX sh rules.
   - `#!/usr/bin/env bash` → enforces bash rules.
   During development, run `shellcheck -s sh` on bash-shebanged files
   to confirm the script would work if reduced to sh — this catches
   accidental bashisms that weren't load-bearing. Commit only when
   the shebang-matched pass is clean.
2. **`shfmt`** — auto-detects dialect from the shebang:
   - `#!/bin/sh` → `shfmt -p -d` (POSIX parse, diff mode).
   - `#!/usr/bin/env bash` → `shfmt -d` (bash parse, diff mode).
   Fail on any diff output.
3. **`shunit2` tests** — required when the script has logic worth
   testing. Tests live alongside the script as `*_test.sh` files.
4. **Every script starts with `set -eu`** (sh) or `set -euo pipefail`
   (bash). Strict mode is not optional.

## Python Quality Standards

All Python code in this repo (the agent itself) meets the same
standards as `aofire-python-agent`:

1. **flake8 clean** — `.venv/bin/flake8 --max-complexity=5`
2. **McCabe Cyclomatic Complexity <= 5**
3. **100% branch coverage** —
   `.venv/bin/pytest --cov --cov-branch --cov-report=term-missing`
4. **pytest** for all tests; **pytest-mock** for mocking
5. **Mutation testing with mutmut** (v2) — 100% kill rate once
   functional code lands. Only `if __name__` guard may survive.
   Use `"XX" not in output` to kill string mutants.
6. **Fuzz testing with hypothesis** — every function accepting
   external inputs gets a `@given(...)` test verifying no
   unhandled exceptions, correct return types, and invariants.
7. **mypy --strict** — `.venv/bin/mypy --strict src/`, zero errors.
8. **Call graph taint analysis** — `.venv/bin/aofire-call-graph src/`
   (from the installed `aofire-python-agent` package).
9. **Functional test gap analysis** — read every function and every
   test; enumerate all paths; write tests to close the gaps.

See `~/python_agent/CLAUDE.md` for the full rationale. This project
inherits the standards verbatim; any deviation is a bug.

### Venv

Always use the project venv: `.venv/bin/python3`, `.venv/bin/pytest`,
`.venv/bin/flake8`, `.venv/bin/mypy`. Never system Python.

### Before Committing

```bash
.venv/bin/flake8 --max-complexity=5
.venv/bin/mypy --strict src/
.venv/bin/pytest --cov --cov-branch --cov-report=term-missing
```

## Correctness

These are foundational.

- **No one writes correct code — not humans, not AI.** Confidence
  without evidence is the most dangerous state.
- **A programmer's critical job is proving their code is correct.**
  Trust nothing without verification.
- **Failure handling code that is never tested is a liability.**
- **Prefer parameters over hardcoded values.**
- **An accidental fix is not a fix — it's a clue.** Ask WHY a change
  affects behavior before shipping it.
- **Trace symptoms to code paths, not external theories.**

## Testing Philosophy

- **Tests are part of the implementation, not a follow-up.**
- **Both sides of every conditional.**
- **Every test MUST have a meaningful assertion.**
- **Test from multiple angles.**
- **Reproduce runtime bugs in tests first** — red → green → commit.
- **Mutation testing is the proof.**

## Working Style

- Trunk-based development: commit directly to `main`, push after
  each group of changes.
- Don't suggest breaks or stopping.
- When you catch a mistake or unintended change — stop. Understand
  what changed and why. Don't rationalize differences away.
- Never check files into the wrong repo by drifting directories.
- Always check if a target file exists before `mv`/`cp`/`Write`.
- Never hide unexpected messages or errors — fix the source.
- Revert failed experiments immediately.

## Git

- Commit after every group of code changes. Don't wait to be asked.
- Use the git `user.name` and `user.email` configured on the system.
- **Public AGPL-3.0-or-later repo.** Nothing proprietary belongs here.
  Follow the one-way code flow rules in `~/PRODUCTS.md`: code can
  flow FROM this project INTO proprietary ones, never the reverse.
