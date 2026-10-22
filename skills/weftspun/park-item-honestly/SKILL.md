---
name: park-item-honestly
description: "Park an RFD or a task-list item. For an RFD, parked means backlog — drop its flight_level so it leaves the board, keep the open state (never `parked`), and record the reason and resume condition as a dated move in the inventory's rfd-triage journal. A task-list item gets a `[PARKED · <reason>]` prefix with an `unpark_when`, or is deleted for an empty queue. Use when the operator says park it, shelve it, no budget today, defer, or names a specific RFD/task to hold."
tools: Read, Write, Edit, Grep, Bash
---

# Park an item honestly

The workspace convention has two layers:

1. **RFD source (`rfd/<N>-<slug>.exs`)**: parked means backlog. Remove the
   `flight_level` line so the RFD leaves `mix rfd.board`, and keep `state`
   at an open RFD 1000 value (`prediscussion`, `ideation`, `discussion`). The
   reason and the resume condition go in the inventory's `rfd-triage`
   journal as a dated move from `Board:<L>` to `Backlog` (see
   [[find-unparked-items]]). Older RFDs carry a `Shelved YYYY-MM-DD:`
   paragraph. Leave it as history, and don't add new ones unless the
   operator requests one.
2. **Task list** — subject prefix `[PARKED · <reason>]` with metadata
   `{parked: true, parked_reason, unpark_when}`. If the operator wants
   an empty queue, delete the task instead; the RFD carries the record.

**Do not write `State: parked`.** It is not on RFD 1000's list and the
check-rfd-structure gate rejects it. This bit me: 6 PRs shipped invalid
state values before the gate caught it (the gate had a DIR_RE that
silently skipped the entire 2xxx register — fixed in
weftspun/request-for-discussion PR #164).

## When to invoke

Operator asks to park, shelve, defer, or hold an RFD or task. Or asks to
mark "no budget today" on specific work.

## Pipeline

**1. Identify scope.** Which RFDs, which task-list items. A parent RFD's
sub-rungs are usually shelved together; explicit sub-rung tasks
inherit the parent's shelved state.

**2. Edit each RFD source.** Delete its `  flight_level :lN` line, and drop the
matching `, flight_level: :lN` from its row in `SERIALS-vsekai-fabric.exs`
(the register carries the level too). If it is a `@critical_path` step,
remove that serial from `lib/rfd/board.ex` too.

**3. Write the move.** One `rfd-triage` transaction per RFD, with the reason
and a concrete resume condition as the description:

    2026-10-17 (weftspun/2264) 'park: no repo push since September; resume when the drape needs repaired meshes
     # tags: site:weftspun, verdict:park
     Assets:RFD:weftspun:Backlog  1 RFD
     Assets:RFD:weftspun:Board:L1  -1 RFD

**4. Check.** After the RFD PR merges, run
`elixir tools/rfd_inventory.exs <root> --check` in the inventory. It must
report no drift.

**5. Update the task list.** For each parked task:

    TaskUpdate({
      taskId: N,
      subject: "[PARKED · <reason>] <original subject>",
      metadata: {parked: true, parked_reason: "<reason>",
                 unpark_when: "<condition>"}
    })

If the operator wants an empty queue, delete parked tasks instead — the
RFD carries the record and the task list stays a queue.

**6. Commit and PR.** One commit per parked-RFD wave, cite each RFD's
OID in the body, and land as one PR. Verify with:

    pixi run -e gate python scripts/check-rfd-structure.py

Should show 0 problems (or list only pre-existing ones out of scope).

## Rules that catch failure modes

- **Never write `State: parked`.** It is invalid. Park = drop `flight_level`, keep the open state. See [[find-unparked-items]].
- **A board RFD with a step can't be parked alone.** `mix rfd.board --check` fails when a `@critical_path` serial in `lib/rfd/board.ex` loses its level. Remove it from that list in the same commit, after the operator rules on it.
- **Body paragraph, not preamble (old Shelved lines).** When the operator does request a `Shelved` line, put it in the prose, not the preamble: check-rfd-structure reads a preamble `**Shelved:**` as an unknown metadata field.
- **`gh pr merge --auto` races your amend.** If required checks are already green when you enable auto-merge, the merge fires on whatever commit is at the branch tip AT THAT INSTANT — a force-push seconds later doesn't land. When you amend after arming auto-merge, verify the merged commit's actual diff with `gh pr view <n> --json state` and `git show <merged-sha> -- <file>`. See RFD 2167 incident.
- **Squash may not be allowed.** Some repos disallow squash-merges (weftspun/request-for-discussion is one). `gh pr merge --auto --merge` (regular merge commit) is the fallback.
- **`gh pr merge` arg order matters.** `--repo` before the PR number silently no-ops; the PR number comes first: `gh pr merge <n> --repo <owner/repo> --auto --merge`.
- **Reconcile task list and RFD state before reporting.** If a task says PARKED but the RFD still has a `flight_level`, either the RFD or the task is wrong. Fix the drift before the next zoom-out.
- **The unpark condition must be concrete.** "when time returns" is not concrete; "when local GPU frees for reward training" is. A vague condition means the item will not be picked back up because nothing will ever obviously trigger it.
- **Ask for rulings by plain topic, not RFD number.** The operator does not know RFDs by serial ("i don't know what those are"). Group items by topic, and treat replies typed in chat (often cut off or partial) as rulings; re-ask only what is still open.
- **On Discord, write the numbered options into the `clarify` question text.** The operator wants Hermes choices, but the button labels render blank there, so a form whose options live only in `choices` comes back cancelled. Put "1 = …, 2 = …" in the question itself (or numbered items for "reply with the numbers to keep"), keep `choices` short, and accept a digit typed in chat as the answer. Even with the numbers in the question text, the form can still come back `cancelled`. A cancelled form is not a ruling: put the same numbered questions at the end of your chat reply so the operator can answer them by digit.
- **A park reason must point to live evidence of idleness.** "No repo push" holds only after the live GitHub and Hugging Face check in [[find-unparked-items]] step 5a. A blank inventory column is not evidence.
- **The operator's verdict words map to RFD edits:** done = `:committed`; archive or park = backlog (drop `flight_level`); remove a duplicate = `:abandoned` stub; keep = no edit. When a word is ambiguous ("archive"), apply the backlog reading and say so in the report.
- **Abandon as a stub.** Replace the source with only the header `rfd N, "<title>", :abandoned do` and `abandoned_at "<sha of origin/main that still holds the full text>"`, and drop the level from its register row. Delete the rendered `rfd/<N>-<slug>/` directory before `mix rfd.render`: a stale `DETAILS.md` left beside the new README fails check-rfd-structure ("has a DETAILS.md and never names it").
- **Triage only the board.** Backlog RFDs are out of scope unless the operator names one.
