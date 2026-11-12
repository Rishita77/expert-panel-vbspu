# Registrar confirmation before final release

Approved 12 November 2026. Letter-content revisions remain deferred until the new format is supplied.

## Workflow

1. VC/Admin locks the final selection. This is still the utilisation-counting action.
2. Registrar/VC/Admin prepares the final letter; VC/Admin approves its PDF as before.
3. The approved final letter enters Documents → Pending Registrar release.
4. Registrar/Admin checks the final panel and approved PDF, then confirms release on the letter page.
5. POC can now open the final panel and download that exact released final-letter revision from the request.

VC-only accounts cannot perform Registrar confirmation. A user holding both roles can perform both responsibilities; no separate-person restriction was requested.

## Persistence and access

FinalRelease records the locked selection, exact approved letter revision, confirming staff account and timestamp. Each selection and letter revision may be released once. PostgreSQL guards prevent modification/deletion and reject a release with a mismatched or unapproved source. Confirmation also checks that the approved PDF exists and matches its stored checksum.

Repeated confirmation of the same letter returns the existing release. Confirmation of a second letter for an already released selection is rejected. Approved PDF bytes and nomination ledger entries do not change during release.

POC request links, direct final-selection access and direct PDF downloads all check release. Privileged officers can inspect the approved sources beforehand. The request shows a waiting-for-Registrar status without exposing names to POC.

## Existing records

No historical letter is automatically released. Existing approved final letters enter the pending queue until Registrar/Admin confirms them. There is no new letter-content version or signature integration.

## Verification

A disposable PostgreSQL database and fictional records verified pending/released queues, role permissions, direct-link access before and after confirmation, corrupted-PDF rejection, repeat-confirmation idempotency, immutable release/audit records, and unchanged utilisation and approved PDF.
