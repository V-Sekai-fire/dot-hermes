# Style-gate recipes for prek.toml

All use existing tools. Put `exclude = "^(vendor/|patches/)"` at the top level
(the whitespace in a `.patch` is part of the patch).

## Baseline hygiene config

Checks that hold for most trees as they are, with no network fetch for the
first block:

```toml
[[repos]]
repo = "builtin"
hooks = [
  { id = "trailing-whitespace" }, { id = "end-of-file-fixer" },
  { id = "mixed-line-ending" }, { id = "check-merge-conflict" },
  { id = "check-added-large-files" }, { id = "check-yaml" },
  { id = "check-json" }, { id = "check-toml" },
]

[[repos]]
repo = "https://github.com/astral-sh/ruff-pre-commit"
rev = "<latest tag>"
hooks = [
  { id = "ruff-check", args = ["--isolated", "--select", "E9,F"] },
  { id = "ruff-format", args = ["--isolated"] },
]

[[repos]]
repo = "local"
hooks = [
  # gofmt -l exits 0 even when it lists files, so turn its list into a failure.
  { id = "gofmt", name = "gofmt", language = "system", entry = "bash -c 'out=$(gofmt -l \"$@\"); [ -z \"$out\" ] || { echo \"$out\"; exit 1; }' --", files = "\\.go$" },
]
```

- Pass `--isolated` to ruff: a user-level ruff config on the desk otherwise
  turns on rules CI never sees, and newer ruff defaults are wider than
  pyflakes. `E9,F` keeps it to syntax errors and real defects (unused
  imports and variables); fix those findings in a commit before the hook.
- Plain `gofmt -l -d` as an entry never fails; wrap it as above.

## C/C++ formatting

```toml
[[repos]]
repo = "https://github.com/pre-commit/mirrors-clang-format"
rev = "<same major as local clang-format>"
hooks = [ { id = "clang-format", types_or = ["c", "c++"] } ]
```

- Godot-style code: copy `.clang-format` from `4-entities/godot` (has
  `InsertBraces: true`); set `IncludeBlocks: Preserve` if `Regroup`
  reshuffles existing includes.
- Hand-formatted code: generate the config with
  `scripts/least_churn_clang_format.py <repo> --exclude <vendored>/`. Keep
  `SortIncludes: Never` and no `InsertBraces`, so the reformat is
  whitespace-only and a whitespace-stripped compare proves it.
- clang-tidy `readability-braces-around-statements` is the braces alternative
  but needs compile_commands.json; InsertBraces needs nothing.

## Ban `auto` in C/C++

No stock clang-tidy check bans `auto`, so use a pygrep hook:

```toml
[[repos]]
repo = "local"

[[repos.hooks]]
id = "no-auto"
name = "no auto in C/C++"
language = "pygrep"
entry = '^(?!\s*//).*\bauto\b'
files = '\.(c|h|cpp|hpp|cc|hh|cxx|hxx|inc)$'
```

The negative lookahead lets whole-line comments say "auto-rigging".
Replace each `auto` with the declared return type from the header
(`result<T>` aliases, nested structs like `skin::transfer_report`); a
named nested struct is nameable, check before reaching for `decltype`.

## Braces in JavaScript

Prettier has no braces option; ESLint with ONLY `curly: all` adds them
without imposing any other style:

```toml
[[repos.hooks]]
id = "eslint"
name = "eslint (curly)"
language = "node"
entry = "eslint --fix"
files = '\.(js|mjs|cjs)$'
additional_dependencies = ["eslint@<npm view eslint version>"]
```

`eslint.config.mjs`: `export default [{ files: ['**/*.js','**/*.mjs','**/*.cjs'], rules: { curly: ['error','all'] } }];`
written in the file's own indent. `--fix` emits `{break;}`; hand-adjust
to the file's existing `{ break; }` spacing. Lines inside template
strings are not code and stay untouched.

## CI workflow

```yaml
name: Static checks
on:
  pull_request:
  merge_group:
  push:
    branches: [main]
concurrency:
  group: static-checks-${{ github.ref }}
  cancel-in-progress: true
permissions:
  contents: read
jobs:
  prek:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<latest major>
      - uses: actions/setup-go@<latest major>   # only when a gofmt hook exists
        with:
          go-version-file: <dir>/go.mod
          cache: false
      - uses: j178/prek-action@<full tag, e.g. v3.0.2>
        with:
          extra-args: --all-files
```

- prek-action publishes full tags only (no moving `v3`); check with
  `git ls-remote https://github.com/j178/prek-action refs/tags/v3` before
  writing a major-only ref.
- A `TRACE Failed to extract metadata ...` line in the log is prek noise,
  not a failure; read the `....Passed` lines.
