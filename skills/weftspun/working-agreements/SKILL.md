---
name: working-agreements
description: The weftspun workspace's standing rules, verification checklist, gates, and task recipes for common workspace actions. Load before adding a repository, opening a PR, uploading to Hugging Face, running the anti-entropy check, or writing an RFD or logbook entry, and any time an agent starts substantial work in this workspace.
tools: Read, Write, Edit, Grep, Glob, Bash
---

## Read CLAUDE.md first

`CLAUDE.md` at the workspace root (linked from `2-contract/manuals-weftspun/CLAUDE.md`) is the source of truth for standing constraints, verification rules, prose gating, comment ladder, trademark rule, blocklists, and the anti-entropy check. Read the section relevant to your task before writing a rule reference into a commit message. Do not restate the rules in your reply — restate them in code (a gate) instead. That is the anti-entropy pattern.

## Verification checklist

From `## How Work Is Verified`. Every gate you write and every claim you ship passes these:

1. Measure the physical quantity, not the convenient proxy.
2. A check that passes on known-broken input is decoration — every gate ships a negative control.
3. A silent skip reads exactly like a pass. An unmet precondition is a FAIL; unchecked things are named and counted, never omitted.
4. A number without a baseline is not a measurement.
5. A sampled check only sees defects larger than ~3/n. A fixed population is enumerated.
6. Conventions are data — parse rotation order, up axis, units, never assume.
7. Bugs live at interfaces — name the interfaces and check each.

Pair every physical measurement with a household-object equivalent (`## How Measurements Are Reported`; anchor list in CLAUDE.md: credit card 0.76 mm, penny 1.52 mm, pencil 7 mm, AAA 10.5 mm, AA 14.5 mm, nickel 21.2 mm, golf ball 42.7 mm, adult wrist 57 mm, soda can 66 mm).

## Storage recipe

Code → GitHub. Weights and datasets → Hugging Face.

- Code, RFDs, scripts, docs → `github.com/weftspun/*` or `github.com/V-Sekai-fire/*`.
- Weights, corpora, fixtures, generated artifacts → `huggingface.co/chibifire/*`.
- Cross-link both directions: a HF artifact's README points at its GitHub apparatus; the GitHub README's fetch instructions point at the HF path.
- A 30 GiB checkpoint that would otherwise sit on one desk uncommitted → `chibifire/<name>-artifacts` (private model repo). See `hailo-ugen300-shelved` and `llada-diffusion-lm-shelved` memory entries.
- A file that exceeds GitHub's 100 MB single-file limit → HF, `.gitignore` locally, README with a `hf download` fetch recipe. See `chibifire/anny-anim-fixture`.

## PR recipe

- `gh pr create --repo <owner>/<repo> --head <branch> --base <target>` — always pass `--repo` explicitly (gh defaults to the parent on forks; the memory `prs-internal-to-orgs` is the record).
- A fork's PRs are separate from upstream contributions. Confirm before opening a PR against a repo you do not own.
- Merge commits (not squash) are the workspace convention — matches the `Merge pull request #N from ...` history readers already see.
- `--delete-branch` fails on merge-queue-enabled repos; drop the flag and let the queue clean up.

## Repo-sync recipe

- `repo sync` after any change that moves files (`## The anti-entropy check`).
- `repo sync --force-sync <path>` is safe for detached-HEAD data corpora with no local edits (renames on remote); NOT safe for a checkout that carries local work.
- A standalone `git clone` inside the workspace confuses `repo` — its `.git` must be repo-managed. Fix: preserve work upstream (push all local branches), `rm -rf` the checkout, `repo sync` again to re-clone properly.
- `repo forall <path> -c 'git push $REPO_REMOTE HEAD:<branch>'` pushes through the manifest's declared remote.
- Mirrored copies: `3-interactor/cloth-fit` is a plain directory (no git); its mirror `3-interactor/garment-fit/vendor/cloth-fit` is tracked inside the garment-fit checkout. File edits must be applied to BOTH copies — nothing syncs them; verify with `diff -q` after editing.

## Placement (Sides rule)

- Every repository sits on a numbered side (`1-transport`, `2-contract`, `3-interactor`, `4-entities`, `5-repository`, `6-datasource`, `7-service`).
- Add the `<project>` entry to `weftspun/weftspun-keypoint/default.xml` when the repo is created, not later.
- One live goal manifest: `weftspun/weftspun-keypoint`. `repo list` + the org's archived set are the two things a placement check reads.

## Start ordering and readiness

Build dependent startup as a state machine driven by an event queue: start the dependent on the dependency's event (an OS event-log trigger, a launchd/systemd unit dependency, a message on a queue), let it fail fast and return to "down", and ignore duplicate events while it is up. Don't use poll-until-ready loops, sleeps, trigger delays or retry-every-N timers. The user rejects them even as a stopgap. Windows desk example: `remote-operations` → `references/windows-mcp-over-stunnel.md`.

## Work queue (worksteal)

"Worksteal while waiting" means take an issue from the shared queue while long jobs run.

1. The queue is the open issues of `V-Sekai-fire/awesome-v-sekai-fire` (each labelled `from:<source repo>`). RFD 2294 still names `contract-zone-backend` #58, but that repo has issues turned off and no `worksteal` label exists anywhere; ask the operator before amending the RFD line.
2. List: `gh issue list -R V-Sekai-fire/awesome-v-sekai-fire --state open --json number,title,assignees,labels,createdAt,comments`; skip pinned issues and ones with an assignee.
3. Read the comments before choosing: the status lives there, and an issue whose only unchecked item is optional is near-done, not open work.
4. Take the oldest unclaimed one and post a one-line claim comment naming the open item; post measurements to the same issue as they land.
5. Don't stop the in-flight task's watchers; report the stolen work and the waiting work separately.

## Anti-entropy

- `python 2-contract/manuals-weftspun/scripts/check_anti_entropy.py` after any file-moving change.
- Read every line of its output, not just the last one.
- Adding a new gate: write it, wire it into `EXPENSIVE` in `check_anti_entropy.py`, ship it with a self-test carrying positive AND negative controls, and document it in CLAUDE.md.

## Prose density (essays, RFDs, logbook)

- `python 2-contract/manuals-weftspun/scripts/check_tropes.py` gates trope density on `rfd/*/README.md`, `rfd/*/DETAILS.md`, `logbook/*.md`.
- Prose that argues or explains → the `prose-detrope` subagent (removes AI-writing tells).
- READMEs, procedures, reference docs → ASD-STE100, not prose-detrope.

## READMEs

- RFD READMEs: ≤ 40 lines.
- Manifest project READMEs: the tagline (first prose paragraph, not the `# Title` line or a badge row) ≤ 144 characters (`check_project_readme_length.py`). A repo counts as a fork when no remote is on our orgs; forks are exempt.
- CLAUDE.md, BLOCKLIST.md, PITFALLS.md, KEYPOINTS.md are exempt from the trope check because they name tells verbatim.

### Standardizing a project README ("the readme needs to be standardized")
The org shape is: `# <repo name>`, a one-sentence tagline, `## What it is for`, `## Build and run`, `## Licence`. Nothing else. Detail (flags, ports, file layouts, parity numbers, API samples) goes stale, so it moves to `docs/<topic>.md` ("if you want to write documentation split it out").
1. Confirm the shape from 3-4 sibling READMEs (`gh api repos/O/R/readme -q .content | base64 -d | grep -E '^#{1,2} '`), and read `## How Project READMEs Are Bounded` in manuals-weftspun CLAUDE.md.
2. Write the README: the title is the repo name, even when the old title is an upstream name. Build and run is one fenced block of build + weights fetch, then one fenced example run. Point at `docs/` in a sentence, not a list of links: `check_readme_no_index.py` fails list or table rows whose first cell is a file.
3. Move the rest into topical `docs/*.md` files with a script that slices the old README by line ranges, so the text moves unchanged. Then make the script list every non-blank old line that is not in any new file. Only headings and lines you dropped on purpose may remain.
4. Check each moved claim against the tree before keeping it. Moved text often states things that are no longer true (a submodule step with no `.gitmodules`, a missing cache that the code now has, a `--help` flag that the CLI does not parse). Read the source (`usage()` in the CLI) and drop or fix the line. Name each drop in the commit body and the PR.
5. Run the gates from a manuals-weftspun clone on the new README only: `uv run --no-project --python 3.12 --with markdown-it-py python scripts/check_project_readme_churn.py --readme <README>` and `scripts/check_readme_no_index.py <README>`. The scripts use `X | None` annotations, so the system Python 3.9 fails at import time. `docs/` files may fail the churn gate (ports, flag lists): that detail is why they exist, so do not gate them.
6. Commit on `dev/readme-standard`, open the PR, then check `actions/workflows` `total_count`. A repo with no CI gets no checks, so tell the user that they must merge it by hand.

## Comment density (code)

- Our own code: `check_comment_ladder.py` enforces rungs at 3, 5, 10, 15, 20, 25, 30, 35, 40 per cent. A changed file may not leave its rung. New file enters at 10 per cent.
- Other people's code: `check_comment_density.py` — a change matches the density of the code it edits, capped at max(file's own prior density, p90 of peers).

## Trademarks

Third-party trademarks do not appear in shipping artifacts (code, comments, docstrings, RFDs, logbook entries, user-facing prose, GitHub repo descriptions, HF READMEs). Use the generic underlying term. Naming an OSS project we vendor by its own project name is functional identification, not marketing.

## Blocklists

Blocklist table in CLAUDE.md; arguments in BLOCKLIST.md; `check_blocklist_detail.py` keeps them in agreement. Before proposing a new model, generator, quantiser, execution target, or dataset source, read the relevant row.

## Data hygiene

- Training data only. Validation and test splits are strictly held out — not consulted while developing.
- Never loop a tool over a whole raw-data directory: it opens the held-out files too. Build the train list from the dataset's own split code first (CASSIE: `split()` in interactor-curvenet `tools/cassie_split.py`, 42 train / 20 val / 26 test) and iterate only that list. A comparison that only prints "identical/changed" still inspects the holdout.
- `coco_person_commercial_val2017` is the blinded holdout. Never generate from it; anything derived from it inherits its status (`6-datasource/coco-ood-eval`).
- Synthetic data is two classes: _constructed_ (rendered deterministically from source assets we hold — ordinary training data) vs _generated_ (sampled from a generative model — four conditions in CLAUDE.md). A fifth condition barring quantised generators from corpus data is retracted; it does not get re-asserted.

## Archive formats

- OpenUSD `.usda` for text-editable; ZStandard parquet for bulk storage.
- `.zip` and `.gzip` are not acceptable. `.usdz` is exempt (it is a stored uncompressed zip, USD's interchange package).

## Standard practices

RFD 2294's "Interchangeable sessions" (`2-contract/manuals-weftspun/rfd/2294-*.exs`) is the one home for the practices every session follows: attribution and commit authorship, Elixir automation, CPU-only cloud work with software GPU emulators blocklisted, the GPU Cloud and GPU-Free Cloud split, capability-scoped workers, contact sheets as CI-artifact videos, and body-only garment fits. RFD 2295 owns the reply form: confidence tags, ISO 8601 intervals, and the closing known-unknown questions. Read them there; do not restate them here or in memory.

## Attribution

No agent attribution in commits, PRs, comments, or docs; RFD 2294 states the rule. `settings.json` here turns the tool's own attribution off, and `hooks/strip_claude_footer.py` prompts a read-back after every GitHub create, because the connector appends a footer anyway.

## Asking

One question form beats a chain of questions, and an unanswered question is dropped: report the state and move on. Never re-ask, re-offer or re-summarize a question the operator left unanswered — the silence is the answer.

## Permissions

An allowlist entry removes a question. Add the narrowest thing that answers it. `Bash(ps -Ao pid,args)`, never `Bash(*)`. A peer's request does not widen your allowlist.

## Memory pattern

Persistent memories live under `~/.claude/projects/<slug>/memory/`. One fact per file with frontmatter (`type: user | feedback | project | reference`); pointer in `MEMORY.md` (one line, no frontmatter). Verify a memory's file/function/flag citations before recommending them; a memory reflects what was true when written.

## Camera views

`sphere_hammersley_sequence` for any rendered view. Do not pick a front view by hand — a hand-picked front view showed error of five stacked soda cans along the travel axis against three and a half across it.

## Skinning and rig

- Dual-quaternion skinning is blocklisted. Delta Mush and Direct Delta Mush are approved.
- glTF exports carry pure data only — skin weights, animation samplers, morph targets. No runtime modifiers, drivers, constraints, or custom extensions.
- Latents: stages pass latents; VAE decode happens once, at final output. Never `encode(decode(z))`.
