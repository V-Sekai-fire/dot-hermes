---
name: write-checks-that-can-fail
description: Before trusting a check, prove it can report the other outcome — the failure mode is a check that prints something reassuring while measuring nothing
---

# Write checks that can fail

A check that cannot distinguish its outcomes is not a weak check, it is
no check. It costs the same to run, prints something reassuring, and
certifies whatever was already broken. `CLAUDE.md` states it as rule 2 —
a check that passes on known-broken input is decoration — and rule 3 —
a silent skip reads exactly like a pass.

The trap is not writing a bad assertion. It is writing a *good*
assertion the check never reaches.

## Reflex

Before believing a green check, ask: **what would make this print the
other thing?** If there is no answer, the check has not run yet.

Then make it print the other thing, once, deliberately.

## The five ways a check measures nothing

Each of these produced a false green in one session.

**It never reached the assertion.** A parser control ran outside a git
repository, so the tool exited at `fatal: not a git repository` before
reading its config. Three configs "passed" identically — including the
one with the defect planted in it.

**It matched on guessed wording.** The same control grepped for
`parse error|invalid assembly`. The real message was `unknown command: #`.
The tool was rejecting the input correctly and the check called it
accepted. Grep for the *outcome* — exit code, artifact present — not for
a string you predicted.

**The threshold was never crossed.** An `ar` response-file fix was
"verified" with 400 objects producing a 30 KB command line, against a
32,768-byte threshold. The shim loaded, the banner printed, and the
response file never engaged. Rerunning at 1200 objects (82,820 bytes)
is what made it actually fire.

**The exit code came from the wrong process.** `if git cherry-pick X | tail -3`
tests `tail`, which always succeeds. A conflicted cherry-pick reported
as clean while `CHERRY_PICK_HEAD` sat on disk. Same family: `$PIPESTATUS`
is bash; **zsh spells it `$pipestatus`**, so the bash form silently
expands to nothing and a clean compile reads as a failure. Capture
output and status separately and never put a compiler behind a pipe.

**Absence was read as success.** A CI watcher counted "0 checks
returned" as ALL SETTLED and reported green. The token had expired and
every call was 401ing. An empty or unauthorised result is an *error*
state, never a settled one — and long-running watchers must re-mint
credentials, because an hourly expiry otherwise masquerades as success.

A sixth, in the same family: `echo "pushed"` inside a loop, printing
regardless of what the push returned. One of three had 403'd.

A seventh: **the negative control was too close to the positive.** An
int8 reconstruction was checked against its source weights (cos 0.99996)
with a sibling checkpoint as the "wrong" reference, which scored 0.99985:
the two models were a fine-tune apart. A control must be structurally
unrelated input that the check is certain to reject (the same layer
kind from another block, a shuffled tensor), and the report states the
gap between the two numbers, not only that the good one is high.

An eighth: **the test environment had more than the target.** A local
container pre-installed a package the deployed build lacked, so the app
imported fine locally and crashed remotely. Build the test environment
from the target's own manifest and nothing else.

A ninth: **the check read text, not what the loader uses.** A GPU-arch
gate grepped `strings` for `sm_86`; a renderer library names every arch
in its text but ships kernels for one, so the gate passed it and the run
died with "no kernel image". Measure the artifact the runtime consumes
(`cuobjdump --list-elf` for SASS), and include a control file that has
none of the thing (a host-only `.so`): under `set -euo pipefail` an empty
`grep` exits 1 and kills the gate for the wrong reason.

A tenth: **the build target set was empty.** A pre-push hook ran a bare
`lake build` in a package with no `@[default_target]`; Lake printed
"Nothing to build" and exited 0 on every Lean change. Read the build
log for what was compiled, not only the exit code, and plant a type
error in a module the hook should cover: it must fail the hook (via
`prek run <hook-id> --files <file>`), then pass once reverted. Fix it
by marking the real libraries default targets so the no-argument
command builds them.

An eleventh: **the check's sign was undefined on its input.** A
winding-number inside/outside test was applied to an open sheet (an inner
garment layer), where the sign is arbitrary; a clearance gate against the
closed body passed while the outer layer sat through the sheet. Use a
test whose sign is defined for the geometry (face normals oriented by a
closed reference), and judge only points where it is defined.

A twelfth: **the audit's probes could not land on the defect.** A
closed-solid audit (boundary edges, non-manifold edges, winding probes
0.2 mm off sampled faces) passed a thickened garment whose sheet crossed
itself 2,231 times, because a crossing occupies almost none of the
probed volume. When a property is local and rare, count it directly
(here: edges passing through a triangle they do not touch) and gate on
that count, with a clean control (0) and a planted fold (>0). Same family:
a sign test written as `w > 0.5` never fires on an inward-wound mesh,
which reads -1 inside; compare magnitudes when either sign is possible.

A thirteenth: **the control crashed instead of failing.** Running new
self-test controls against the old code by stashing the implementation
gives an error (a new argument the old code lacks), which proves nothing
about behaviour. Keep the new interface and flip only the behaviour
switch (a `tables=False` argument back to `True`): the new control must
report FAIL by its own assertion, then the switch goes back.

## Control before fix

When a hypothesis names a cause, build the control that isolates it
**before** writing the fix: a switch that changes only that variable
(closed loops on/off, bends on/off) with everything else, including the
RNG draw sequence, held identical. Run both arms on the baseline code.
If removing the suspected cause does not move the number, the hypothesis
is dead and no fix gets written. A fix measured without this arm can
repair the traced case and still be wrong overall.

Then run the fix on both arms: it must move the default arm toward the
control arm's number and leave the control arm (where the fixed path is
never taken) exactly unchanged. A change on the control arm means the fix
touches more than the named cause.

Before blaming the search step, verify the intermediate structure it
searches (graph nodes, neighbour order) against ground truth, with a
scrambled-copy control that must flag every item. If the structure is
right, the defect is in the walk or in when it is re-run; a per-event
trace (was the missing answer ever found, when did the wrong one appear
relative to the input that should have split it) localises it.

For a port checked against the original app's own log, compare event by
event (each committed input must add exactly what the log recorded) and
work from the FIRST divergent event only; later mismatches usually
cascade from it. Instrument the real call at that event, inside the
code path, after the state changes it depends on: a diagnostic that
re-runs the search before the call (or from a copy of the state) reads
state the real call never sees and points at the wrong element.

When the port reads line-for-line identical to the original at the
divergent step and the behaviour still differs, stop reading code: run
the original as the oracle on the same input. Build it from the original
source files unchanged (only lifecycle hooks swapped for an explicit
init) against a minimal stand-in for the platform's value types in the
platform's precision (for Unity: float Vector3/Mathf/Quaternion with
Unity's normalize and equality tolerances), and drive it with the same
replay driver logic as the port, so a difference isolates to the ported
classes. Do not route the original through a transpiler that targets a
language subset (UdonSharp→GDScript and the like): run its `--check`
first and count parse failures, dropped constructors, rejected lambdas,
untyped generic collections and a changed float width. Its output is a
third port and cannot arbitrate between the other two. Recipe for a
Unity-C# oracle under dotnet: `references/unity-csharp-oracle.md`.

Give the oracle comparison its own planted control (disable one call in
the oracle copy only; the diff must light up) before reading "0 events
differ". Then read the three-way result: oracle and port agree but both
miss the log means the defect is in the replay driver's reconstructed
inputs (tap position, mirror plane, which anchor or stroke a recorded
constraint maps to), not in the ported classes; port differs from oracle
means a port bug, and the first differing event per session is the place
to diff the two step by step.

## A/B comparisons of two builds

- Prove each binary is what its name says with a probe whose expected
  value differs between them (one case the fix is known to change). Two
  arms reporting identical numbers everywhere is a red flag, not a
  result: a stash-build-pop script killed mid-run leaves the tree without
  the change, so the next run builds "fix" from base.
- Refuse to start when the change is absent from the tree
  (`git diff --quiet <path> && exit 1`), and check again afterwards.
- Put multi-file compile lines in a bash script with arrays: zsh does not
  word-split `$S`, so the compile gets one bogus filename and every later
  row prints empty.
- Enumerate the population from the repo's own split tool (the train
  list), never a glob over the raw data directory: the glob opens
  held-out validation and test files.
- "N of M inputs identical" is not evidence until those inputs reach the
  changed code. Count how many take the path (an env-gated counter in
  the fixed branch), and compare every intermediate state (per-event
  trace of a replay), not only the final output: final states hide
  differences that later steps paper over. Report differing states and
  how many inputs exercised the path.
- When the code is a port, judge each differing case against the
  original's own log as well as against correctness. If the original
  shows the same defect, say so: fidelity vs correctness is the
  operator's call, and the fix goes behind an option until decided.

## Closing the tracked item

Before closing an issue a fix was filed under, read its own done-when
checklist: a merged fix for one sub-problem does not close an issue
with other unchecked items. Close only when every box is checked, or
say which remain and leave it open.

## Frontier scoring of a test oracle

When asked to apply frontier learning to a randomized oracle, split it
into levels (shape × drawing style × size, n problems each), score a
problem as exact or not, and compute regret `1[s>=1] - s/n` per level.
Levels with `0 < s < n` are the frontier: trace failures there first,
and keep a change only if frontier exact count rises and no level loses
exact problems. Report solved / frontier / unsolved counts and the
before-after exact totals, not only aggregate percentages.

## Both directions, always

A control that only shows the good case proves the check *can* say yes.
Pair it:

    control -- real input        : behaved (accepted)
    control -- planted defect    : behaved (caught)
    control -- defect then fixed : behaved (clears)

The third matters more than it looks. It proves the check responds to
the *thing* rather than to some unrelated property of the broken file.

The strongest control is not planted at all: run the check against a
defect that already happened. An archive-symbol gate was validated
against two real facades found earlier the same day — better evidence
than any synthetic input, because nobody chose those inputs to be found.

## Do not assume the convention, read the value

Two PRs were opened against `main`. One repository used `main`; the
other used `main-fabric`, and that PR named a branch that does not
exist. `default_branch` is one API call. The same shape put a ref in a
committed config file that no longer resolved after a rename.

Anything a tool will resolve later — a branch, a remote, a path, a
flag name — gets read now, not guessed. Check the flag too: a control
passed `--config` to a tool whose option is `-f`.

## When the result is implausible, suspect the check first

A tree-hash comparison reported CONTENT DRIFTED on all six branches of
a rebase. The rebase was correct; the check was impossible to satisfy,
because the whole point of the operation was adding two files to every
tree. The right question was not "are these identical" but "do these
differ by *exactly* the expected files".

An implausible result is usually the measurement, not the world.
