# scriptorium design: the input-language contract

scriptorium's one design rule is **schema-first generation**. There is no bespoke authoring
DSL: the input *is* a `DocumentGT` / `PageGT` instance (the same ground-truth schema the
consuming OCR pipeline targets) plus a `DegradationSpec`. Because scriptorium authored the
typesetting from that GT, the emitted ground truth is correct *by construction*, and **every
schema element must earn a renderer** — an element the schema can express but no template can
typeset is a gap, by definition.

This document specifies the input language, the output, and the template roadmap that turns
"the schema claims to express X" into "scriptorium can render X and prove the GT."

---

## 1. Input

```
input  =  (DocumentGT, [PageGT, ...])   +   DegradationSpec
```

### 1.1 The GT half: DocumentGT / PageGT

The structural input is a document-level `DocumentGT` and one `PageGT` per page, as defined
in the [`scholar-schema`](https://github.com/loganrooks/scholar-schema) package (forked from
scholardoc's `scholargt` v2.0.0 schema). The renderer reads, at minimum:

| Schema element | What the renderer does with it |
|---|---|
| `PageGT.regions[*]` (`label`, `text`, `bbox`) | Typesets each region's text in a layout slot determined by its `SpatialLabel` |
| `PageGT.reading_order` | Orders body content; the linearization the GT asserts |
| `Region.semantic_labels` / `SemanticType` | Selects the renderer (e.g. `note` -> `\footnote`, `marginal_reference` -> margin number) |
| `DocumentGT.source` | Title / author block, document metadata |
| `DocumentGT.elements[*]` (`SemanticElement` union) | The cross-page semantics each milestone learns to render (notes, citations, marginal refs, sous rature, commentary) |
| `DocumentGT.registers` (`LayoutRegister`) | Drives multi-register layouts (dual-column, Talmudic frame) |
| `DocumentGT.note_schemas` | Note marker style (arabic / roman / symbolic) and reset boundary |

The key elements the roadmap (§3) is built to exercise: `Note`, `MarginalReference`
(with `ReferenceSystem` ∈ {stephanus, bekker, akademie, sz_pagination, diels_kranz, ...}),
`SousRature`, `Commentary`, and `LayoutRegister`.

#### Schema dependency

The schema package is being built **in parallel** and may not exist when you read this.
scriptorium therefore imports it **lazily and optionally** through
[`scriptorium.schema_bridge`](../src/scriptorium/schema_bridge.py):

- If `scholar-schema` is installed, inputs are validated against the real pydantic models.
- If not, scriptorium runs on **raw PageGT-shaped JSON** with a minimal structural check, so
  the walking skeleton and the bundled fixture work today.

`render_*(..., strict_schema=True)` forces the real-model path and raises a clear error if
the package is absent. *TODO(scholar-schema):* once the repo is published and pinned, flip
the bridge to strict-by-default and drop the structural fallback.

### 1.2 The degradation half: DegradationSpec

A [`DegradationSpec`](../src/scriptorium/degradation.py) is **severity-parameterized** so
that scan difficulty is a single controlled experimental variable. Fields map to
augraphy effect families:

| Field | Effect | Range |
|---|---|---|
| `severity` | master dial; `0.0` == clean pass-through | `[0, 1]` |
| `skew` | page rotation | `[0, 1]` |
| `noise` | additive sensor / paper noise | `[0, 1]` |
| `bleed_through` | ghost of the verso showing through | `[0, 1]` |
| `shadow` | scanner / binding shadow gradient | `[0, 1]` |
| `jpeg_quality` | output JPEG quality (lower == more block artifacts) | `[1, 100]` |
| `seed` | RNG seed for reproducible degradation | `int \| None` |

`DegradationSpec.from_severity(s)` builds a spec where one dial drives every effect — the
sweep primitive for generating clean → rough strata of the same page.

**Status:** the spec is the stable contract now; the scan-simulation backend
([augraphy](https://github.com/sparkfish/augraphy)) is **planned, not yet integrated**. The
current reference `apply()` is an honest stub: a clean spec passes the image through; a
non-clean spec raises `NotImplementedError` rather than faking scanner physics.
*TODO(augraphy):* construct an augraphy pipeline from the spec fields.

---

## 2. Output

```
output  =  rendered PDF
        +  page images (one raster per page; degraded per the DegradationSpec)
        +  GT JSON, schema-conformant and unmodified in coordinate space (normalized bboxes)
        +  render manifest (sidecar): everything only the renderer knows
```

The GT stays strictly `scholar-schema`-conformant — bboxes remain normalized `[0,1]`, as the
schema's `BBox` validators require. Everything the renderer alone knows travels in a
**versioned sidecar render manifest**, never grafted onto the GT: pixel-space geometry is
*derived* (`px = normalized × page dimensions from the manifest`), so no consumer ever needs
a schema the schema repo doesn't publish. This closes the loop — the `(image, GT, manifest)`
triple is aligned because the same process produced all three — without forking the contract.

### 2.1 Render-manifest contract (v1, draft)

One `manifest.json` per batch run; one entry per page. Required fields:

| Field | Contents |
|---|---|
| `manifest_version` | this contract's version (semver) |
| `generator_commit` | scriptorium git SHA that produced the run |
| `schema_version` / `schema_pin` | `scholar-schema` version + exact pin used for validation |
| `template_id`, `template_version` | which renderer produced the page |
| `source_text` | source-work identifier + license/provenance tag (public-domain rule) |
| `degradation` | severity, seed, backend + version, ordered op list *actually applied* |
| `stratum` | the difficulty band (see the strata definition in the engine packet) |
| `image` | path, format, DPI, `width_px`, `height_px`, sha256 |
| `page_gt` | path, sha256 |

A page is reproducible from its manifest entry alone (same commit + template + source +
seed ⇒ byte-identical output); a third-party tool can consume `(image, GT, manifest)`
without pinning any other repo in the programme. This is the appropriability contract:
corpus *packs* (curated bundles of templates × sources × strata for a given purpose) are
defined over these triples, not over ad-hoc folders.

The walking skeleton (milestone 1) emits the PDF and echoes the validated GT
(`RenderResult.gt`); raster page-image emission, the manifest, and the render-geometry
alignment pass land with the augraphy integration.

---

## 3. Template roadmap (milestones)

Templates are ordered by how much of the schema they force into a renderer. Each milestone is
a `(LayoutRegister/SemanticElement) -> LaTeX` mapping. The hard cases are not deferred
decoration; they are **the reason scriptorium exists**: the cases the schema claims to express
that no public benchmark tests (every public OCR benchmark excludes footnotes, floating
elements, non-English text, and critical apparatus).

### Milestone 1 — single column + footnotes  ✅ *(walking skeleton, shipped)*

Single-column body in reading order; `Note` (placement `page_bottom`) rendered as
`\footnote`, keeping the in-text marker and note content paired exactly. Template:
[`single_column.tex.j2`](../src/scriptorium/templates/single_column.tex.j2). Exercises:
`text_block`, `note_area`, `SemanticType.NOTE`, `reading_order`.

*Why:* footnote anchoring (marker ↔ note pairing) is the canonical under-benchmarked
capability — olmOCR-Bench deliberately excludes it. It is the smallest layout that produces
non-trivial GT a markdown dump cannot represent.

### Milestone 2 — marginal reference numbers (Stephanus / Bekker / Akademie)

Body text with canonical reference anchors set in the margin (`MarginalReference` +
`ReferenceSystem`). Exercises the `marginal_reference` element and the print-citability
property: the mapping between a margin number and the span it anchors.

*Why:* these systems (Stephanus for Plato, Bekker for Aristotle, Akademie for Kant,
SZ-pagination for Heidegger) are how philosophy is *cited*. No general benchmark contains
them; a pipeline that drops them is useless to a reading scholar.

### Milestone 3 — sous rature (text under erasure)

`SousRature` elements: text simultaneously present and struck through (Derridean
*sous rature*). Renders the term overprinted with its erasure mark while keeping the
underlying text recoverable in GT.

*Why:* it is a typographic construct that is *meaningful*, not noise — an OCR system that
silently "corrects" it destroys the philosophical content. It tests whether the
representation can mark text as present-yet-crossed-out.

### Milestone 4 — Glas-style dual-register columns

Two parallel reading streams (`LayoutRegister`) typeset as facing columns with independent
flow, after Derrida's *Glas* (Hegel column / Genet column). Exercises multi-register reading
order: two streams that must not be linearized into one.

*Why:* dual-register layout breaks the single-`reading_order` assumption most pipelines bake
in. It is the simplest layout where "what reads after what" is genuinely ambiguous without
register identity.

### Milestone 5 — Talmudic / commentary frame

A central text framed by concentric commentary registers (`Commentary` + multiple
`LayoutRegister`s; Rashi-style apparatus, after Robert Gibbs). Exercises nested registers,
RTL/bidi (`text_direction`), `ScriptVariant` (square Hebrew vs Rashi script), and
`Commentary.passage_ref` anchoring.

*Why:* the maximal stress test — every register, direction, and commentary-anchoring feature
the schema claims, in one page. If scriptorium renders this with provable GT, the schema has
survived contact with the hardest real layout in the corpus.

---

## 4. Why schema-first (the epistemic argument)

The previous project (scholardoc) stalled on a circular dependency: ground truth required an
annotation tool, which required a validated GT schema, which was never validated because no
GT existed. scriptorium breaks the circle by *manufacturing* GT: author the GT, render from
it, and the (image, GT) pair is aligned by construction at zero annotation cost.

The roadmap's discipline — *every schema element must earn a renderer* — also doubles as a
schema test. An element scriptorium cannot render is an element whose meaning is
underspecified, surfacing the gap before any extractor depends on it. This is the
pilot-annotation the scholardoc audit asked for, executed mechanically.

One independence constraint (see [`README.md`](../README.md) "Context"): scriptorium is a standalone repo, never merged
into the OCR pipeline. The GT source must not cohabit with the system it evaluates, or the
evaluation checkers drift toward generator quirks (Goodhart).
