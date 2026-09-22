# Letter schema and preview approval package

Status: proposed for approval. DEC-044 governs: staff-entered reference, reviewer authority, downloadable unsigned documents, e-sign deferred. No application migration or production policy activation is made by this package.

## Documents for review

User supplied `C:/Users/rishi/Downloads/logo.png` for the central letterhead image. Embedded unchanged in both previews, replacing the logo placeholder.

Header correction approved by user: top left reads “प्रो० आर. के. सिंह”, “कुलपति”, then “Prof. R.K. Singh”, “Vice Chancellor”. Applied to both previews. This supplies the previously pending personal name for these layouts; the logo remains pending.

- `output/pdf/principal-hod-letter-preview.pdf`
- `output/pdf/subject-expert-letter-preview.pdf`

Both are fictional offered-panel previews, not locked final selections. They retain the bilingual header, college heading, numbered sections and signature position from the samples. They use the approved one Principal/five Professors offer, separate VC, and example category supplements, rather than copying contradictory sample counts. A four-Professor final selection is described separately. Logos, signatory personal name and unconfirmed university conditions remain visibly provisional; no scanned signature is reproduced. Unicode Hindi was visually checked using a browser print renderer after the initial ReportLab shaping proved unsuitable for these previews.

## Proposed user journey

Processor enters official reference and letter date at preparation, selects the complete engine recommendation and reviews its snapshot. Reviewer may return with a reason or approve the exact revision for download. Approval freezes a stored PDF and records the actor/time; it does not claim a digital signature, external delivery or change in utilisation. Staff can download the identical approved bytes repeatedly. A subsequent correction creates another revision and returns to review.

Offer approval precedes management's final choices. A separately approved final-selection record uses locked members; a replacement or cancellation notice uses a confirmed change. Proposed first delivery includes offer, addendum, final record and change notice formats, with the two attached layouts defining the common styling. An offer must never require final lock as a prerequisite.

## Concrete proposed entities

| Entity | Fields and constraints |
|---|---|
| OfferVersion | UUID; request FK; request_revision; sequence; source_run FK; previous_offer nullable FK; kind initial/replacement/category_addendum; state draft/submitted/returned/approved; policy_snapshot JSON; created_by/time; approved_by/time nullable. Unique (request, sequence); approved records immutable. |
| OfferMember | UUID; offer FK; expert FK; role; seat_position; snapshot JSON containing name, category, institution, designation/rank and eligibility evidence. Unique (offer, expert) and (offer, role, seat_position). No arbitrary off-engine identities. |
| LetterTemplateVersion | UUID; template_key; version; document_kind; language; immutable layout/text identifier and content checksum; branding/signatory snapshot; approval actor/time. Unique (template_key, version); used versions cannot be edited. |
| Letter | UUID; request FK; kind offer/addendum/final/replacement/cancellation; staff_reference text max 500; normalised_reference; current_approved_revision nullable FK. Propose case-insensitive whitespace-normalised reference uniqueness across app letters; different revisions of the same letter retain its reference. This uniqueness scope is part of package approval, not an assumed university convention. |
| LetterRevision | UUID; letter FK; revision integer; template FK; source_offer/source_selection/source_change nullable FKs; source_revision identifier; predecessor nullable FK; letter_date; content_snapshot JSON; state draft/submitted/returned/approved; created_by/time; approved_by/time; private PDF key; SHA-256 checksum. Unique (letter, revision); exactly one source type appropriate to kind. Approved bytes and facts immutable. |
| LetterEvent | UUID; letter_revision FK; action prepared/submitted/returned/approved/superseded/downloaded; actor FK; timestamp; reason max 1000. Append-only. Download is not dispatch. |

Database references use PROTECT. Preserve raw reference exactly for printing while using the normalised value only for duplicate checking. Blank reference/date blocks submission. No signature state or dispatch table is required for this release. Future integrations can add linked records without redefining approved PDF contents.

## Source ownership and migrations

1. Add offer/template/letter/event tables; no rewriting or deleting existing AllocationRun, FinalSelection, PanelChange or ledger records.
2. Add nullable `source_offer` to FinalSelection and nullable `offered_member` to FinalMember for compatibility. All newly created operational selections must use an approved offer; old rows retain their original source_run and are explicitly legacy/demo until reviewed. Do not fabricate an offer reference or approval for them.
3. Store source facts at preparation and validate again at submission/approval. Case changes or competing revisions require a visible refresh and another review. Approved offers and notices retain their own historical facts after later expert-master changes.
4. An approved addendum links the earlier offer and engine evidence; final selection uses the effective offered membership. Preserve retained names and roles, avoid duplicates, and check required categories. Approval of an offer/addendum is count-neutral.
5. Lock the request and letter while approving; recheck authority/current revision. Build the PDF before final commit and freeze its checksum/source revision in the transaction. Failed rendering leaves nothing approved; a competing source change rejects the prepared artifact. Clean unreferenced temporary files through a controlled process.
6. Confirmed replacements/cancellations feed notices only after their integrity checks pass. A document operation cannot confirm a business change itself or mutate utilisation.

## Example and acceptance

Staff enter `EXAMPLE/2026/001` for offer revision 1. Reviewer returns it for a date correction; revision 2 preserves the earlier draft and reason. Reviewer approves revision 2. All downloads return the same bytes. Management's later four-Professor selection produces a separate final record. A replacement notice references the original letter and confirmed change; it does not silently replace names in the original PDF.

Before delivery verify Hindi shaping, embedded fonts, no clipping, long names, category extras and multi-page signature placement. Test staff-only access, reviewer-only approval, blank/duplicate reference rejection, stale revisions, duplicate clicks, immutable downloads after master changes, source linkage and zero document-side utilisation changes. Confirm first-offer generation before final lock and addendum selection from approved offered names.

## Approval requested

Approve the two preview layouts and this entity/workflow package, including app-wide normalised reference uniqueness and version-preserving corrections. The preview's conditions are proposed wording for review. Personal signatory details and official logo remain pending verified assets/content; they must not be guessed for operational output. Keep e-sign and automatic dispatch outside this release.
