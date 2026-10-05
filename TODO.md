# Warehouse14 – Improvement To-Do

Review date: 2026-10-05 (based on `main` @ `04ee751`)

## What the latest update contains

The commits since the last real code change are all Dependabot bumps (boto3-stubs, pydantic 2.13.x, markdown, …).
No functional changes have landed, and the README still marks the project as "on hold".
The simple API currently implements **PEP 503 only** (HTML index, `#sha256=` fragments, legacy `file_upload` endpoint).

## Packaging PEPs since the project went quiet (~2023)

Source: <https://peps.python.org/topic/packaging/>

### Relevant to a package index (sorted by priority)

| PEP | Title | Status | Relevance for Warehouse14 |
|-----|-------|--------|---------------------------|
| 691 | JSON-based Simple API | Final | **High.** Baseline for every newer index feature (content negotiation `application/vnd.pypi.simple.v1+json`). |
| 833 | Freezing the HTML simple repository API | Final (May 2026) | **High.** HTML stays at api-version 1.4 permanently. All new features land in JSON only, so we need PEP 691. |
| 629 | Versioning the Simple API | Final | **High, trivial.** Add `<meta name="pypi:repository-version">` / `meta.api-version`. |
| 658 / 714 | Serve distribution metadata (`.metadata` files, `data-core-metadata`) | Accepted | **High.** Lets pip/uv resolve without downloading whole wheels. Extract `METADATA` from wheels on upload. |
| 700 | Extra Simple API fields (`versions`, `size`, `upload-time`) | Final | **High, easy** once the JSON API exists. Needs `size`/`upload_time` on `File` (currently commented out in `models.py`). |
| 592 | Yanking | Final | **Medium.** `data-yanked` / `yanked` plus a UI button for project admins. |
| 792 | Project status markers (active / archived / quarantined / deprecated) | Final | **Medium.** The DynamoDB schema already mentions `isarchived`. Expose it in the UI and the simple API, and block uploads to archived projects. |
| 847 | Problem Details (RFC 9457) for Simple API errors | Draft (Aug 2026) | **Medium, easy.** Return `application/problem+json` for 4xx/5xx instead of plain strings. Worth doing early because it's cheap. |
| 752 | Implicit namespaces for package repositories | Accepted (Jun 2026) | **Medium-high for a private index.** Namespace grants such as `acme-*` per group map naturally onto existing groups/admins. Requires JSON api-version 1.5. |
| 740 | Index-hosted digital attestations | Final | **Low-medium.** Accept and serve attestations (`provenance` field). Useful for supply-chain-conscious companies. |
| 807 | Index support for Trusted Publishing | Draft | **Medium.** OIDC-based upload (GitHub/GitLab CI to a short-lived token) without long-lived API tokens. Fits the OIDC-first design. Wait until it is accepted. |
| 694 | Upload 2.0 API | Draft | **Watch.** Would replace the legacy `file_upload` form endpoint. Don't implement until accepted. |
| 766 | Explicit priority among multiple indexes | Draft (Informational) | **Watch.** Relevant to dependency confusion when users mix Warehouse14 with PyPI. Document recommended `uv`/`pip` config. |
| 708 | Dependency-confusion mitigation (tracks/alternate-locations) | **Rejected** | Not interesting anymore. Use PEP 752 namespaces and PEP 766 guidance instead. |
| 763 | Limiting deletions on PyPI | Withdrawn | Not interesting. |

### Relevant to upload validation and metadata display

| PEP | Title | Status | What to do |
|-----|-------|--------|-----------|
| 625 / 427 | sdist and wheel filename rules | Final | Validate that uploaded filenames match `name` and `version`. Reject non-normalized sdist names. |
| 527 / 715 | Remove unused file types and eggs | Final | Reject `bdist_egg`, `.exe`, `.msi`, and other legacy formats on upload. |
| 639 | License expressions (Metadata 2.4) | Final | Accept `license_expression` and `license_file` upload fields and show them in the UI. |
| 753 | Uniform project URLs | Final | Normalize `project_urls` labels (Homepage, Source, Documentation, …) in the project page. |
| 794 | Import name metadata (Metadata 2.5) | Accepted | Accept and display `import_name(s)`. |
| 770 | SBOMs in wheels | Final | Optionally surface `.dist-info/sboms/` content in the UI. |
| 685 | Extra name normalization | Final | Only for display of `provides_extra`. |

### Not relevant (client or build side)

PEP 735 (dependency groups), 751 (`pylock.toml`), 723 (inline script metadata), 739, 783 (Emscripten), 808, 771, 777/817/825 (wheel variants and Wheel 2.0), 725/804 (external deps), 819 (JSON metadata, draft; keep an eye on it).
These mostly need **no** index changes, but the wheel-variant PEPs (825 provisional, 817 draft) may later need index-side variant metadata.

## Bugs found while reviewing (`warehouse14/simple_api.py`, `models.py`)

- [ ] `upload()`: error paths access `form[':action:']`, a typo that raises `KeyError` (500) instead of 403. Also use 400 rather than 403 for malformed requests.
- [ ] `server_static()`: redirect target is `/simple/{normalized}/{filename}`, but it should be `/packages/{normalized}/{filename}`.
- [ ] `server_static()`: missing `project is None` check, so an unknown project raises `AttributeError` (500) instead of 404.
- [ ] `upload()`: `sha256_digest` comes from the client and is never verified against the uploaded content.
- [ ] `Project.latest_version` sorts version strings lexicographically (`"10.0" < "9.0"`). Use `packaging.version.Version`.
- [ ] `visible()` failures return 401. They should probably be 404, so private project names aren't leaked.

## Maintenance and housekeeping

- [ ] Fix the integration tests (pyppeteer is effectively dead; migrate to Playwright, since Chromium is available in CI images).
- [ ] Drop Python 3.9 (EOL Oct 2025), and update classifiers and the `python` constraint.
- [ ] Migrate `pyproject.toml` to PEP 621 `[project]` table (Poetry 2.x); `[tool.poetry.dev-dependencies]` is deprecated (use dependency groups).
- [ ] Decide on pydantic: drop v1 support (`>=1.8.2,<3`) and use v2 APIs.
- [ ] Replace `black` with `ruff` (lint + format) and add type checking.
- [ ] Remove large commented-out code blocks (`models.py` old `DB`/`SimpleFileDB`, `simple_api.py` leftovers).
- [ ] Revisit the CSS framework (README mentions waiting for materialize-css; decide now or swap it out).
- [ ] Group the Dependabot boto3-stubs bumps (weekly grouped updates) to cut PR noise.
- [ ] Finish the "Deployment" section in the README, add a smoke-test script (TODO in `DEV.md`).
- [ ] Update CHANGELOG (last entry 0.2.0).

## Feature backlog (to plan later)

Rough order: foundation first, then features that depend on it.

1. **JSON Simple API (PEP 691 + 629 + 700)**: content negotiation, `api-version`, `versions`, `size`, `upload-time`. *Foundation for everything below.*
2. **Richer file model**: store `size`, `upload_time`, `uploaded_by`, `packagetype`, `requires_python`, `yanked` on `File` (migration for existing DynamoDB entries).
3. **Core metadata serving (PEP 658/714)**: extract `METADATA` from wheels at upload, store `<file>.metadata`, advertise `core-metadata` hash.
4. **`requires-python` in the simple index**: `data-requires-python` / JSON field from the upload form.
5. **Problem Details errors (PEP 847)**: consistent JSON error responses for the simple API and upload endpoint.
6. **Yanking (PEP 592)**: admin UI and API to yank or unyank a release with a reason.
7. **Project status markers (PEP 792)**: archive, deprecate, or quarantine a project; block uploads when archived.
8. **Upload hardening**: verify hashes server-side, validate filenames (PEP 625/427), reject legacy types (PEP 527/715), and use proper HTTP codes.
9. **Namespaces (PEP 752)**: reserve prefixes (e.g. `acme-`) for groups and enforce them on upload. Strong protection against internal name squatting and confusion.
10. **Metadata 2.4/2.5 display**: license expressions (639), uniform project URLs (753), import names (794).
11. **Trusted Publishing (PEP 807)**: OIDC token exchange for CI uploads, once the PEP is accepted.
12. **Attestations (PEP 740)**: accept and serve provenance.
13. **Multi-index guidance (PEP 766)**: docs for configuring pip/uv to use Warehouse14 alongside PyPI safely.
14. **Watch list**: Upload 2.0 (PEP 694), Wheel Variants (PEP 817/825), JSON Package Metadata (PEP 819).
