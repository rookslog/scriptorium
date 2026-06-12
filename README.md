# scriptorium

**Schema-first synthetic scholarly corpus generator.**

scriptorium *manufactures* ground truth instead of annotating it. It typesets trusted
public-domain texts into scholarly PDF layouts and degrades them into scan-like images,
emitting **(PDF / page image, perfect ground truth)** pairs. Because scriptorium authors the
typesetting, the ground truth (text, reading order, footnote anchoring, region types) is
correct *by construction* — at zero annotation cost, with difficulty as a controlled
variable.

It exists to fill a documented gap: every public OCR benchmark excludes footnotes, floating
elements, non-English text, and critical apparatus — precisely the under-benchmarked
capabilities scholarly documents need.

> Status: **walking skeleton** (milestone 1). Renders a single-column page with one footnote
> from a PageGT-shaped JSON fixture through a LaTeX template and the
> [tectonic](https://tectonic-typesetting.github.io/) engine.

## Design rule: schema-first generation

The input language **is** a `DocumentGT` / `PageGT` instance (from the
[`scholar-schema`](https://github.com/loganrooks/scholar-schema) package) plus a
`DegradationSpec`. Output is a rendered PDF + page images + the GT JSON echoed back with
render-time additions (bboxes). GT alignment holds by construction, and **every schema
element must earn a renderer**. See [`docs/design.md`](docs/design.md) for the full contract
and the template roadmap.

## Install

```bash
uv sync --group dev
```

### LaTeX engine (tectonic)

scriptorium renders PDFs with [tectonic](https://tectonic-typesetting.github.io/), a
self-contained engine that fetches the TeX packages it needs on demand — **no full TeX Live
distribution is ever required.**

```bash
brew install tectonic    # macOS
# or: cargo install tectonic / see the tectonic site for other platforms
```

If tectonic is not installed, scriptorium still emits the `.tex` source; only the PDF step is
skipped, and the end-to-end render test auto-skips with reason `"tectonic not installed"`.

## Usage

```bash
# Render the bundled fixture to <out>/page.tex and (if tectonic is present) <out>/page.pdf
uv run scriptorium render tests/fixtures/minimal_page.json out/
```

```python
from scriptorium import render_pdf

result = render_pdf(page_gt_dict, "out/")   # page_gt_dict is a PageGT-shaped mapping
print(result.tex)            # generated LaTeX
print(result.pdf_path)       # Path to the PDF, or None if tectonic is absent
print(result.gt)             # the input GT echoed back (basis for render-time bboxes)
```

The `scholar-schema` dependency is **optional and lazily imported** — scriptorium works on
raw PageGT-shaped JSON before that repo is published. See
[`docs/design.md`](docs/design.md#schema-dependency).

## Development

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
```

Tests tagged `tectonic` run only when the engine is installed; everything else runs
anywhere, including CI.

## Repository layout

```
src/scriptorium/
  render.py          PageGT JSON -> LaTeX -> PDF (the walking skeleton)
  degradation.py     DegradationSpec: severity-parameterized scan degradation (contract)
  schema_bridge.py   lazy/optional bridge to scholar-schema
  cli.py             `scriptorium render ...`
  templates/         Jinja2 -> LaTeX templates (milestone 1: single_column.tex.j2)
docs/design.md       the input-language contract + template roadmap
tests/               unit tests + the end-to-end tectonic render test
```

## Licensing

Dual scheme — see [`LICENSES.md`](LICENSES.md):

- **Code**: Apache-2.0 ([`LICENSE`](LICENSE)).
- **Corpus releases** (generated synthetic PDFs / images / GT JSON): CC-BY-4.0.

## Context

scriptorium is one of three repos in the `agentic-ocr` programme (the others:
`scholar-schema`, the representation contract; `agentic-ocr`, the system under test). The
generator is deliberately a standalone public project: the ground-truth source must not
cohabit with the system it evaluates, or the evaluation checkers drift toward generator
quirks (Goodhart).
