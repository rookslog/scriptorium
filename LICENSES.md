# Licensing

scriptorium uses a **dual licensing scheme**: one license for the software, a different one
for the synthetic corpus the software produces. The two are deliberately separate because
they protect different things.

## Code — Apache License 2.0

Copyright 2026 Logan Rooks.

All source code in this repository (everything under `src/`, `tests/`, the templates, the CI
configuration, and the documentation) is licensed under the
[Apache License, Version 2.0](LICENSE).

Apache-2.0 is a permissive license: you may use, modify, and redistribute the code, including
in closed-source and commercial work, provided you preserve the copyright and license notices
and state significant changes. It also includes an explicit patent grant.

## Corpus releases — Creative Commons Attribution 4.0 (CC-BY-4.0)

Any **synthetic corpus** that scriptorium generates and that is published as a *release*
artifact — rendered PDFs, degraded page images, and the accompanying ground-truth JSON — is
licensed under
[Creative Commons Attribution 4.0 International (CC-BY-4.0)](https://creativecommons.org/licenses/by/4.0/).

You may share and adapt the corpus, including commercially, **provided you give appropriate
credit** (cite scriptorium and the corpus release), link the license, and indicate if changes
were made.

### Why two licenses

- **The code is software**; Apache-2.0 is the standard permissive software license with a
  patent grant, matching the rest of the `agentic-ocr` programme.
- **The corpus is data / a creative dataset**, not software. A content license (CC-BY-4.0) is
  the appropriate instrument for a published benchmark dataset, and CC-BY is the convention
  for openly redistributable research corpora. The attribution requirement is what lets the
  corpus function as a *citable* benchmark.

### Source-text provenance (important)

scriptorium typesets **trusted public-domain source texts** (e.g. Project Gutenberg,
Wikisource, Perseus / Open Greek & Latin, Deutsches Textarchiv). The CC-BY-4.0 grant covers
scriptorium's *contribution* — the typesetting, layout, degradation, and ground-truth
annotation. The underlying source texts must already be in the public domain (or otherwise
freely licensed) in the relevant jurisdiction; corpus releases will document the provenance
and public-domain status of every included source. Acquired non-public-domain material is
**never** redistributed and never included in a corpus release.

## Third-party dependencies

Runtime and build dependencies (Jinja2, Pillow, the tectonic engine, and the optional
`scholar-schema` package) are distributed under their own licenses; see each project for
details. They are not relicensed by this repository.
