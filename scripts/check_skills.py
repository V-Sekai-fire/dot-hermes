"""Gate: every skill is loadable.

A skill with broken frontmatter is not a weak skill, it is an absent one: the
loader skips it and nothing says so. The name must agree with the skill directory
it lives in, because the directory is the category and the skill's identity.

Usage:
    python check_skills.py
    python check_skills.py --self-test
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
# A line in the frontmatter must be `key` `:` `value`, value optional.
KEY_LINE = re.compile(r"^([A-Za-z][A-Za-z_-]*)\s*:\s*(.*)$")
REQUIRED = ("name", "description")


def frontmatter(text):
    if not text.startswith("---\n"):
        return None, "no frontmatter block"
    end = text.find("\n---", 4)
    if end < 0:
        return None, "frontmatter block is never closed"
    out = {}
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        m = KEY_LINE.match(line)
        if not m:
            return None, f"frontmatter line is not a key: {line[:40]!r}"
        k, v = m.group(1), m.group(2)
        out[k] = v
    return out, None


def skill_problems(path):
    """Problems with one SKILL.md. path is the file; the skill name is path.parent.name."""
    text = path.read_text(encoding="utf-8")
    fm, err = frontmatter(text)
    if err:
        return [f"{path.parent.name}: {err}"]
    bad = []
    for key in REQUIRED:
        if not fm.get(key):
            bad.append(f"{path.parent.name}: frontmatter has no {key}")
    if fm.get("name") and fm["name"] != path.parent.name:
        bad.append(f"{path.parent.name}: name is {fm['name']!r}, so the skill and its directory disagree")
    return bad


def find_skills():
    """All SKILL.md under skills/ that sit in a <category>/<name> directory."""
    found = []
    for p in SKILLS_DIR.rglob("SKILL.md"):
        if p.is_symlink():
            continue
        parts = str(p.relative_to(SKILLS_DIR)).split("/")
        # A skill sits at skills/<category>/<name>/SKILL.md; reject anything shallower
        # or a loose SKILL.md directly under skills/.
        if len(parts) >= 3 and p.name == "SKILL.md":
            found.append(p)
    return found


def run():
    if not SKILLS_DIR.is_dir():
        print("FAIL skills/ is absent")
        return 1
    skills = find_skills()
    if not skills:
        print("FAIL no skills found, so nothing was checked")
        return 1
    problems = []
    for p in sorted(skills):
        problems += skill_problems(p)
    cats = sorted({str(p.relative_to(SKILLS_DIR)).split("/")[0] for p in skills})
    for line in problems:
        print(f"  FAIL {line}")
    print(f"\n{len(skills)} skill(s) across categories {cats}, {len(problems)} problem(s)")
    return 1 if problems else 0


def self_test():
    import tempfile

    # (label, frontmatter text, is-clean) A control is a non-clean skill the gate must reject.
    cases = [
        ("a well-formed skill in a matching directory passes",
         "---\nname: a\ndescription: does a thing\n---\nbody\n", True),
        ("control: no frontmatter is caught", "body only\n", False),
        ("control: an unclosed block is caught", "---\nname: a\ndescription: d\n", False),
        ("control: a missing description is caught",
         "---\nname: a\n---\nbody\n", False),
        ("control: a name that disagrees with the directory is caught",
         "---\nname: other\ndescription: d\n---\nbody\n", False),
    ]
    all_ok = True
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "weftspun/a").mkdir(parents=True)
        f = root / "weftspun/a" / "SKILL.md"
        for label, text, is_clean in cases:
            f.write_text(text)
            probs = skill_problems(f)
            ok = (len(probs) == 0) == is_clean
            all_ok = all_ok and ok
            detail = f" ({'; '.join(probs)})" if probs else ""
            print(f"  {'ok  ' if ok else 'FAIL'} {label}{detail}")
    print(f"\n{'ok   ' if all_ok else 'FAIL '}{len(cases)} controls, both directions")
    return 0 if all_ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    sys.exit(self_test() if ap.parse_args().self_test else run())
