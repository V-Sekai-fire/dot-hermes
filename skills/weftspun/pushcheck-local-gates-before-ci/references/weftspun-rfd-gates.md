# Weftspun RFD gates: what they flag and how to pass them

The `ci-*` manual-stage gates in manuals-weftspun compare against
`GATE_BASE` and only judge lines or files the branch changed.

## ci-line-length (`scripts/check_line_length.exs`)
- An added line in a `.ex`/`.exs` file, RFD prose included, may not exceed
  98 columns.
- A markdown table row cannot wrap. When cells push a row past 98, turn the
  table into a bullet list (`- `name`: issuer X, constrained to Y. Role
  Z.`) with 4-space continuation lines. Keep every fact the table held.

## ci-rfd-literals (`scripts/check_rfd_literals.exs`)
- Counts "churny" literals in RFD prose outside fenced blocks and outside
  `&{repo(...)}`, `&{file(...)}` and `&{pin}` spans. A changed file fails
  when its total rises, or when it adds any `file_line`, `branch` or `pr`
  literal at all (those three are strict).
- Common false positives:
  - `host.domain:PORT` matches `file_line` (`\.[A-Za-z]\w{0,5}:\d+`).
    Write "port 8443 on `host.domain`" instead.
  - A hex id with letters and digits, 7–40 characters long (Fly machine
    ids, short hashes), matches `sha`. Drop it or describe the thing
    ("the leader, the third machine").
  - `V-Sekai-fire/<repo>` matches `own_org`. Use `&{repo("<repo>")}`.
  - `#123` or `PR #12` matches `pr`.
- A pre-push sibling hook, `rfd-literals`, runs the same script against
  `${GATE_BASE:-origin/main}` on every push, so a `prek install -t pre-push`
  checkout catches these before CI.
- To find which literals a change added, re-implement the `@kinds` regexes
  in Python, run them over `git show origin/main:<f>` and `HEAD:<f>`, and
  diff the match lists per kind. That is faster than reading the diff by eye.

## ci-rulesets (`scripts/check_rulesets.py`)
- Resolves the repo as `--repo`, then `GITHUB_REPOSITORY`, then the
  `origin` remote, so it runs locally with no env setup. If the local copy
  of the script predates that change, set `GITHUB_REPOSITORY=owner/name`.
