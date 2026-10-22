# Inventory census: the whole RFD set in one read

Recipe for the survey half of "study rfds" / "zoom out" / "what's the queue". Produces the four-bucket census (board / backlog / shelved / closed) for both trees without re-parsing every `.exs` or running the Elixir inventory tools.

## Load the committed dump

The `6-datasource/inventory/sql/` directory holds the inventory as a split SQLite dump (tables + postings, sharded by txn id). It is committed and is the read-only snapshot that `elixir tools/load.exs` rebuilds — loading it directly is equivalent, and needs no credentials or the tackler binary.

- Execute the files in a fresh SQLite db, in numeric prefix order (`00-begin.sql`, `01-journal.sql`, `02-txn.sql`, `02-txn.txn-0.sql` … `02-txn.txn-f.sql`, `03-…`, … `99-end.sql`). A numeric-prefix sort of the directory is the safe order; the sharded files interleave under the same integer prefix.
- After that, `txn_flat(code, description, tags)` exists. `code` is `weftspun/NNNN` or `smoke-water/NNNN`; `tags` is a comma list of `key:value` pairs.

## The classification is in the tags

Each RFD's tags encode everything you need; the inventory writes one `account` per RFD from exactly this logic, and the tags reproduce it:

- site — `site:weftspun` or `site:smoke-water`. Two trees, two questions: weftspun = rules/history; smoke-water = the live runway.
- state — `state:<prediscussion|ideation|discussion|published|committed|abandoned|moved>`. 
- level — `level:<l1|l2|l3>`, present only on a board RFD. Absent = off the board.
- shelved — bare `shelved` tag (an old `Shelved YYYY-MM-DD:` paragraph; the RFD carries the tag).
- names-repo:site:repo (repeated) — the repos the RFD owns, for liveness cross-ref in the triage half.
- step:sN — board order position; weftspun's sequenced rungs only.

## One census query

Classify every RFD from `txn_flat` by the rules above:

- Board (active) = state in prediscussion/ideation/discussion AND level present AND not shelved. Report grouped by level (l1, l2, l3).
- Backlog = state in prediscussion/ideation/discussion AND level absent AND not shelved. Open but off the board.
- Shelved = shelved tag AND open state. Still counted on its level like any other (never delete it).
- Closed = state in published/committed/abandoned/moved.

This matches `rfd_inventory.exs`'s held() exactly, so it is the census the rest of the skill (triage, idleness, parking) reads from. It is a read; nothing here writes the inventory.

## Report shape

- Two trees, named. Smoke-water is the live runway; weftspun is the rules + history tree. Report each tree's buckets separately; never mix their serials.
- Board first, in order. The weftspun board's sequenced rungs (step:sN) are the critical path — list those before the unsequenced l1/l2 items. In smoke-water, the ordered rungs (dev.N) lead, then dev.next.
- Backlog thematic. Bucket the backlog by topic (cineform/recording, mask/omnigen, motion, frontier/taskweft, fdb/bao/security, godot/sandbox/engine, model/quant/ggml, docs/tooling) over the description field. Any RFD that falls in none is the other bucket — report its count honestly; do not force a theme or pretend the remainder is zero. prediscussion vs ideation distinguishes early ideas from started discussion.
- Name the backbone. One sentence stating what the open queue is about (e.g. "most of the board hangs off the dress-on first rung") so the operator sees the dependency chain, not just a list.
- Closed counts only. published / committed / abandoned / moved per site; names, not lists, is enough here.

## Pitfalls

- Read the inventory tags / .exs source, never the rendered README.md/DETAILS.md — the dump and source are the truth; rendered files are build artifacts that can lag.
- Enumerate the whole tree. A numeric-prefix glob (rfd/2*-*.exs) silently drops the 1xxx RFDs, the oldest open work; rfd/*.exs or the full txn_flat set is what you want.
- A missing push in the github journal means unknown, not idle — that belongs to the triage half (idleness confirmation), not the census. The census is about what is open/parked, not how new the work is.
- No credentials are needed for the read: the committed sql/ dump carries all RFDs with their classification. Do not mint a token or run the Elixir writers just to read.
