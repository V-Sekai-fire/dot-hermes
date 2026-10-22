#!/usr/bin/env python3
"""Find the clang-format config that changes the fewest lines of a repo's C/C++.

    python least_churn_clang_format.py <repo> [--exclude ggml/ --exclude vendor/] [--out style.json]

Greedy coordinate search: start from Google/4-space/100 columns, try each value
of each option, keep any change that lowers the count of removed lines, two
rounds. Prints the count per round and writes the winning style as JSON. Turn
it into .clang-format with one `Key: value` line per entry under `---` /
`Language: Cpp`. Then `clang-format -i` and compare whitespace-stripped files.
"""
import argparse, difflib, json, subprocess
from concurrent.futures import ThreadPoolExecutor

OPTIONS = {
    "BasedOnStyle": ["LLVM", "Google", "Chromium", "Mozilla", "WebKit", "Microsoft"],
    "ColumnLimit": [80, 90, 100, 110, 120, 0],
    "AccessModifierOffset": [-4, -2, 0],
    "PointerAlignment": ["Left", "Right"],
    "AllowShortFunctionsOnASingleLine": ["All", "Inline", "Empty", "None"],
    "AllowShortIfStatementsOnASingleLine": ["Never", "WithoutElse", "AllIfsAndElse"],
    "AllowShortLoopsOnASingleLine": ["true", "false"],
    "AllowShortBlocksOnASingleLine": ["Never", "Always"],
    "AllowShortCaseLabelsOnASingleLine": ["true", "false"],
    "AllowShortLambdasOnASingleLine": ["All", "Inline", "None"],
    "SortIncludes": ["Never", "CaseSensitive"],
    "IncludeBlocks": ["Preserve", "Regroup"],
    "NamespaceIndentation": ["None", "All", "Inner"],
    "FixNamespaceComments": ["true", "false"],
    "BinPackParameters": ["true", "false"],
    "BinPackArguments": ["true", "false"],
    "AlignAfterOpenBracket": ["Align", "DontAlign", "AlwaysBreak", "BlockIndent"],
    "AlignOperands": ["Align", "DontAlign"],
    "AlignTrailingComments": ["true", "false"],
    "SpacesBeforeTrailingComments": [1, 2],
    "ContinuationIndentWidth": [4, 8],
    "BreakBeforeBinaryOperators": ["None", "NonAssignment", "All"],
    "BreakBeforeTernaryOperators": ["true", "false"],
    "BreakConstructorInitializers": ["BeforeColon", "BeforeComma", "AfterColon"],
    "PackConstructorInitializers": ["BinPack", "CurrentLine", "NextLine", "Never"],
    "IndentCaseLabels": ["true", "false"],
    "LambdaBodyIndentation": ["Signature", "OuterScope"],
    "SpaceAfterTemplateKeyword": ["true", "false"],
    "SpaceAfterCStyleCast": ["true", "false"],
    "BreakBeforeBraces": ["Attach", "Linux", "Stroustrup", "Allman"],
    "EmptyLineBeforeAccessModifier": ["Leave", "LogicalBlock"],
    "MaxEmptyLinesToKeep": [1, 2],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--exclude", action="append", default=[])
    ap.add_argument("--out", default="least_churn_style.json")
    a = ap.parse_args()
    files = subprocess.run(["git", "ls-files", "*.c", "*.h", "*.cc", "*.cpp", "*.hpp"],
                           cwd=a.repo, capture_output=True, text=True, check=True).stdout.split()
    files = [f for f in files if not any(f.startswith(x) for x in a.exclude)]
    src = {f: open(f"{a.repo}/{f}").read().splitlines() for f in files}

    def cost(style):
        s = "{" + ", ".join(f"{k}: {v}" for k, v in style.items()) + "}"

        def one(f):
            r = subprocess.run(["clang-format", f"--style={s}", f], cwd=a.repo, capture_output=True, text=True)
            if r.returncode:
                return 10**6
            d = difflib.unified_diff(src[f], r.stdout.splitlines(), lineterm="", n=0)
            return sum(1 for l in d if l.startswith("-") and not l.startswith("---"))

        with ThreadPoolExecutor(8) as ex:
            return sum(ex.map(one, files))

    best_style = {"BasedOnStyle": "Google", "IndentWidth": 4, "ColumnLimit": 100}
    best = cost(best_style)
    print(f"{len(files)} files, start {best}")
    for rnd in range(2):
        for k, vals in OPTIONS.items():
            for v in vals:
                t = dict(best_style, **{k: v})
                c = cost(t)
                if c < best:
                    best, best_style = c, t
        print(f"round {rnd}: {best} lines")
    json.dump(best_style, open(a.out, "w"), indent=1)
    print(json.dumps(best_style))


if __name__ == "__main__":
    main()
