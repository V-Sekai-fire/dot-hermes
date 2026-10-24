---
name: pushcheck-local-gates-before-ci
description: "Use before git push, on red prek CI, or adding prek."
---

# pushcheck — local gates before CI

CI is the wrong place to catch a formatter, a missing include, or a
copyright-header violation. Every one of those is a mechanism that
already exists on the desk — the `.pre-commit-config.yaml` prek picks
up, the SCons that compiles the module, the CMake that links the
library. RFD66606-2229's retro named the pattern: **a part with no caller
is not yet a part.** `pushcheck` is that caller.

## Reflex

Before `git push`, always:

    pushcheck && git push -u <remote> <branch>

The `&&` matters. A failed check has to be a hard stop.

Before opening a PR from a branch with many commits (especially right after a rebase onto
`main`), run `prek run --all-files` once, the same form CI runs. A run on the last diff only
checks the files in that diff, so formatter drift in earlier commits on the branch reaches
CI. Commit whatever it rewrites as a separate formatting-only commit.

## What it runs

The shell function in `~/.zshrc` sniffs the project type and runs the
gates that apply to what actually changed:

1. **prek** on the diff, whenever a `.pre-commit-config.yaml` exists in
   the checkout root. That covers clang-format, ruff-check + ruff-format,
   mypy, codespell, validate-codeowners, validate-includes,
   copyright-headers, header-guards, file-format — the whole
   static-checks bank.
2. **scons real compile** for a Godot fork (`SConstruct` at root and
   any changed file under `modules/<name>/`). Compiles just the affected
   module's static library, so the check finishes in seconds on a warm
   sccache. Not `--dry-run` — `--dry-run` only parses SConscript, and the
   class of failure that ate three CI cycles this session (missing
   `#include "core/object/class_db.h"`) only shows up when the C++
   actually goes through the compiler.
3. **cmake real build** for a CMake project (`CMakeLists.txt` at root
   and any changed C/C++/CMake file). Configures into
   `.build/pushcheck/` once, then rebuilds.
4. **mix compile + test** for an Elixir project (`mix.exs` at root and
   any changed `.ex`/`.exs`/`.eex` file). Uses `--warnings-as-errors`
   because a warning survives to CI as a failure.

Exits non-zero on the first violation; prints `pushcheck: green` on
success and returns 0 so it composes with `&& git push`.

Step 0 (before the changed-files check, so never skipped) fails when any
remote URL carries credentials (`https://x-access-token:ghs_...@github.com`).
Those one-hour tokens expire and then every push fails with "Invalid username
or token"; it prints the `git remote set-url` fix. Remotes stay plain and the
credential helper mints tokens. Verified on a planted token URL (fails), a
plain https remote and an ssh remote (both pass).

Never chain `pushcheck; gh pr create`: use `&&`, a `;` opens the PR on a red
check.

## Install the hooks, then run CI's manual stage locally

The user wants failures caught on the desk, not in CI ("install prek so we
fail earlier"). Do both steps for every checkout you touch:

1. **Install both hook types.** A checkout often has only `pre-push`, so
   commit-stage gates (e.g. `line-length`) never run. Check with
   `ls .git/hooks | grep -v sample`, then:

       prek install -t pre-commit -t pre-push

2. **Run the CI-only gates by hook id.** Gates marked `stages: [manual]`
   (the `ci-*` set in manuals-weftspun) run in neither hook. Copy the hook
   list from the workflow's `prek run` line and supply the env CI sets:

       GATE_BASE=origin/main GATE_BRANCH=<branch> \
         prek run --all-files --hook-stage manual <ids from checks.yml>

   Strip ANSI with `sed 's/\x1b\[[0-9;]*m//g'` before reading the output.
3. To see the failing gates on a PR, run `gh run view <id> --log-failed` and
   look for `Failed` and the lines after `- hook id:`.

A gate that fails locally only because a CI env var is unset is a weak
gate. Fix the gate itself rather than exporting the variable once by hand:
resolve the value as `--flag`, then the env var, then something derived
(for example `git remote get-url origin` parsed to `owner/name`). If none
of those gives a value, FAIL with a message that names the three sources.
Never fall back to a hardcoded default, which goes stale when the repo is
renamed and then checks the wrong target. Add controls for both the
precedence order and the empty cases.

**Promote a CI-only gate into pre-push** when it fails a PR that a local
hook could have caught. Add a sibling hook running the same script with
`--base "${GATE_BASE:-origin/main}"`, `pass_filenames: false`,
`always_run: true`, `stages: [pre-push]`. Use `always_run`, not a `files:`
filter: on a new branch's push the filter can skip the hook, and a skip
reads as a pass. Prove it both ways before the PR: `prek run --all-files
--hook-stage pre-push <id>` passes on the clean branch and fails on a
throwaway branch with a planted `--no-verify` commit of the bad literal.
Then push for real and confirm the hook line appears in the push output.
Put this on its own branch/PR, not on the PR being fixed.

**Prove a hook can fail before trusting its pass.** Read the hook's
`entry` and run it once by hand: a bare `lake build` in a package with
no `@[default_target]` prints "Nothing to build" and exits 0, so it
certifies any Lean change. Fix the build config, not the hook line
(mark the libraries and exes the repo ships as `@[default_target]`), then
run the hook through prek with a planted type error (`prek run <id>
--files <file>` must say Failed) and again clean (Passed). Likewise a
hardcoded toolchain path in a build script (a Windows `LEAN_INC`) makes
the hook fail on every other OS: resolve it from the tool
(`lean --print-prefix`) with an env override. Note that a script that
`cd`s to its own dir first resolves relative paths from there.

**A CI cache that outlives its toolchain fails the PR, not main.** A
cache keyed only on a lockfile hash (Dialyzer PLTs under
`hashFiles('mix.lock')`) is restored into a runner whose setup action
installed a newer patch release, and the tool rejects it ("Old PLT
file"). A rerun hits the same cache, so don't rerun: compare the
installed version in the failing log with main's last green run, then
put the installed version into both `key` and `restore-keys` (give the
setup step an `id` and use `steps.<id>.outputs.otp-version`).

What a specific weftspun RFD gate flags, and how to rewrite the prose so
it passes: `references/weftspun-rfd-gates.md`.

## Adding prek to a repo that has none

When the user requests "add prek" (often with style rules like "enforce
the style as is", "ban X", "always braces"):

1. **Config is `prek.toml`** (prek's own format, recommended by
   prek.j178.dev for new projects), not `.pre-commit-config.yaml`. Use
   array-of-tables `[[repos.hooks]]` form; `prek util yaml-to-toml` converts
   an existing YAML but drops comments. Check with `prek validate-config prek.toml`.
2. **Enforcement runs in GitHub Actions** via `j178/prek-action` in
   `.github/workflows/static_checks.yml` (on `pull_request` + push to main,
   `extra-args: --all-files` for small repos). The PR's green check is the
   verification; don't substitute a long local build for it.
3. **"Style as is" = an existing formatter configured so today's code is a
   no-op.** Never write a custom formatter. Pick the nearest upstream config
   (Godot's `.clang-format` for tab/`Type *x` C++), run it, and tweak only the
   keys that churn (e.g. `IncludeBlocks: Preserve`) until `clang-format f |
   diff f -` is empty. Exclude `vendor/`.
   - With a bare "add prek" (no style rule named), start with checks that
     hold for the tree as it is: prek's `builtin` hooks (whitespace, EOF,
     line endings, merge markers, large files, YAML/JSON/TOML), a narrow
     linter (`ruff check --isolated --select E9,F`), and the language's own
     formatter only where it is already a no-op (gofmt). Measure a C++
     formatter first: loop a few base styles over the non-vendored files and
     count changed lines.
   - The user wants the formatters in, even on hand-formatted code where
     every style rewrites thousands of lines: offering to defer the reformat
     only costs a round trip (the reply is "add"). Search the clang-format
     options for the least-churn config with `scripts/least_churn_clang_format.py`,
     write it to `.clang-format` with a comment that it matches the existing
     hand formatting, apply it with `ruff format --isolated` for Python, and
     land it on its own branch (reformat commit first, hook commit second).
     Prove the reformat changed no code: whitespace-stripped content of every
     file equal before and after (the only allowed difference is `\`
     continuations when a one-line `#define` is split), then build and run
     the tests once. Pin `mirrors-clang-format` to the same major as the
     local clang-format, so the hook agrees with the tree you formatted.
   - Exclude vendored trees and `patches/` (the whitespace in a `.patch` is
     part of the patch). Recipes and tool traps (ruff `--isolated`, gofmt's
     exit code, prek-action tags):
     `references/adding-prek-style-gates.md` ("Baseline hygiene config").
4. **Rules a formatter lacks become a lint, not a formatter.** Recipes in
   `references/adding-prek-style-gates.md` (braces, ban `auto`, JS `curly`).
5. Prove every gate Failed on a planted fault, fix the tree, commit fixes
   and the gate config as separate commits (fixes first, so each commit is
   green), push, then confirm in the job log that each hook printed Passed
   (not Skipped): `gh api --allow-escape-sequences
   repos/O/R/actions/jobs/<job>/logs | sed 's/\x1b\[[0-9;]*m//g' | grep -E
   'Passed|Failed|Skipped'` (`gh run view --log` can come back empty right
   after the run ends).
6. `git add` the new `prek.toml` and workflow before the final local run:
   prek only sees tracked files, so check-toml and check-yaml report "no
   files to check" on the untracked config and its first CI run is the
   first time they run.

Pitfalls found adding prek to skin-tokens-ggml:
- "Style as is" for hand-formatted C++ with no near upstream config: search clang-format keys
  greedily (try each value, keep it if fewer lines change; ColumnLimit 0, `SortIncludes: Never`,
  `AlignAfterOpenBracket: DontAlign` helped most). It still churned ~2,900 of 14,800 lines, so
  report the count and let the operator decide on the reformat. Prove it whitespace-only by
  comparing each file with all whitespace stripped (macro `\` continuations are the only allowed
  extra), then build and run the tests.
- `gofmt -l` exits 0 while listing files: wrap it, `bash -c 'out=$(gofmt -l "$@"); [ -z "$out" ] || { echo "$out"; exit 1; }' --`.
- ruff 0.17's default rule set is wide and a user-level ruff config leaks in locally: pin hooks with
  `--isolated` and an explicit `--select` (E9,F = syntax errors and pyflakes).
- After a reformat PR merges with a merge commit (SHA kept), add `.git-blame-ignore-revs` with the
  full SHA in its own PR; check with `git blame --ignore-revs-file` (324 -> 3 lines in one file).
- Exclude vendored trees (`ggml/`, `patches/`) in `prek.toml` only. Do not add `linguist-vendored`
  or other `.gitattributes` marks unasked: the operator rejected it.

Stage a planted file (`git add`) before `prek run --files` on it: prek
detects a fixer's change from the git diff, so an untracked file it
rewrites still reports Passed.

## Why this is a skill and not a habit

Because the pattern lives in muscle memory and muscle memory doesn't
survive a coordinator handoff. The last three pushes without it cost:

- PR #79 in `V-Sekai-fire/entities-godot` — three CI cycles for
  clang-format (`Type& var` should be `Type &var`), then
  copyright-headers (Godot's canonical MIT block, not SPDX-only),
  then CODEOWNERS (six new `modules/<name>/` lines), then a real
  build failure (missing `#include "core/object/class_db.h"`),
  every one of which prek + a real scons compile would have caught
  locally in under 15 seconds. Wall-clock cost: ~45 minutes of
  operator wait plus a stuck PR closed and reopened at narrower scope.
- `V-Sekai-fire/weftspun-character-taxonomy#3` — a prek check ran
  green on second attempt because the first push was rushed. One
  CI round-trip avoidable.
- Every prior push through `V-Sekai-fire/*` this session where
  formatting drift landed on the desk before the reviewer.

None of these were compute-bound. Every one was operator round-trip
bound.

If a push updates the branch ref (`git ls-remote`) but
`gh pr view --json headRefOid` stays on the old SHA and no `pull_request`
run starts, check `gh pr view <n> --json state,mergedAt` FIRST. The usual
cause is that the operator merged on green seconds before the push; a
merged PR never takes new commits. Then cherry-pick the stranded commit
onto a fresh branch from `origin/main` and open a new PR. Do not call it
GitHub lag or broken checks until state shows OPEN (githubstatus.com
confirms the rest). `pushcheck` is not new mechanism — it's the caller that turns
the mechanism the workspace already ships into the fast feedback the
operator already needed.

## When it doesn't apply

- **First-touch of a repo you don't own.** No `.pre-commit-config.yaml`,
  no `SConstruct`, no local build. `pushcheck` reports "no changed
  files" or skips the compile step; that's honest, not a bypass.
- **Docs-only diffs.** `pushcheck` still runs prek on the touched
  Markdown / YAML / .exs files — that catches the copyright-headers
  and file-format issues just as often as it catches clang-format —
  and skips the compile step because no source changed. Fast.
- **A CI check the desk cannot reproduce.** Multi-platform builds
  (Android, iOS, Windows-MSVC on a Mac desk), signed release
  workflows, secret-dependent integration tests. `pushcheck` covers
  the local subset honestly and CI covers the rest; that's the
  boundary, not a failure of the pattern.

## Related

- RFD66606-2229's retro passage names the exact pattern: "a part with no
  caller is not yet a part." `pushcheck` is that caller.
- `~/.local/bin/gh-app` mints the token the push uses; `pushcheck`
  runs before that step, no auth required until the push itself.
- The `.pre-commit-config.yaml` files (46 of them across the
  workspace) are the mechanism side; `pushcheck` is the caller side.
- CLAUDE.md's "How Work Is Verified" rule 3: "A silent skip reads
  exactly like a pass" — `pushcheck`'s "no changed files" print and
  "green" print are named and distinct on purpose.
