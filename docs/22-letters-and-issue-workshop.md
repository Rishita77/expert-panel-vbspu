# Letters and issue tracking - workshop

Prepared 14 September 2026. Proposed for discussion; application code and schema changes await approval of the concrete package.

## User decisions following the workshop (DEC-044)

- Staff supply the official reference number at initial document preparation; do not generate university reference numbers automatically.
- Deliver the document for now. E-signing is explicitly deferred to a stretch goal by the user, overriding the initial SRS signing requirement for this release. Do not require an e-sign integration to download a reviewer-approved document, or label that document electronically signed. Actual external dispatch/signature evidence is not implied by downloading it.
- Reviewer is the approval/issuing authority for this phase.
- Keep the appearance and structure almost the same as the two supplied PDFs. Retain approved nomination rules where sample wording/counts differ. Do not copy scanned signatures into generated documents.

These answers resolve numbering mode, signing scope, reviewer authority and layout direction. The proposed digital-signing prerequisite below is superseded for this release. Next prepare sample-based draft previews and the concrete schema/migration mapping for approval. Do not invent a separate dispatch workflow or official numbering pattern.

## Source review and current boundary

Reviewed all four pages of the two VC sample PDFs and SRS sections 20-21. Use the samples' bilingual letterhead, Hindi body, institution heading, numbered expert sections and signature area. Keep separate Principal/HoD and subject-expert templates. The sample membership wording differs from the approved composition; retain current approved rules, not sample counts. The samples do not establish an automatic reference-number scheme, current signatory details, dispatch recipients or signing integration credentials. Do not reuse scanned signatures as signing credentials.

SRS 21 requires reference number, date, college, post, subject, selection date, VC nominee, experts, additional category members, university conditions and authorised digital/e-signature provision. Counts remain tied to final lock under the user's later decision; generating, signing, issuing or reprinting a letter must not change utilisation.

Existing implementation has immutable AllocationRun recommendations and FinalSelection locks. It does not yet have a versioned issued-offer record or category addendum. Document 21's locked-change accounting does not complete those earlier offer requirements. Include those records and journeys in this package before claiming full letter issuance.

## Proposed document types

| Document | Authoritative source | Prerequisite |
|---|---|---|
| Offered-panel letter | Reviewed immutable offered revision: one Principal, five Professors, separate VC, supplements as required | Complete engine evidence, required verification, VC decision evidence and authorised offer approval |
| Revised offer / category addendum | Engine-backed change linked to its original offer | Reviewer confirmation and explicit newly communicated names; no manual off-engine addition |
| Final-selection record | Locked final membership: one Principal, four Professors, separate VC and required supplements | Existing reviewer lock; external issuance of this additional record subject to university preference |
| Replacement notice | Confirmed change and resulting effective committee | Confirmed replacement; both old and new identities preserved |
| Cancellation notice | Confirmed cancellation | Confirmed decision and reference to affected original letter |

Management chooses from the offered names. Final lock must not be required to generate the first offered-panel letter. Issuing an offer does not count its members. Category additions before final lock must be explicitly offered before they can be selected.

## Proposed staff journey

1. Processor prepares an offer from complete engine evidence, or prepares a notice from the relevant confirmed decision.
2. Show the exact source revision and a draft preview. Use visibly marked sample branding where verified university assets/signatory text are missing. Hindi body is the initial format; preserve supplied English names without automatic translation.
3. Processor records the official reference and recipients; reviewer approves the exact document revision. Proposed offer-approval authority is reviewer, separately from already approved final-lock authority.
4. Sign using the confirmed university method. Printing or previewing does not mean signed; a recorded signature status must not masquerade as cryptographic verification.
5. Authorised staff record issue against the approved, signed version. Proposed issue authority: reviewer, with processor preparing and recording dispatch evidence. Signature and issue authority need confirmation.
6. Preserve the issued PDF bytes, source facts, template version, reference, signer/issuer, timestamps and checksum. Downloads return the stored issued artifact, never regenerate it using current master data.
7. Record dispatch separately with recipient, channel, date and evidence. Until communication services and recipients are approved, provide no automatic external sending. A failed delivery does not repeat approval, issue or accounting.
8. Corrections create a linked new version; supersession is explicit. Reprints preserve the same artifact/reference. A name change requires the approved panel-change workflow, not editing PDF text.

## Proposed schema and constraints

| Record | Main facts and ownership |
|---|---|
| Offered revision | Request and revision, allocation run, predecessor, immutable member/policy/eligibility snapshot, prepared/reviewed actors and timestamps; unique revision per request |
| Offered member | Expert identity, role/position, historical name/institution/category and source evidence; distinct person per revision |
| Template version | Document type, language, approved text/layout version, approved signatory/branding configuration and provenance; immutable after use |
| Letter revision | Source offer/lock/change, template version, predecessor, official reference, letter date, source snapshot, private PDF storage key/checksum, prepared/approved/signed/issued state and actors/timestamps |
| Document event | Append-only prepare/approve/return/sign/issue/supersede event, actor, time and reason; distinguish source approval from document approval |
| Dispatch record | Issued letter, exact recipient/channel, attempt state, evidence/reference, recorder/time; retries linked to original attempt |

An issued letter must have a unique official reference under the approved numbering scope. Reject stale source revisions at approval and issue. Serialize issue and reference allocation; retries return the original issued result. Store PDFs privately and enforce staff permissions on download. Template changes apply only to new drafts. No write to utilisation from document services.

Migration implications: introduce explicit offered revisions alongside existing AllocationRun records; do not retroactively declare previous recommendations issued or invent references/signatures. Bridge existing final selections to documented source records explicitly. Addenda and revised offers retain predecessor links. Detailed migration mapping and data examples will be finalised after the issue/signing decisions below.

## Layout and acceptance

- Approve one synthetic Principal/HoD and one subject-expert preview before template release. Preserve sample structure with corrected approved role counts and mandatory SRS fields.
- Hindi conjuncts/matras, English names and long institution names must survive rendering, extraction and printing. Embed an approved Devanagari-capable font; test multi-page wrapping and signature placement.
- Test offered-panel names versus final selected names, required extra categories, revised offers, replacements and cancellations.
- Test missing date/reference/approval/signature blocks, duplicate issue, stale revisions, unauthorised downloads, immutable reprints and zero utilisation effects.
- Test processor preparation, reviewer return/approval, signing status and issue/dispatch journey in the browser.
- Review existing replacement/history safeguards before using their output in official notices. Prior passing tests do not by themselves establish all document-20 acceptance cases or operational readiness.

## Decisions to settle

1. Numbering: recommend staff enter the existing university outward/dispatch reference initially, with duplicate prevention. Alternatively automatic numbering requires exact prefix, scope and rollover rules.
2. Signing: identify whether the university uses wet signing/scanned return, certificate-based digital signature, or e-sign service. SRS specifies digital/e-sign provision; a manual interim workflow requires explicit approval and does not satisfy a required digital-sign integration by itself.
3. Issuing: confirm reviewer authority to approve offers and issue signed letters. Specify the receiving office/person; recommend processor-recorded manual dispatch initially, with automatic communication separately configured.
4. Content: confirm current signatory designation/name, approved branding, conditions and whether final-selection records are externally issued or internal only. Samples guide layout but do not establish current authorised content.

Next: resolve the first three operational questions, produce the exact schema/migration mapping and synthetic letter previews, then seek package approval before implementing official issue.
