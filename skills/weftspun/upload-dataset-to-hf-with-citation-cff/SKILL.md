---
name: upload-dataset-to-hf-with-citation-cff
description: Use when writing or updating a CITATION.cff for an HF dataset, model/download repo or code repo, or publishing a Weftspun dataset staging directory (e.g. a MaskScore stub) to HF.
tools: Read, Write, Edit, Grep, Glob, Bash
---

# Upload dataset to HF with CITATION.cff

Every upstream this dataset cites goes in a `CITATION.cff` at the repository
root. Two classes, both listed:

1. **License-required attribution** — CC-BY-4.0, MIT, BSD, and every other
   license whose terms require a credit line. Without these the corpus is
   undistributable. SpeakingFaces (CC-BY-4.0), Parakeet TDT (CC-BY-4.0),
   allosaurus (MIT), WavLM SV (MIT) are the recurring ones.
2. **Courtesy citations** — Apache-2.0, MPL, and other permissive licenses
   whose paper or model card the dataset consumes. No legal obligation, but
   the reader needs to know which model produced which column. Whisper,
   Voxtral, wav2vec2, Gemma, Qwen3-TTS, ANNY are the recurring ones.

The rule is the same either way: if the dataset used it, cite it.

## When to invoke

Publishing a new dataset repo to HF, adding a new stub subdirectory to an
existing one, adding a new upstream of any license to a corpus, or debugging
a dataset viewer that is not surfacing parquets that are on disk in the repo.

## Author line

Weftspun does not sign these `chibifire org`. Author is:

    authors:
      - family-names: Lee
        given-names: "K. S. Ernest (iFire)"
        alias: fire
        website: https://github.com/fire

Copy that verbatim, including the parenthesised nickname in `given-names`.

## Pipeline

Reference: `6-datasource/anny-render-corpus/build/hf_speech_stage/`.

**1. Build the staging directory.** Everything the HF repo will hold sits
under one local directory, with the parquets in stub subdirectories
(`speech/`, `mesh/`, ...) rather than at the root, so future stubs do not
collide by filename.

    build/hf_<name>_stage/
      README.md                  frontmatter + configs + human prose
      CITATION.cff               author + every upstream under references
      speech/*.parquet           this stub's 3 parquets
      mesh/*.parquet             next stub's 3 parquets
      ...

**2. Author the CITATION.cff.** Structure follows citation-file-format.github.io:

    cff-version: 1.2.0
    title: <one-line dataset title>
    message: >-
      If you use this dataset, please cite it and the upstream sources
      listed under `references`.
    authors:
      - family-names: Lee
        given-names: "K. S. Ernest (iFire)"
        alias: fire
        website: https://github.com/fire
    license: Apache-2.0
    license-url: https://apache.org/licenses/LICENSE-2.0
    type: dataset
    version: <RFD serial, e.g. RFD-2164.5>
    date-released: "<YYYY-MM-DD>"
    url: https://huggingface.co/datasets/chibifire/<repo>
    identifiers:
      - type: other
        value: urn:oid:1.3.6.1.4.1.66606.1.2.<serial>
        description: RFD <serial> (<title>)
      - type: other
        value: urn:oid:1.3.6.1.4.1.66606.1.1.<parent>
        description: RFD <parent> (<parent title>)

    references:
      # <source name> -- <license, e.g. CC-BY-4.0 (attribution required)>
      - type: data | software
        title: ...
        authors: ...
        url: ...
        doi: ...             # if the source publishes one (SpeakingFaces: 10.3390/s21103465)
        license: <SPDX-ish>

**Validate before upload** against the official schema (catches what reads fine by eye):

    curl -sL -o schema.json https://raw.githubusercontent.com/citation-file-format/citation-file-format/1.2.0/schema.json
    python3 -c "import json,yaml,jsonschema; s=json.load(open('schema.json')); \
      print([e.message for e in jsonschema.Draft7Validator(s).iter_errors(yaml.safe_load(open('CITATION.cff')))])"

It must print `[]` (`uvx cffconvert --validate -i CITATION.cff` is the one-line equivalent). The top-level `type` is exactly `dataset` or `software`, nothing else: `report`, `article` and the like live only inside `references:`. Pick `dataset` for an HF dataset or staging dir, and `software` for a code/model/download repo, including the repo an RFD lives in. Reference `type:` then takes the schema's enum: a dataset reference is `type: data` (or `database`); `type: dataset` is valid only at the top level. Take every `commit:` value from `git -C <checkout> rev-parse HEAD` and paste it; a SHA completed from its short prefix by hand is a fabricated pin. Two more rules the schema enforces: every `references:` entry needs `authors`
(for our own repos and converted weights use the author line above, plus the upstream maker for a
conversion, e.g. `- name: Meta` on a Llama 3 conversion); `license:` takes SPDX ids only, so a
non-SPDX licence (NVIDIA Open Model License, Meta Llama 3 Community License, Tomorrow Open Source
Technology License) goes in `license-url:` with its name at the start of `notes:`. curl every
`url`/`repository-code` and expect 200.

**Software and download repos** (desktop viewer archives, a C++ library) get the same file with
`type: software`, `repository-code:` or `url:`, and one reference per component that ships or that
the code follows: engine, runtime libraries, model weights and the model's code, encoders whose
outputs ship (with the Copyright Office wording that no person wrote those inputs), and algorithms
adapted from another project (NOTICE lists them). Take names and licences from the product's
credits slide or NOTICE so the two stay in step. List parts from what the shipped artifact
REALLY contains (unpack it and list its members; a shared resource pack can carry programs that
one product never runs), not from the feature description. When the parts' licences differ, drop
the top-level `license:` and point `license-url:` at a LICENSE.md that holds a parts table and
every full licence text: a single SPDX id for a mixed package is a false claim. A converted
weight repo keeps its upstream licence; check our HF card against the upstream card. A library change that adopts a new method (e.g.
SOMA-X twist helpers) adds that reference in the same PR.

Include every upstream the dataset actually used. The license field is
recorded honestly (`CC-BY-4.0`, `MIT`, `Apache-2.0`, `MPL-2.0`, ...) so the
reader can tell attribution obligation from courtesy citation, but the
inclusion decision is `did the dataset consume it`, not `does its license
require a credit`. See `build/hf_speech_stage/CITATION.cff` for the full
worked example — 11 references spanning CC-BY-4.0 data, MIT tools, and
Apache-2.0 models.

**3. Wire the README configs.**

    ---
    license: apache-2.0
    tags: [maskscore, rung-<N>, ...]
    configs:
      - config_name: <stub>
        data_files: <stub>/maskscore_<stub>.parquet
      - config_name: <stub>_candidates
        data_files: <stub>/maskscore_<stub>_candidates.parquet
      - config_name: <stub>_scores
        data_files: <stub>/maskscore_<stub>_scores.parquet
    ---

**The subdirectory prefix is what makes the dataset viewer render.**
Parquets in a subdirectory are invisible to the viewer unless the
`data_files:` path includes the subdirectory (`speech/maskscore_speech.parquet`,
not `maskscore_speech.parquet`). Missing subdirectory prefix is exactly
the failure mode that made `chibifire/maskscore-rung-1-bootstrap`'s
speech configs not surface until we fixed the README.

**3b. Gate before any byte leaves — the first upload included.** Run the blocked-word gate over the whole staging
directory: `python tools/space_gate.py scan <dir>`. After the upload, `bao-hf-token 2>/dev/null | python tools/space_gate.py audit <repo> dataset` must print `AUDIT-OK`; the gate reads the token from stdin (or `TOKEN_FILE`) and ignores `HF_TOKEN`, so an exported token gives `Illegal header value b'Bearer '`. Run it with a python that has pyarrow, jsonschema and pyyaml (private repo
interactor-skintokens-qlora; `--self-test` must report every planted control). It decodes every
Parquet string and list<string> column per row group — raw bytes of zstd pages hide strings, so
a `grep` over the files proves nothing. A hit inside an upstream column copied verbatim (someone
else's home path in a source link) goes in the gate's `ALLOW` set with its reason and a planted
control for a neighbouring column; never edit upstream values to pass the gate, because the
exact check against upstream then fails. The gate also scans the FULL path of each file, so a
staging dir under `/Users/<name>` or `~/.hermes` fails on the path itself ("blocked word in the
file name"): stage gate uploads in `/tmp/<dir>`. Copy files from the Mac with
`COPYFILE_DISABLE=1 tar --no-xattrs` so `._*` AppleDouble files stay out of the staging dir,
and look for them before uploading anyway.

**4. Upload, incrementally.** Use `hf` (the HF CLI). The upload must
survive a dropped connection or a killed session: bytes already sent
land as commits, and a rerun resumes rather than restarting. Upload the
staging directory with `upload-large-folder`, which commits per file as
each finishes and resumes on rerun, then follow up with individual
`README.md` / `CITATION.cff` uploads when only those change:

    pip install hf_transfer
    export HF_HUB_DISABLE_XET=1
    export HF_HUB_ENABLE_HF_TRANSFER=1
    hf upload-large-folder --repo-type dataset chibifire/<repo> build/hf_<name>_stage
    hf upload --repo-type dataset chibifire/<repo> build/hf_<name>_stage/README.md README.md
    hf upload --repo-type dataset chibifire/<repo> build/hf_<name>_stage/CITATION.cff CITATION.cff

`hf upload <repo> <dir> .` is the atomic form: one commit for the whole
directory, nothing lands until it finishes. Do not use it for a staging
directory over about 50 MB.

Xet stays off. RFD 2196 rule 5 measured the xet finalize stalling at
6 KB/s and timing out at 94 GB / 110 shards; LFS + `hf_transfer` is the
path that landed. The hub now warns that `HF_HUB_ENABLE_HF_TRANSFER` is
deprecated in favour of `HF_XET_HIGH_PERFORMANCE` (2026-09-04) —
deprecated is not removed; accept the warning, do not set the xet
variable, because it turns on the path the RFD measured as broken. An
earlier revision of this step set it; retracted the same day. Whether
`upload-large-folder`'s per-file commits sidestep the finalize under
xet is unmeasured; RFD 2196 binds until a ≥50 GB push is timed both
ways. Verified against huggingface_hub 0.36.2: `HfApi.upload_folder`
has no `multi_commits` parameter in this version, so the CLI above is
the resumable path, not a Python-side flag.

**huggingface_hub 2.x has no `upload_large_folder`** (HfApi only keeps `upload_file` /
`upload_folder`). There, resume by file: loop the staging files smallest first, skip any whose
remote size (`dataset_info(files_metadata=True).siblings`) already matches, `upload_file` each
one as its own commit, and compare every remote size with the local one at the end. Reference:
`tools/hf_upload_axl2.py` in interactor-skintokens-qlora. When the upload runs on another host
(the Windows desk's WSL), hand the token over without echo:
`bao-hf-token | ssh desk "wsl -d FedoraLinux-44 -u root -e dd of=/root/.hf-up-token status=none"`,
`chmod 600`, and have the uploader read the file and delete it before doing anything else (never
`tee`, which prints the token back over ssh).

Record the final commit hash in the README after the last upload, so a
training run or a paper can pin the exact snapshot it consumed.

**5. Verify from the dataset viewer.** Open
`https://huggingface.co/datasets/chibifire/<repo>` and confirm each new
config appears in the "Subset" dropdown. If not, the config's
`data_files` path is wrong — recheck the subdirectory prefix, not the
upload.

## Amending a published dataset (new rows, a new table, a citation fix)

Changes to a live dataset go through an HF pull request, never a direct commit to main:

1. Note the base: `api.dataset_info(repo).sha`. Download the files to change at that revision into
   `/tmp/<repo>-pr/` (the gate refuses paths under the home directory).
2. Append rows in the file's OWN schema and compression (`pq.read_schema(old)`,
   `ParquetFile(old).metadata.row_group(0).column(0).compression`); put the source in the existing
   `source` column and the population/sex in theirs. Assert the natural key stays unique after the
   concat.
3. Copy numbers from the primary source by parsing it (HTML table cells, the regulation text,
   `pdfimages -png` of a printed edition for figures), never by retyping; spot-check a few values
   against the page. Cite only what the source itself prints: a journal volume, pages or DOI
   recalled from memory is not a citation (drop it).
4. Add the human table to the dataset's markdown next to the existing one, saying what it adds,
   where it agrees with the old table (computed, not eyeballed) and what neither covers.
5. Validate `CITATION.cff` (schema check above), run `space_gate.py scan /tmp/<repo>-pr`.
   When the rebuild regenerates whole tables rather than concatenating, write old rows first and
   assert `new.slice(0, old.num_rows).equals(old)` and `old.schema.equals(new.schema)` for each
   table against the base snapshot: that is the proof no live row changed.
6. `api.create_commit(repo, ops, repo_type="dataset", create_pr=True, parent_commit=<base>)`;
   follow-up fixes go to the same PR with `revision="refs/pr/<n>"`. Read every file back from
   `refs/pr/<n>` (`force_download=True`) and compare bytes.
7. Merge only when the operator says so: `api.merge_pull_request(repo, n, repo_type="dataset")`,
   then re-download from main and compare again.

A study derived from videos (e.g. joint angles from CC BY walking footage) gets one
`type: video` reference per video: title, `authors: - name: "<channel>"`, the watch URL,
`license: CC-BY-3.0` (YouTube's Creative Commons option is CC BY 3.0), and a note with the date the
licence was read from the watch page. Put the CFF in the study's work folder before the run starts.

A reference that names only an issuing body (UN, ISO, NASA, a government agency) still needs
`authors:` for the schema: `- name: "<that body>"`, keeping `institution:`. A regulation (e.g. a
CFR section) is `type: legal-rule` with the agency as author and the eCFR URL; read its figure
plates from the govinfo annual-edition PDF (`pdfimages -png`, 600 dpi), not the blurry web copy. When asked to fix a
file's pre-existing schema errors, list each error with its path first, fix them all in the same
PR, and report the count before and after.

## Rules that catch failure modes

- **Author line is `K. S. Ernest (iFire) Lee` (github.com/fire), not `Weftspun (chibifire org)`.** The organisation owns the HF repo namespace; the author line credits the human. First uploads have caught this reflex twice.
- **Name the repo by its hexagon side:** a dataset is `chibifire/datasource-<name>` (a converted copy of an upstream: `datasource-<upstream>-parquet`), placed at `6-datasource/<name>` in the manifest.
- **A converted copy of an upstream dataset keeps the upstream license** and cites exactly what the upstream README asks to be cited: copy its BibTeX entries into `references:`; never add an arXiv id, DOI, volume or page range that is not in the source text.
- **Create the repo private** unless the operator says public; ask about visibility in the report.
- **CITATION.cff at the repo root** — not inside a stub subdirectory. One file per HF dataset, covering every source used by every stub in it.
- **Every upstream the dataset consumed is a separate `references:` entry**, with its real license recorded honestly. Include a DOI for paper-backed sources (SpeakingFaces: 10.3390/s21103465) or the HF model card URL for weights. `did the dataset use it` decides inclusion; the license field decides whether the credit was legally required or a courtesy.
- **The README `configs:` block is the source of truth for the dataset viewer**, not the parquet layout on disk. A parquet uploaded to a subdirectory that no config points at renders as nothing. Silent skip that reads exactly like a pass — rule 3.
- **Version the CITATION.cff by RFD serial** (`version: RFD-2164.5`) not by a semver invented on the spot. The RFD is the release; the file cites it.
- **`hf upload` never rewrites what it did not upload.** A first pass with the full staging directory is fine; a second pass with only `README.md` will not delete a stray file, so the staging directory is the reference — not the state on HF.
- **The upload is incremental or it is a liability.** `hf upload-large-folder` commits per file and resumes; `hf upload <dir> .` is one atomic commit that costs the same bytes twice on any drop. A multi-GB corpus render or a checkpoint goes through the resumable form every time; the atomic form is for a README.
- **Pin the snapshot.** The final commit hash goes in the README. A dataset consumed by a training run whose commit cannot be named afterwards is a training run that cannot be reproduced.
- **Older `hf` CLI builds**: this build exposes `hf repo create` / `hf upload` / `hf repo set` / `hf download` (with `--repo-type dataset`) \u2127 the `hf dataset create/upload` and `hf repo files` forms are absent. When a `dataset`-prefixed subcommand isn't found, run `hf --help`; use `--repo-type dataset` on the generic `repo`/`upload` commands.
- **Visibility**: default to private at creation; to publish, set the repo visible \u2127 `hf repo set <repo> --mode dataset --private false`. If the build lacks `repo set`, use the HF web UI or the `huggingface_hub` `api` visibility method.
- **Related skills**: [[emit-etnf-maskscore-stub]] for what to put in the parquets, [[register-rfd-under-pen-oid]] for the serial cited in `version:` and `identifiers:`.
