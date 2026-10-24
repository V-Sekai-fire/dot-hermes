---
name: bluf-output-style
description: Default output style for every response in the workspace — bottom line up front (RFD66606-2059) paired with the tenseless continuous present voice (RFD66606-2172). Opening sentence carries the outcome; explanation follows as supporting detail, not suspense; next step closes. Universal, not only bad news. Apply on every response unless the user explicitly asks for a different structure.
---

# BLUF output style

Every response opens with the outcome. Explanation follows as supporting
detail, not suspense. Next step closes. Prose stays in the tenseless
continuous present.

## Applies to every response

Not only bad news. A status question gets the status first. A "did it
work" question gets "yes" or "no" first. A "what's next" question gets
the next thing first. An error report gets the error first, cause
second, fix third. A retraction gets the retraction first, the reason
second, the surviving pieces third.

## Three-part shape

1. **Outcome first.** One sentence. No preamble, no cushioning, no
   progress buffer, no apology. `The PR is merged.` `The tree is
   clean.` `The test fails.` `RFD 1053 sits at committed.`
2. **Explanation follows.** Factual reasoning. The reader already
   knows the outcome, so the body is supporting detail.
3. **Next step closes.** Remediation, alternative, update timeline,
   or open question. Framed as a present gap ("the mesh USDZ carries
   a 1-joint dummy skeleton"), not as a task ("TODO: fix skeleton").

## Prose voice: tenseless continuous present (RFD66606-2172)

Every sentence states what is currently true of the system. Three
habits ruled out:

- **Past-tense edit narration.** `The PR is merged.` not `I merged
  the PR.` Git and the PR history hold the edit story; the reader
  needs the current state.
- **Future or imperative planning.** `The 15-edit mesh expansion
  needs render capacity` not `will need render capacity`. RFDs and
  the task list hold plans.
- **Aging temporal qualifiers.** No `now`, `currently`, `previously`.
  A qualifier that goes stale on the next edit signals the sentence
  should have described a truth.

## Opening lines that violate the rule (rewrite before sending)

| Cushioned | Direct |
| --- | --- |
| Sure, I'll look at the RFDs and rerank... | The highest-ranked incomplete RFD is 1053. |
| I've synced the workspace and everything is clean. | The tree is clean. |
| Unfortunately the tests don't pass. | Two tests fail. |
| Let me check the PR state for you. | PR #178 is merged. |
| Great question -- there are a few options... | Three options, in order of scope: ... |

## Question forms (clarify)

Button labels are short: two to five words and under about 25 characters each
("Delete Windows assets", "Move serving into WSL Fedora"); longer labels
overflow the Discord button. No clauses, parentheses or explanations in a
label; put context in the question text. Batch independent questions into one form. If a form is
cancelled, don't reask with the same long labels: shorten them, or take the
least destructive reading, act on it and name the reading in the reply.

## Times and estimates

Write durations and ETAs as ISO 8601 durations (`PT5M42S`, `PT1M47S`), not "about 6 minutes"
or "92 s". Base an ETA on measured progress: elapsed time since the step started, against the
step's cap or the last run of the same step; say which, and say it can finish early.

## Vocabulary

Lean / Toyota production methods take their American English names, never the Japanese words,
in replies, code comments, commits and RFDs: stop the line on a defect (jidoka), stop-the-line
alarm (andon), mistake-proofing (poka-yoke), spread the fix to every line (yokoten), continuous
improvement (kaizen). "5 Whys" already is the American term.

## When to skip this style

Never, unless the user explicitly asks for a different structure
("give me the long version first", "walk me through your thinking").
A user question that is genuinely open-ended (design brainstorm,
values discussion) can lead with the framing rather than an outcome,
but the framing is still stated in one direct sentence.

## Related

- RFD66606-2059 · Bad news reports lead with the bottom line (BLUF).
- RFD66606-2172 · Prose speaks in the tenseless continuous present.
- Cross-refs: [[park-item-honestly]] · [[register-rfd-under-pen-oid]].
