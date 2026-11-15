# Mathew Godinez's portfolio

Four static pages hosted on GitHub Pages. No JavaScript, analytics, external fonts, contact form or build service.

## Editing

- `content/*.txt`: public page copy. `{{key}}` inserts a value from `facts.json`; `{{key:date}}` inserts its source date.
- `facts.json`: public values and dated provenance. A source date can be an attestation date; read the `evidence` field before treating it as a measurement.
- `content/resumes.json`: public resume copy, using the same facts.
- `assets/work/`: carefully selected historical excerpts and an unmodified screenshot containing fictional records. Historical transcriptions retain their original dates and numbers rather than updating as current facts change.
- `drafts/`: private, ignored work. Never add it to Git.

Reconcile source records before changing claims. Keep personal contact records, private collaborator details, application answers and unreconciled marketing metrics out of this repository.

## Build

Run `python3 build.py` after copy or fact changes. It checks public page word limits, fact references, source dates, image files and the local private banned-phrase list. `@quote`, `@image`, `@table` and `@links` take one JSON object (or link array) per line. A section anchor uses `## Heading {#anchor-name}`. No arbitrary HTML is accepted in content.

Run `python3 build_resumes.py` after changing resume copy or facts. It requires ReportLab and the macOS Arial/Georgia fonts and emits both PDFs in `assets/`. These are public variants: no phone, street address, GPA or unreconciled campaign metrics.

`python3 build_assets.py` reproduces the typographic share image with Pillow and the same local fonts. It is not needed for ordinary copy updates.

Before publishing: inspect both PDF renders; check navigation, downloads, figure loading and keyboard focus; test every page at phone and desktop widths. The public pages are generated files committed alongside their sources. A push to `main` publishes through the existing GitHub Pages configuration.
