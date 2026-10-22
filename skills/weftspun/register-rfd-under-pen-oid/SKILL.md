---
name: register-rfd-under-pen-oid
description: Allocate the next RFD serial in SERIALS-vsekai-fabric.exs under Weftspun's PEN arc, write the rfd/<N>-<slug>.exs source whose rendered README carries the AI-drafted attestation canary and the urn:oid spine, and verify the pair with the anti-entropy check. Use when a new RFD needs a number, when subdividing an existing serial (2164.N.M), or when backfilling a previously ad-hoc numbering.
tools: Read, Write, Edit, Grep, Glob, Bash
---

# Register RFD under PEN OID

Weftspun's Private Enterprise Number is `1.3.6.1.4.1.66606`. Site 2
(`v-sekai-fabric`) is category 1 (`documents`), so an RFD's full arc is
`1.3.6.1.4.1.66606.1.2.<serial>[.N.M]`, and it is quoted in prose in the
RFC 3061 URN form `urn:oid:1.3.6.1.4.1.66606.1.2.<serial>`.

## When to invoke

The user asks for a new RFD, asks to subdivide an existing serial into
`.N` or `.N.M` sub-rungs, or points out an RFD that landed under an
ad-hoc number and needs a real serial. Also invoke when a related
document needs to cite an RFD by identifier and the identifier does not
yet exist.

## Where the register lives

`2-contract/manuals-weftspun/SERIALS-vsekai-fabric.exs`. The `arc`,
`pen`, `site`, `category` fields at the top of the file are the source
of truth for the OID shape. Read them before assuming.

New RFDs at this site get `2NNN` serials, per the reactivated-2026-08-31
note in the file's `customLayerData`.

## Pipeline

**1. Read the register.** `mix rfd.next <slug>` prints the next serial, counting register rows, `rfd/` files on disk and pushed `dev/rfd-NNNN-*` branches; it cannot see another checkout's unpushed branch. Use it, or `grep -o 'serial 2[0-9]*' SERIALS-vsekai-fabric.exs | sort -u | tail` plus `ls rfd` and `git branch -r | grep rfd-`: the file holds several blocks, so its last lines and the row of the newest RFD you know about are not the newest serial, and parallel sessions claim numbers hourly. A wrong pick surfaces only as `serial listed twice` from `mix rfd.check`. By hand: open `SERIALS-vsekai-fabric.exs` and find the
`allocated do` block. The highest `serial <N>, "<slug>"` row in it is the
last allocated serial. The next one is `<N>+1`, and it is max-plus-one
rather than the lowest gap. A `deleted do` block below carries rows in
the same `serial <N>, "<slug>"` shape; those are spent, never candidates.

**2. Append the allocation** to `allocated do`, in serial order:

    serial <N+1>, "<kebab-case-slug>"

The slug follows the source's filename so that a retitle renames the
document without renumbering it. Never reuse and never renumber; a serial
is the last arc of an OID and it names one document forever. A document
that landed under a number the register gives to something else is
reissued under a fresh serial, not renumbered into place.

**3. Write the RFD source.** `2-contract/manuals-weftspun/rfd/<N>-<slug>.exs`.
The `.exs` is what is tracked. RFD 2232 makes `README.md` and `DETAILS.md`
build artifacts of `mix rfd.render`, gitignored and never hand-edited:

    # Copyright (c) 2026 K. S. Ernest (iFire) Lee
    # SPDX-License-Identifier: MIT
    use RFD.DSL

    rfd <N>, "<title>", :discussion do
      flight_level :l1          # omit for backlog; on the board only when active
      feature "<one sentence>"
      scope "<paths or mounts>"

      prose ~S"""
      :: decision
      ...
      :: problem
      ...
      :: related
      - RFD <m>, <why>.
      """

      details_title "<title of DETAILS.md>"

      prose ~S"""
      :: details <Heading>
      ...
      """
    end

Copy the shape from the newest RFD in `rfd/` rather than from memory. The
first `prose` renders into README.md and the `:: details` sections into
DETAILS.md. The AI-drafted attestation sentence is rendered by default
(`lib/rfd/doc.ex`). Never type it. A record of finished work takes
`:committed` in the header. Its register row gets `flight_level:` only if
the RFD is on the board.

**4. Cite by URN.** Use the full `urn:oid:` form in prose. Sub-rungs
extend with dot-arcs (`urn:oid:1.3.6.1.4.1.66606.1.2.2164.3.2` is
"RFD 2164 sub-rung 3.2"). Never abbreviate to bare `.2164` or invent
sitewise shortcuts.

**5. Run the anti-entropy check.**

    pixi run python scripts/check_anti_entropy.py

It enumerates the serial register against the RFD sources under `rfd/`,
across every checkout in the manifest rather than this one. An allocated
serial with no document, a document with no row, and two documents on one
serial all fail. Read what it says, not the last line.

**6. Commit both files in the same commit.** The register row and the
`.exs` source land together, so a `git bisect` never lands on a state with
one and not the other.

## Site 3: the private register

Site 3 (`3NNN`, arc `66606.1.3`) is the private manuals checkout (`2-contract/manuals-smoke-water/SERIALS.exs`, register `VSekaiFire`), and the register lives in that private repo, never in the FOSS tree (RFD 1000 / pen-66606 `sitesWithoutRegister`). Rows are `serial N, "<directory slug>"` only: the check reads serial + slug, so the human titles never leave the private repo. A 3NNN RFD that moved to the public register is recorded there as a 2NNN row and excluded from the private register (not double-counted). The FOSS `scripts/check_anti_entropy.py` reads it as `../manuals-smoke-water/SERIALS.exs` in its `REGISTERS` list; the path only resolves inside a `repo` workspace, and the check exits 0 when no `.repo` is above it, so a standalone clone or CI never touches it.

## Moving a private 3NNN RFD to the FOSS register ("migrate it to the FOSS manuals")

1. Take the next 2NNN with `mix rfd.next`, and also check `git ls-remote origin` for `dev/rfd-NNNN-*` branches: in-flight PRs hold serials that are not in `main`'s register yet.
2. Rewrite the source for the public tree: MIT header (`SPDX-License-Identifier: MIT`), no product, codename or private-org names (that includes `chibifire/...` HF repo ids: cite the upstream DOI instead), no links to 3NNN RFDs (relink to the public RFD that owns the method). Keep `:: references` for DOIs; the spine order is Decision, Problem, References, Related.
3. Shorten `feature`/`scope` to one line each so the README stays within 40 lines; `mix rfd.render` reports both the line count and a wrong spine order.
4. Run `pixi run -e gate prek run --files <exs> SERIALS-vsekai-fabric.exs`, commit both on a `dev/rfd-NNNN-<slug>` branch, open the PR.
5. In the private repo, delete the 3NNN source and its `SERIALS.exs` row in one commit, and keep the dev.next entry pointing at "weftspun RFD NNNN". Run `mix rfd.check` there.

## Rules that catch failure modes

- **`fatal: this operation must be run in a work tree` after running the gates:** something in the check run flipped the repo-local `core.bare` to true in the `.repo/projects/...git` dir. Restore with `git --git-dir=.git config core.bare false`, then commit.
- **Elixir RFD sources cap added lines at 98 columns** (prek hook `line-length`): markdown tables wider than that fail the commit; split attributes out of the table into prose.

- **Editing a gate script in manuals-weftspun: no new comment lines.** `check_comment_ladder.exs` (CI hook `ci-comment-ladder`, run with `--base origin/main` before pushing) caps a file that gains a comment line at its EXACT previous density, so even a five-line rationale fails. Put the reasoning in the commit body; keep the code change to the literal edit (a one-line list, not a reformatted multi-line one).
- **Commit subjects start with a capital, digit, bracket or backtick.** `ci-practices` rejects a lowercase first letter even when the subject is otherwise sentence-case prose; `python scripts/check_commit_style.py --base origin/main` catches it locally.
- **Private repo pushes `HEAD:refs/heads/main` directly; the FOSS repo takes a `dev/` branch and a PR through the merge queue.** Both checkouts are detached-HEAD `repo` clients: `git checkout -B dev/<name>`, commit, push, then `git checkout -q <sha>` and delete the local branch so `elixir .repo/manifests/sync.exs . --preflight` reads 0 blocking.
- **`--force-with-lease` after the operator may have edited on the web: `git fetch` the branch first and read what moved.** A stale lease rejects, and a refreshed lease can overwrite the operator's own commit; compare before pushing and offer to restore theirs.

- **The `arc`, `pen`, `site`, `category` fields in the `layer` of `SERIALS-vsekai-fabric.exs` are the source of truth.** Do not hardcode `1.3.6.1.4.1.66606.1.2` into scripts; read it from the register.
- **Sub-rungs are dot-arcs on the serial**, not slashes and not colons: `urn:oid:1.3.6.1.4.1.66606.1.2.2164.3.2`, not `.../2164/3/2`.
- **PEN category comes before site**, not after: `<pen>.<category>.<site>.<serial>`. An earlier version of this pipeline had `<pen>.<site>.<category>.<serial>` and the user corrected it.
- **The canary is rendered, not typed.** A misspelling is rejected by `check_rfd_canary.py`'s self-test control, and a sentence typed into a rendered README is lost on the next `mix rfd.render`.
- **Keep churny literals out of RFD prose.** `scripts/check_rfd_literals.exs --base origin/main` fails a new RFD for `PR #N`/`#N`, bare commit SHAs, `file:line`, `feat/`-style branch names and backticked project names such as `` `interactor-xr-pilot` ``. Cite a landing by its commit subject in quotes, and name a project in words, or with `&{repo("<name>")}` only when the name is already in `RFD.lock.exs`. Otherwise render raises `is not in RFD.lock.exs`. Run this gate before committing: the prek hooks on commit do not run it.
- **Slug and filename match.** The register's slug must equal the `<slug>` in `rfd/<N>-<slug>.exs`. The anti-entropy check enumerates both. When renumbering a draft, also delete the rendered `rfd/<old-N>-<slug>/` directory that `mix rfd.check`/prek left behind; it is untracked output under the old number.
- **A rendered README over 40 lines fails the structural gate.** Budget the
  lines before drafting: the rendered README has 19 base lines (5 head, 4
  blank, 6 for the three section headings and their blanks, 1 canary) plus,
  when details exist, a 3-line pointer hidden from the `.exs` in the
  decision (`DETAILS.md` carries the rest of this RFD). Decision, problem and
  related prose therefore budget to 21 lines with details, 24 without. Trim
  related bullets or fold decision sentences before deleting content; `mix rfd.check`
  prints the exact count. The cap applies in the private repo too: the check
  renders the README in memory even though RFDs ship source only.
- **`check_household_units.exs --base origin/main` reads any `<number> m` as a bare length, speeds in m/s included.** Pair real lengths with an anchor (card, penny, pencil, AAA, AA, soda can); write speeds in km/h and a length used as a name ("a 100-metre seam") with a hyphen. Run it before committing; prek on commit does not.
- **An amendment to a merged RFD goes on a fresh `dev/rfd-NNNN-<topic>` branch from `origin/main`.** Check the earlier PR's state first (`gh pr view N --json state`): pushing to a merged PR's branch updates nothing.
- **A commit with only the serial or only the source** leaves the register in a drift state that neither half of the pair notices on its own; the anti-entropy check does, but only when it is run.
