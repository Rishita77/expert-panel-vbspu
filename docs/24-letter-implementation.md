# Letter workflow implementation

Status: implemented after the user's approval of document 23. DEC-044 remains the governing release scope: downloadable unsigned documents, reviewer approval, no external dispatch and e-sign deferred.

## Delivered workflow

1. A processor opens a complete current offer, a locked final selection, or a confirmed replacement/cancellation and enters the staff-provided reference and letter date.
2. The system stores a source snapshot and creates a draft revision. Whitespace- and case-normalised references are unique across application letters.
3. A processor submits the revision. A reviewer may return it with a reason or approve it.
4. Approval renders the PDF, saves the exact private bytes, records a SHA-256 checksum and prevents changes to the approved facts or file reference.
5. Authorised University staff can download the approved PDF. Every download is recorded. A document never changes utilisation, confirms a business change or represents an e-signature or external delivery.

The reviewer/Registrar controls preparation and submission. The VC or administrator controls return and approval. This follows the approved authority boundary and retains individual actor/time history.

## Stored records and guards

`Letter` preserves the request, kind, original reference and creator. `LetterRevision` preserves the snapshot, one of the permitted sources, status, review data, checksum and private PDF key. `LetterEvent` is append-only preparation, submission, return, approval and download history.

Database guards prevent changing or deleting letter identity, deleting revisions, changing approved revision facts, or changing/deleting events. The private document root is outside public static files. PDF rendering uses a headless Chromium-compatible browser with a per-document temporary profile. `LETTER_PDF_BROWSER_PATH` (or `CHROME_BIN`/`CHROMIUM_BIN`) selects the browser, and `LETTER_DEVANAGARI_FONT_PATH` optionally selects a font. On Linux, install Chromium and a Devanagari font such as Noto Sans Devanagari; on Windows, Mangal or another Unicode Devanagari font can be configured. `LETTER_PDF_NO_SANDBOX=1` is reserved for an explicitly isolated local/container runtime; the production default keeps the browser sandbox enabled.

The first implementation provides one approved revision per letter. A later correction/revision screen must create revision 2 and preserve revision 1; it is intentionally not a silent edit path.

## Verification

- 33 allocation, lock, change and letter workflow tests pass against PostgreSQL.
- The renderer test confirms the application produces a PDF beginning with the PDF file signature.
- Migration consistency and Django system checks pass.
- The reviewed header uses the approved Vice-Chancellor block and supplied logo asset. The browser print renderer shapes Devanagari correctly and runs as a non-interactive server process; it does not depend on a user's desktop browser session.

## Deliberately deferred

- E-signature and delivery integrations.
- Automatic email/SMS dispatch and delivery receipts.
- A future offer-version/addendum workflow beyond the existing immutable allocation-run source.
- A correction UI creating later letter revisions.
- University confirmation of production font distribution, official wording and production storage/backup procedure.
