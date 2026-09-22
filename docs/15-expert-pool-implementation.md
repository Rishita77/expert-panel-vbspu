# Expert and approved-pool phase — handover

12 September 2026. User approved the workshop after clarifying that Principal and Professor can be recorded together and that checks belong in normal staff forms, with no separate inspector role/screen.

## Delivered

- One expert identity, automatically assigned permanent PostgreSQL sequence, Unicode name, recorded category, contact details and subject links.
- Separate current post and academic rank, including Principal + Professor. One current home institution, preserved history, dated changes, explicit rank/internal-external evidence and concurrent-edit protection.
- Existing institution/subject identities reused. College affiliation details remain removed. Own-college comparison is visible within expert/list detail, using the chosen requesting college's identity.
- Approval records and versioned candidate lists, including role, appointment/subject scope, members and validity. Current main-list approval requires EC provenance; category/VC source evidence is recorded with pending operational-authority checks clearly identified.
- Staff record existing University approval from the list page. Missing required facts prevent the action. There is no additional verifier account or standalone readiness page.
- New versions copy the old scopes/members into an editable draft. Recording the replacement version supersedes the previous one; earlier versions and audit remain.
- Read-only reviewers see non-contact expert facts/history. Maintainers/processors can see mobile/email. Account administration alone grants no expert access. Reviewers cannot access CSV preview/reference downloads or edit records.
- Six downloadable CSV header templates, a contact-free reference mapping, bounded UTF-8 validation preview and the [staff collection guide](14-expert-data-collection-guide.md). Preview never commits data or consumes a sequence.

## Demonstration

Use the existing `demo.poc` account from `.local/demo-access.md`:

1. Open `/office/catalog/experts/`. The three labelled demonstration experts include a Principal/Professor, a Professor and an Assistant Professor.
2. Inspect the Principal's separate post/rank and multiple list memberships. Select **प्रदर्शन अनुदानित महाविद्यालय** in the inline college check to demonstrate own-college exclusion.
3. Open `/office/catalog/pools/`. Four synthetic source lists demonstrate Principal, Professor, SC/ST supplement and VC memberships. These are not six-name nomination outputs.
4. Open an approved list and create a new draft version with a reason. Edit that draft's scope/member details; the original approved contents are protected.
5. Open `/office/catalog/import/`, download a template and validate a CSV. Review row errors/warnings; no records are imported.
6. Sign in as `demo.reviewer` and verify that expert contacts and editing actions are absent, including in audit details.

Synthetic approval reference `DEMO-EC-2026-NOT-OFFICIAL` is explicitly not University approval. The seed command added its own labelled aided-college fixture instead of changing existing colleges' unknown management classifications. A failed first seed attempt rolled back all its records because the existing sample college's classification did not establish internal VC eligibility; sequence gaps from that rollback are expected and harmless.

Existing server command remains:

```powershell
& .\.venv\Scripts\python.exe manage.py office 127.0.0.1:8000 --settings=config.foundation
```

For a new synthetic environment with foundation demo accounts/directory already created, `seed_experts_demo --settings=config.foundation` adds these examples. It refuses to overwrite existing labelled demo experts. Browser verification also creates labelled synthetic examples and retains them; it does not clean or reset user records.

## Implementation and integrity

Modules: `apps/experts` (identity, institution history, forms/views, CSV preview) and `apps/panels` (approval, list/version, scope, membership, inline checks and state services). Additive migrations reused the existing staff/directory/draft tables. No utilisation ledger or nomination transaction tables were introduced.

PostgreSQL creates the sequence; database triggers reject changes to assigned numbers. A partial unique constraint enforces one current institution. Service revision checks and the shared foundation access mutex serialize authorised changes; an additional database guard rejects known overlapping institution intervals.

Approved list business facts, member/scope rows and their referenced approval records are protected by database triggers. Allowed supersession preserves the earlier row; material changes go into the copied draft. Expert master facts remain current and independently audited; final issued-panel snapshots belong to the later nomination phase. Do not treat current master display as an immutable historical letter.

Expert audit contacts are filtered before rendering reviewer responses. CSV reference exports exclude contact fields and neutralise formula-leading display names. CSV uploads are read in memory with explicit byte/row bounds and are not saved as files or audit payloads.

Tests cover shared identity/multiple roles, sequence guards, current-institution concurrency, invalid intervals, rank/category/VC checks, role/contact visibility, audit rollback, list versioning/immutable evidence, invalid membership dates, duplicate memberships, unknown validity end, CSV bounds/matching/contradictions, zero preview writes and sequence consumption, and missing-record action handling.

Verification commands:

```powershell
& .\.venv\Scripts\python.exe manage.py check --settings=config.foundation
& .\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=config.foundation
& .\.venv\Scripts\python.exe -m pytest tests/test_foundation.py tests/test_experts.py --ds=config.foundation -q
& .\.venv\Scripts\python.exe -m pytest tests/test_preview.py -q
& .\.venv\Scripts\ruff.exe check apps config tests
```

Browser checks are `tests/experts_browser.cjs` and the existing `tests/foundation_browser.cjs`, using the bundled Playwright/Chrome as described in document 12. Screenshots: `test-results/expert-history-desktop.png`, `approved-list-desktop.png`, `expert-mobile.png`. Desktop and mobile layouts were visually inspected.

## Next boundary

The allocation workshop will decide the remaining ranking/history/date/authority details using concrete examples and these records. No allocation, offered panels, final selection/lock, utilisation changes, official letters, real bulk import or production deployment is claimed here. SRS fairness and user overrides remain authoritative; pending offers do not become an additional ranking factor.
