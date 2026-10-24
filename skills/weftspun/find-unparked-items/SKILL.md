---
name: find-unparked-items
description: Survey and triage the workspace's RFDs and tasks. Separates the queue (open board RFDs) from the backlog, shelved and closed items, and builds the study on the org inventory's journals. Use when the operator asks "what's unparked", "what's active", "what's left", "zoom out", "what's the queue look like", "study rfds", "triage" or "wind down the least important work".
tools: Read, Grep, Glob, Bash
---

# Find unparked items

"Parked" is not a canonical RFD66606-1000 state (RFD66606-1000 lists prediscussion,
ideation, discussion, published, committed, abandoned, moved — no
`parked`). Parked means backlog: the RFD stays open and has no
`flight_level`, so it is off the board. Active means open and on the board. Task-list items carry a
`[PARKED · <reason>]` subject prefix and metadata `parked: true` with an
`unpark_when` field, or are deleted from the list when the operator wants
a truly empty queue.

An **unparked** item is one that is either in the task list without the
`[PARKED]` prefix, or an open RFD with a `flight_level` (it shows on
`mix rfd.board`). That is the queue.

## When to invoke

The operator asks about queue state — "what's unparked", "what's left",
"what's active", "what's the task list", "zoom out" (for the queue part
of the answer), or "is anything blocking budget X".

## Work-stealing ("worksteal")

The live shared queue is the open issues of `V-Sekai-fire/awesome-v-sekai-fire` (labels `from:<repo>` name the source repository); the `worksteal` label on contract-zone-backend that RFD66606-2294 names no longer exists (issues disabled there). Steal the oldest unclaimed, unpinned issue: `gh issue list -R V-Sekai-fire/awesome-v-sekai-fire --state open --json number,createdAt,assignees,isPinned,comments`, read its last comment for the open item, claim it with a comment naming the item you take, and post measurements back to the issue as they land. If the queue cannot be found, ask where it lives rather than inventing work.

## Where to look

**Task list** — call `TaskList` (or read the injected task-status reminder
if one is already present). Subject lines with `[PARKED · ...]` are
parked; without it, unparked.

**RFD sources** — `2-contract/manuals-weftspun/rfd/<N>-<slug>.exs`. The
`.exs` is what is tracked; `README.md` is a `mix rfd.render` artifact
(RFD66606-2232) and is absent until the render runs. An unparked RFD has an
open state AND a `flight_level` line. An open RFD without one is backlog.

## Pipeline

**1. Task list.** Show the pending tasks not prefixed with `[PARKED`.
Grouped by parent RFD OID when the subject carries one
(`urn:oid:1.3.6.1.4.1.66606.1.2.NNNN`).

**RFD survey.** Run `mix rfd.board` in `2-contract/manuals-weftspun` first (`ERL_COMPILER_OPTIONS='[nowarn_deprecated_catch]'`, pixi on PATH). It prints every RFD that has a `flight_level`, sorted by level, and marks the operator's sequenced ones `step N`. The step list is `@critical_path` in `lib/rfd/board.ex`, and `--check` fails on drift. The board is the queue. Open RFDs with no `flight_level` are backlog. Smoke-water's register (`2-contract/manuals-smoke-water/rfd/30NN-*.exs`) is separate and private, so report it apart from weftspun. For the full census — board / backlog / shelved / closed across both trees in one read — use the inventory's committed `sql/` dump and `txn_flat` (recipe and report shape in `references/inventory-census.md`); it classifies each RFD from the same tags the board does, so the whole set is one read, not a per-file re-parse.

Read state from the tracked `.exs`, never from rendered READMEs, which may be stale or absent. The header line is `rfd N, "<title>", :<state> do`:

    grep -h -oE '^rfd [0-9]+, .*, :[a-z_]+' rfd/*.exs | grep -oE ':[a-z_]+$' | sort | uniq -c
    grep -l -E '^\s*Shelved [0-9]{4}-[0-9]{2}-[0-9]{2}:' rfd/*.exs     # shelved set

Open means `:prediscussion`, `:ideation` or `:discussion` with no `Shelved` line. Filter
further to just the RFDs the current operator opened this session by
cross-referencing PR authorship (`gh pr list --author '@me' --state all`
against the merged-PR list).

**3. Cross-reference with merged PRs.** An RFD in the survey with a
merged PR for it in the last session (or with a `State: committed`) is
delivered, not unparked. Distinguish "unparked and delivered" from
"unparked and open".

**4. Report by tier.** Group unparked items by the tier they occupy in
the current session's dependency chain (foundation → fix → port → ship →
Rung 2). See [[register-rfd-under-pen-oid]] for the OID structure that
makes cross-referencing possible.

## Studying and triaging RFDs: use the inventory

When the operator asks to study the RFDs, or to triage them (keep / defer / park / drop), build on the org inventory `6-datasource/inventory` (`datasource-inventory`). Do not write a throwaway table script: the operator rejects that. The inventory is a split SQLite dump in tackler shape, and its tools are Elixir: `load.exs`, `save.exs`, `replace_journal.exs <journal> <file.txn>`, and `github_inventory.exs` as the generator to copy.

1. Load it: `elixir tools/load.exs $TMPDIR/inv.db`. Then query the views `txn_flat(code, description, tags)` and `stock(commodity, account, quantity)`, and the table `txn_comment`.
2. Get repo activity from the `github` journal: the `last push YYYY-MM-DD` comment and the `active`/`archived` tags. Do not make one `gh api` call per repo.
3. RFDs live in the `rfd` journal, written by `tools/rfd_inventory.exs <workspace root>` (shape and pitfalls: the inventory reference file of skill `chibifire-smoke-water`). Each RFD sits in `Assets:RFD:<site>:Board:L1|L2|L3` (active), `:Backlog` (open, no flight level) or `:Closed:<State>`. Run `elixir tools/rfd_inventory.exs <root> --check` first: it must say every RFD sits where its source puts it.
4. **Triage only the active set** (the `Board:*` accounts). Backlog is out of scope unless the operator names it.
5. List the active set with its first decision sentence and newest named-repo push, using one SQL query over `txn_flat` + `txn_comment` joined to the `github` journal's `last push` comments. Read the RFD source only where the decision sentence isn't enough.
5a. **Confirm idleness live before proposing park or drop.** Most RFDs carry no `names-repo` tag, and RFDs written after the last snapshot are missing from the inventory, so a missing push date means unknown, not idle. Treat "unknown" as its own group in the report. Then, for every park candidate, read the live activity in two bulk calls and map repos and Hugging Face artifacts to the RFD by topic, not by tag:
   - GitHub: `gh api 'orgs/<org>/repos?sort=pushed&per_page=100' --paginate -q '.[]|"\(.name) \(.pushed_at[:10])"'` for V-Sekai-fire and chibifire-stages.
   - Hugging Face: `curl -s 'https://huggingface.co/api/<models|spaces|datasets>?author=chibifire&sort=lastModified&direction=-1&limit=40'`. Much of the org's work lands only as models, Spaces and datasets.
   Also grep each candidate's source for repo names (`interactor-*`, `entities-*`, `contract-*`, ...) and check their push dates. A shared repo such as `godot-sandbox` is weak evidence, so say that when you rely on it. Only propose parking an item when nothing on either site has moved for it. When there's doubt, list it as "quiet, can't confirm" and ask the operator where its work lives.
5b. **Running work counts as work in progress too.** Check `ps -Ao pid,etime,%cpu,rss,command -r | head`, open PRs (`gh search prs --owner <org> --state open`), checkouts on a branch or with uncommitted changes (`repo forall -c ...`), and `launchctl list` for the user's agents. Read the stderr log of a launchd job with a non-zero exit. Jobs that keep failing (missing script, bad argument, output already there, a service that moved hosts) are the clearest wind-down candidates. Unload them only after the operator rules.
6. Propose verdicts as plain grouped lists (keep / close / drop / park, each with a short reason), and default anything the operator doesn't contest to the proposal. Edit nothing before the ruling. Then apply the verdicts in the RFD sources as one PR per register:
   - **Park = backlog:** remove the `flight_level` line, and keep the state open.
   - **Close:** state `:committed`, when the work shipped.
   - **Drop:** `:abandoned`, naming the replacement when it was superseded.
   - **Defer:** a bullet in the dev.next RFD (weftspun 2298, smoke-water 3000), then park the source.
   Ask with `clarify` (the operator asks for Hermes choices). On Discord keep each choice label to a few words (about 25 characters) and the question to one line: long labels overflow the buttons, and blank labels have also been seen, so a numbered key in the question text ("1 = merge all, 2 = only A") is the fallback the operator answers by digit. Name items by topic, not serial.
7. Record each verdict as a dated move in the `rfd-triage` journal: one transaction per RFD, same code, `1 RFD` into the new account and `-1` out of the old one, tagged `verdict:<v>`, with the reason as the description. Land it as a third PR. `--check` must pass after the RFD PRs merge. Never regenerate the `rfd` snapshot over moves: the tool refuses, because the moves would be counted twice. To bring in RFDs written since the snapshot, run `elixir tools/rfd_inventory.exs <root> --add`. It appends only the missing codes, and a code that already has a triage move opens at that move's origin. Then `--check` must pass, and a second `--add` must add nothing.

**Work in worktrees, and prove the check both ways.** Other sessions move the shared checkouts (`manuals-weftspun`, `manuals-smoke-water` and the inventory) to their own branches mid-task. Before any write, check `git branch --show-current` and `git status`. Do the edits in worktrees off `origin/main`, under a scratch root laid out as `<root>/2-contract/manuals-weftspun` and `<root>/2-contract/manuals-smoke-water`, because `rfd_inventory.exs` takes a workspace root. Build two roots: a triaged one (the RFD branches) and a pre-triage one (detached at the base commits). Then show both results: `--check` passes against the triaged root once the moves are loaded, and fails against the pre-triage root. Also plant an unbalanced move (one posting `2 RFD`): `replace_journal` must refuse it, with tackler reporting "postings do not zero". Remove the worktrees when the PRs are open, and pass `workdir` to every terminal call made from inside one: removing the directory the shell's cwd sits in makes every later command fail before it starts.

## Rules that catch failure modes

- **`parked` is not a canonical state.** If you find an RFD with `State: parked`, flag it as drift. Parked means backlog: an open RFD with no `flight_level`. An old `Shelved YYYY-MM-DD:` paragraph is history only. The inventory counts a shelved RFD by its level like any other, and the RFD carries a `shelved` tag.
- **Task-list `[PARKED · ...]` prefix trumps the RFD survey.** An operator who wants a truly empty queue deletes parked tasks from the list; the RFD stays shelved in prose. Don't resurrect a deleted task by re-reading its RFD.
- **The task list can drift from the RFDs.** An earlier version of the workspace amend on PR #162 landed only 1 of 5 park edits; the task list flagged all 5 as parked while the RFD READMEs still said `discussion` with no shelved note. That's a real class of drift — always cross-check both directions.
- **Session ownership matters.** An unparked RFD you did not open belongs to whoever opened it. Report it, don't act on it.
- **`gh pr view` shows the truth about a PR that says MERGED.** Auto-merge can fire on an amend-in-flight; the merged commit may not include your last force-push. When reporting on delivered work, check the merged commit's actual diff, not the local branch you thought you pushed. See the RFD66606-2167 incident in the session log.
- **The survey must enumerate the whole tree, not a numeric prefix.** A glob like `rfd/2*-*.exs` drops every 1xxx RFD, which is the oldest open work, so the queue becomes an artifact of the pattern. Use `rfd/*.exs`.
- **Never call an item idle because the inventory has no data on it.** A blank push column comes from the inventory's coverage, not from the work. Proposing to park work the org shipped that same day costs the operator's trust. Do step 5a before writing any park list.
- **No `names-repo` tag is not "no work".** Most board RFDs name no repo, so the inventory has no push date for them, and that is unknown, not idle. Before calling anything idle, check live activity by topic: `gh api orgs/<org>/repos?sort=pushed` for each org, plus Hugging Face models, Spaces and datasets (`/api/<kind>?author=chibifire&sort=lastModified`). The org works on HF as much as on GH. A park list built on that gap got corrected by the operator.
- **"Archive by recency" means archive the stalest.** Order the quiet set by when its RFD was created or last really changed (skip the bulk-sweep commits) and park everything before the natural break (2026-10-19: the September ideas went, the October ones stayed). For a duplicate pair, archive the older copy and keep the one still being worked.
- **Last-touch dates don't triage.** Bulk renders and sweeps touch every RFD, so dates cluster in one month. Sort by repo activity from the inventory, and read the `:: decision` text.
- **A logbook entry that names an RFD number is measured-work evidence.** Cross-reference `logbook/*` files that carry an RFD number to flag apparatus already run; reconcile that with the merged-PR check to decide delivered versus still open, rather than treating a logbook as proof the RFD remains open.
- **Prove every matcher on a known file before trusting a count.** A state or `Shelved` match that never fires returns zero, and that reads like "no open work". Check it hits a file known to be shelved (for example 2162) before reporting. In `.exs` sources, state is the trailing atom of the `rfd N, "...", :state do` line. In rendered READMEs it is the bold field `**State:** discussion`, so match the whole field, never a hand-split remainder.
