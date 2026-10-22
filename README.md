# dot-hermes

The Hermes agent skill home for the weftspun workspace, checked out at `.hermes/` by
repo. It holds the weftspun skills in the `skills/<category>/<name>/SKILL.md` form and
the repo gate that keeps every skill loadable.

## What it is for

Hermes reads skills from the local store at `~/.hermes/skills`, so this checkout is the
git-kept, workspace-visible source for the weftspun category. The working agreements and
what an agent may do without asking live in `manuals-weftspun` (AGENTS.md); RFD 2294
states the standard practices. Unlike the old `.claude` checkout, this one carries no
Claude permission set; Hermes applies its config from the local profile, not from a
workspace file.

## Skills

Each skill is a directory under `skills/<category>/`, named after its frontmatter
`name`, with a `SKILL.md` and optional `references/`, `scripts/`, or `assets/` support
files. The category is the directory name, so the loader and the repo agree on where a
skill lives.

## Build

```sh
python scripts/check_skills.py --self-test
python scripts/check_skills.py
```

## Licence

MIT; see `LICENSE`.
