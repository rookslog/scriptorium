# scriptorium — Claude Code project guide

**What it is.** A schema-first *synthetic* scholarly-corpus generator. It **manufactures**
OCR ground truth instead of annotating it: typeset a known `PageGT` into a scholarly PDF
layout, (eventually) degrade it to a scan-like image, and emit `(page-image, perfect-GT)`
pairs — GT correct *by construction*, difficulty a controlled dial. It targets the layouts
every public OCR benchmark skips (footnotes, marginal references, critical apparatus).
**Public repo**; public-domain / synthetic source text only.

## The one design rule: schema-first generation
The input **is** a `DocumentGT` / `PageGT` instance (from the parallel
[`scholar-schema`](https://github.com/loganrooks/scholar-schema) package) plus a
`DegradationSpec`. There is no bespoke authoring DSL. **Every schema element must earn a
renderer** — an element the schema can express but no template typesets is a gap by
definition (this discipline doubles as a schema test). See `docs/design.md`.

## Architecture
```
PageGT JSON ─▶ schema_bridge.validate_page_gt ─▶ render.render_tex ─▶ render.render_pdf
                (lazy/optional scholar-schema;     (_FootnoteCollector    ─▶ RenderResult
                 structural fallback if absent)      + single_column.j2)      {tex, pdf_path, gt}
```
- `src/scriptorium/schema_bridge.py` — lazy/optional bridge to `scholar-schema` (probes
  `scholar_schema.schema` / `scholargt.schema`); minimal structural fallback (requires keys
  `page_index`, `regions`) when the package is absent. `strict_schema=True` forces the real model.
- `src/scriptorium/render.py` — LaTeX-safe Jinja2 env (`\VAR{}` / `\BLOCK{}` so it doesn't
  collide with TeX), `latex_escape`, `_FootnoteCollector` (region → body vs.
  `note_area` / `semantic_labels:["note"]`), tectonic subprocess compile.
- `src/scriptorium/degradation.py` — `DegradationSpec` (severity-parameterized, `[0,1]`-validated,
  frozen). `apply()` is an **honest stub**: clean → passthrough, non-clean → `NotImplementedError`
  (the augraphy scan-sim backend is planned, not integrated).
- `src/scriptorium/cli.py` — `scriptorium render <page_gt.json> <out_dir>`.
- `src/scriptorium/templates/single_column.tex.j2` — the only template (milestone 1).

> ⚠️ **Gotcha:** `degradation.apply()` is **not wired into the render path** — rendering is
> clean-only today. The `(image, GT-bbox)` pair does not exist yet (no raster emission, no
> render-time bbox extraction). Those are active-roadmap work, not shipped.

## Roadmap
- **Template roadmap** (`docs/design.md` §3, M1–M5): single-column + footnotes **[shipped]** →
  marginal references → sous rature → dual-register (Glas) → Talmudic/commentary. M2–M5 are
  deferred to a follow-on phase, pending schema-taxonomy validation.
- **Engine capabilities** (see `README.md` and `docs/design.md` §1.2/§2): the augraphy
  degradation backend, batch generation, and render-time pixel-bbox emission that turn clean
  single pages into `(image, GT-bbox)` pairs across difficulty strata — **planned, not yet shipped**.

> Detailed execution planning (the build's milestone packet, gates, ledger) is kept in a
> **non-public** area and is intentionally never referenced by path from public files — see
> *Conventions → Planning artifacts*.

## Commands
```bash
uv sync --group dev
uv run scriptorium render tests/fixtures/minimal_page.json out/   # .tex always; .pdf if tectonic present
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
```
Tests tagged `tectonic` run only when the engine is installed (CI skips them via skipif).
`brew install tectonic` for local PDF rendering.

## Guardrails (public-repo hygiene — these are gates, not niceties)
- Repo-relative paths only in committed files; public-domain / synthetic text only; **no
  PDFs / rasters / files >1 MB in git** (CI `no-binary-blobs` guard). Outputs go to gitignored `out/`.
- The GT schema is **frozen** here: render what `scholar-schema` expresses; escalate schema
  gaps upstream — never fork or invent schema structure in this repo.
- scriptorium stays a standalone repo, never merged into the OCR pipeline it feeds
  (Goodhart-independence: the GT source must not cohabit with the system it evaluates).

## Conventions
- **Code navigation:** use `codebase-memory-mcp` (repo is indexed). serena was removed 2026-06-19.
- **Public cross-refs:** cite only in-repo docs (`docs/design.md`, `README.md`) or the public
  `scholar-schema` repo — never a private planning doc. (The earlier dangling `PLAN.md §…` refs
  were scrubbed 2026-06-19.)
- **Planning artifacts (keep private):** the execution packet, status / ledger / friction logs,
  and any non-public-facing planning live in `goal/` — a **separate nested git repo that the
  public repo gitignores**. Never commit planning artifacts to the public repo, and never
  reference them by path from public files.
