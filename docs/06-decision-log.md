# Decision and change log

Current baseline: [University intake and allocation requirements](09-current-requirements.md). Decisions below dated 8 September are historical where superseded by DEC-014–017. The user has expressed readiness to start coding, conditional on a complete SRS reread and no silent assumptions (DEC-019). Previously agreed detailed-schema/phase review gates remain in place.

DEC-018 permits a provisional shared composition for subject-expert appointments and requires independently versioned appointment-type policies. This resolves the immediate composition blocker without claiming VC confirmation.

After the user instructed "So lets start. Chop chop!", the first independent local interface slice was implemented (DEC-022). This does not resolve Q-14 or approve the superseded registration schema.

## Status vocabulary

- **Confirmed direction:** explicitly chosen/authorised by the user; does not approve an unseen detailed schema or later phase.
- **Proposed:** prepared for discussion; no implementation approval implied.
- **Open:** awaiting the relevant policy or operational decision.
- **Superseded:** replaced by a later dated decision; retain original context.

## Decisions

### DEC-048 — Registrar scrutiny and VC allocation handoff (22 September 2026)

For the request-to-panel handoff, the POC submits; the Registrar/Reviewer returns an invalid request or accepts a valid request for VC action; only the VC generates, views and verifies the proposed panel. The POC and Registrar cannot see proposed identities. Admin retains the global override. This supersedes the allocation-authority portion of DEC-046 and conflicting older workflow descriptions. It does not change the separately agreed later document and replacement responsibilities.

### DEC-047 — Institution directory is independent of request activity (15 September 2026)

The institution directory is standalone. `is_requesting_college` is removed because it incorrectly mixes an institution's identity with whether it currently has a panel request. An active institution whose type is “college” may be selected for a request; the request's own state records whether it is draft, under review, returned, or has an offered panel. Existing institution data remains intact.

### DEC-046 — Request review and offered-panel authority (15 September 2026)

The POC prepares and submits a request but cannot generate its panel. A reviewer checks the request, may return it with a recorded reason, and generates the offered panel through the rule engine. The offered panel is visible after generation but its names are view-only. The POC records management's final choices only from that panel; the final panel remains a separate record and is locked by the reviewer. No person can freely edit or swap engine-generated names.

### DEC-045 — Letter workflow schema and implementation approved (15 September 2026)

The user approved the letter schema/preview package and authorised implementation. The delivered University-only workflow prepares an offer, locked-final-selection, confirmed-replacement or confirmed-cancellation document from its fixed source facts; a processor submits it and a reviewer returns or approves it. Approval freezes private PDF bytes and a checksum, while downloads are audit events only. The supplied logo and approved Vice-Chancellor header are used. E-signature, automated delivery and correction/revision screens remain later scope. See document 24 for the delivered schema boundary and verification.

### DEC-044 — Document delivery and signing scope

In response to the letters workshop, the user confirms staff enter the reference number initially; reviewer remains the authority; generated documents should look almost the same as the two supplied PDFs. Deliver documents now and defer e-signing to stretch goals. This explicitly changes the SRS digital/e-sign delivery requirement for the initial release, without representing unsigned documents as signed or downloads as external dispatch. Preserve approved composition and sample layout separately; no scanned signature reuse. Concrete schema mapping and previews remain the next review step.

### DEC-043 — Panel-change policy approved (14 September 2026)

User approved document 20. Processors record reason/verifier and prepare replacement or cancellation; reviewers return or confirm. An unlocked offer never changes utilisation. On confirmed locked replacement, reverse the removed active contribution in its original nomination year and add the incoming contribution in the confirmation-lock year. Determine last nomination from surviving contributions. Use the new replacement allocation date for eligibility. Cancellation is initially limited to confirmed evidence that selection work has not occurred. Preserve every original decision and accounting event.

### DEC-042 — Fresh start for utilisation tracking (14 September 2026)

User explicitly approved a fresh start because complete historical nomination data cannot be supplied. From an agreed operational go-live date, every expert starts with zero system-tracked utilisation; initial ties use permanent sequence. Subsequent final locks supply the common annual utilisation and last-nomination ordering within this tracking period. Describe an empty history as “no nomination recorded since go-live”, never “never nominated”. Preserve the two sample PDFs as historical references without selectively counting their members. All other approved eligibility, own-college, representation and allocation rules remain applicable.

This supersedes the requirement for complete pre-system history as an operational allocation prerequisite. Exact go-live date remains pending before launch. Implementation must explicitly record the tracking boundary and integrate locked utilisation entries; the existing history provider has not been changed by this decision record. Existing demonstration records do not establish operational history. Detailed schema changes retain the agreed review gate.

| ID | Date | Status | Decision | Evidence / consequence |
|---|---|---|---|---|
| DEC-001 | 2026-09-08 | Confirmed direction | Use SRS v1.0 as the project requirements baseline, distinguishing confirmed meaning from ambiguity. | User supplied SRS and requested deep understanding before code. |
| DEC-002 | 2026-09-08 | Confirmed direction | Clarify nomination-policy ambiguities when the relevant phase is reached. | User explicitly deferred clarification until dependent coding work. No silent policy assumptions. |
| DEC-003 | 2026-09-08 | Confirmed direction | Portable deployment to university infrastructure or approved cloud. | User selected portable deployment during roadmap discussion. Actual host remains open. |
| DEC-004 | 2026-09-08 | Confirmed direction | First working application/scrutiny demo after two weeks; weekly demonstrations thereafter. | User selected the two-week working slice; demonstration baseline subsequently accepted in DEC-009. |
| DEC-005 | 2026-09-08 | Confirmed direction | English initially; translation-ready interface and Unicode/Hindi-capable data. | User selected English/Hindi-ready option. Bilingual release is not currently scheduled. |
| DEC-006 | 2026-09-08 | Confirmed direction | Discuss and approve each concrete phase before coding it. | User selected phase approval and included this condition in the implementation request. |
| DEC-007 | 2026-09-08 | Confirmed direction | First operational release is a controlled pilot. | User selected pilot before broader rollout. Cohort and readiness sign-off remain open. |
| DEC-008 | 2026-09-08 | Confirmed direction | Django 5.2 LTS/Python 3.13, PostgreSQL 17, templates/HTMX/Bootstrap; supporting stack and ten-week roadmap as documented. | User requested implementation of the supplied roadmap. Exact patch locks and detailed implementation plans require phase work. |
| DEC-009 | 2026-09-08 | Confirmed direction | Adopt the Phase 0 foundation proposal, first-demo baseline and module/workspace boundaries as the basis for Phase 1 discussion. | User replied "Approved" to the explicit question approving the foundation as the baseline for the Phase 1 account-and-college schema discussion. No Phase 1 schema or coding approval implied. |
| DEC-010 | 2026-09-08 | Superseded | Previously proposed multiple named college staff accounts. | Removed by DEC-014; individual attribution remains necessary for University users. |
| DEC-011 | 2026-09-08 | Superseded | Previously confirmed verified college access requests. | College request/activation process removed by DEC-014. University account provisioning must be settled in the revised phase plan. |
| DEC-012 | 2026-09-08 | Superseded | Previously confirmed one active college assignment per college user. | No college users or memberships under DEC-014. |
| DEC-013 | 2026-09-08 | Superseded | Previous consolidated Phase 1 registration/schema proposal. | Never approved for coding; superseded by University-only scope. |
| DEC-014 | 2026-09-09 | Confirmed direction | University-only access. POC enters Hindi information supplied by colleges; no college portal. Allocation is the main focus. | User reported VC discussion and explicitly confirmed that the POC enters the Hindi information. Overrides English-first intake and college-portal plans. |
| DEC-015 | 2026-09-09 | Confirmed direction | Include subject-expert appointments. SRS governs rules over the sample letters; retain samples primarily as letter-format references. | User answers 1, 2, 6–10, 12 and 14. Mapping SRS composition to subject-expert appointments remains explicitly open. |
| DEC-016 | 2026-09-09 | Confirmed direction | Select the six-name offered panel from the full approved candidate pool; management makes final choices; POC records them. | User answers 3, 5 and 11. Offered panel and final membership are distinct. |
| DEC-017 | 2026-09-09 | Confirmed direction | Only locked final members increase utilisation. Record replacement reasons; engine recommends replacements; remove the replaced final member's count contribution. | User answers 4 and 13. Explicitly supersedes approval-of-offered-panel counting; retain history and resolve detailed year/role accounting at its gate. |
| DEC-018 | 2026-09-09 | Confirmed direction; subject-expert composition provisional | Keep appointment-type rules modular. Initially apply one Principal + five Professors, one separate VC nominee and SRS category supplements to subject-expert requests too, pending VC confirmation. | User explicitly asked to keep the same composition for now but changeable later. Use independent versioned policies and historical snapshots; no VC confirmation or general coding approval inferred. |
| DEC-019 | 2026-09-09 | Confirmed direction | Ready to move toward coding after a full SRS reread; ask about doubts and do not introduce silent or soft assumptions. | Reread all 30 numbered sections, expert/application fields, validations, reports and the page-18 visual summary. Cross-checked against DEC-014–018. Unanswered rules require clarification before dependent code; do not reinstate superseded college access or offered-panel counting. |
| DEC-020 | 2026-09-09 | Partly superseded by DEC-027 | Previously chose separate utilisation counts; final-lock date determines the July–June nomination year. | DEC-027 replaces separate counts with a common count for now. Final-lock-date attribution remains confirmed; cross-year replacement treatment remains open. |
| DEC-021 | 2026-09-09 | Requested direction; lifecycle proposed | Add a pending reservation stage for offered experts, distinct from final utilisation. | User compared pending offers to a booked-but-pending seat and requested an opinion. Acquisition, conflict scope and release/expiry remain unapproved; record proposals without silently implementing them. |
| DEC-022 | 2026-09-09 | Implemented independent foundation slice | Start coding the revised University-office interface and project foundation, leaving unresolved data/access/nomination rules out of executable actions. | User repeatedly instructed to start. Implemented Django/Python 3.13 local preview, Hindi intake preview/edit, immutable independent composition policies, local interface assets and verification. No domain schema, authentication, persisted requests, allocation, reservation or final-lock actions. |
| DEC-027 | 2026-09-09 | Confirmed direction for now | One common utilisation count per expert across appointment types and nomination roles. | User answered the count-scope question: "I think keep a common count for now." Supersedes the separate-count part of DEC-020; final-lock-only counting, July–June year and final-lock-date attribution remain. Retain role/type history for any later approved change. |
| DEC-029 | 2026-09-12 | Approved and implemented | Implement document 11 section 10: University staff accounts/roles, institution and subject directories, shared Hindi request drafts, revision conflict handling and audit. | User replied LGTM to the explicit first-slice implementation approval request. No expert, allocation or final-lock schema approval inferred. See document 12 for implementation and verification. |

## Approval ledger

- **DEC-041 (approved and implemented):** user approved the final-selection/lock package in document 18. Provisional final committee: one Principal, four Professors, one distinct VC nominee, plus selected category members as needed. The VC is outside final SC/ST/OBC coverage. POC records choices/references; reviewer returns/locks; locked members create common utilisation contributions. Document 19 records the delivered boundary. No post-lock replacement/cancellation, letters, overrides or historical import approval is implied.

- **DEC-038 (confirmed simplification):** one applicable approved pool for each role/appointment type/subject. Staff enter requirements; engine resolves the pool automatically. No competing-list chooser or union workflow. List updates preserve earlier versions.
- **DEC-039 (confirmed source of eligibility):** VC eligibility is governed directly by SRS 4.1; no new approval of the rule itself is needed. Category eligibility likewise follows SRS. This closes the redundant A-08 question while retaining operational nominee approval as a later action.
- **DEC-040 (coding authorised):** following LGTM on the explicit SRS/user-decision rule mapping and answers through DEC-039, user requests proceeding with coding. Implement document 16's recommendation slice: ranking, eligibility, composition, explanations, verifier records and immutable evaluations. Real history remains unavailable beyond samples; no invented zero counts. Formal offer issue, final selection/lock, replacement accounting and official letters remain later scopes. Document 17 records actual delivered coverage.

- **DEC-037 (confirmed availability/status clarification):** user instructs recording whoever verifies the decisions; retired/transferred means permanently inactive, and staff need not upload transfer documents. Supersedes document 16's contrary retirement/transfer proposal. Record verifier attribution without creating a separate verification role, keep audit/history, and exclude permanently inactive experts from future allocations. No automatic reactivation by changing institution, or historical count reversal, is implied. Other status/unknown-check details remain open.

- **DEC-036 (confirmed historical coverage):** user confirms the two final-selection PDFs are examples from a larger set. They are partial evidence, not the complete current-year/lifetime dataset. Q-17 remains open for collection, coverage and reconciliation of the remaining records. No opening-count change, zero-history assumption or bulk import authorised.

- **DEC-035 (confirmed historical-source clarification):** user states that the two additional PDFs, `panel for subject expert and vc nominee.pdf` and `principal or Hod.pdf`, were the finally selected panels. Treat them as historical final-selection evidence as well as letter-format references. This corrects the assistant's offered-panel interpretation. Coverage, historical dates, identity matching and later changes remain to be established before approved import; no utilisation mutation or complete-history assertion follows automatically.

### 13 September 2026 — current phase update

- **DEC-032 (confirmed clarification):** one expert may hold Principal post and verified Professor rank together. Ordinary university maintenance staff review inline record checks; no separate readiness-inspector role or screen.
- **DEC-033 (approved and implemented):** user approved the complete experts/approved-pools workshop after those clarifications. Document 15 records the delivered boundary; document 13's original proposal wording is historical. No allocation, final-lock, real bulk-import or production approval implied.
- **DEC-034 (confirmed allocation answers):** for equal annual counts use the latest locked nomination across all years; verified never-nominated experts precede previously nominated experts, while missing history stays unknown. Eligibility uses allocation date only, rejecting the proposed dual allocation/selection-date check. Choose VC first, then generate the six-name panel without duplicating that person. These answers do not independently settle ranking-year selection, later issue/lock revalidation, Principal/Professor ordering or decision authority.
- Document 16 starts the allocation workshop. No engine code or schema is approved by these individual answers. Older ledger rows describing all later phases as future gates are superseded only for the expert/pool slice.

Latest clarification DEC-026 supersedes the pending-offer ranking interpretation of DEC-023 and the blocking interpretation of the DEC-021 seat analogy. Pending experts remain eligible under unchanged SRS ranking. DEC-024 own-college exclusion and DEC-025 deferred homepage wording remain in force. These are requirements records; offer lifecycle details still require review.

| Scope | Status | Approved implementation boundary |
|---|---|---|
| Delivery roadmap and preparation of review material | Authorised | Prepare Phase 0 review pack and discuss the foundation |
| Phase 0 detailed foundation | Approved historically; partially superseded | Architecture retained; intake, scope and utilisation revised in DEC-014–017 |
| Previous Phase 1 account/college schema package | Superseded, never approved for coding | Do not implement document 08; prepare University-only replacement |
| University foundation first-slice package | Approved and implemented | Document 11 section 10; document 12 records implementation and verification. Future expert/allocation schemas remain at their gates. |
| Independent interface foundation | Implemented on instruction to start | Local non-persistent preview only; 23 tests and desktop/mobile browser walkthrough passed; next domain schema still requires review |
| Phases 2–8 | Future gates | No detailed phase implementation approvals recorded |

## Change history

### 2026-09-12 — Expert/list workshop started

- DEC-031 (confirmed): one permanent sequence per expert; multiple separately approved subject/list memberships; existing directory-maintenance staff record approval references and make lists available.
- Reread the original SRS text and visually reviewed expert fields and the final flowchart. Prepared document 13 with source-to-record distinctions, field proposals, examples, constraints and a consolidated next-phase implementation package.
- Sequence generation, institution/rank/date representation and the remaining package defaults are explicit proposals pending phase approval. No expert/pool migrations or application changes made in this workshop.

### 2026-09-12 — College affiliation details removed

- DEC-030 (user-authorised schema change): remove college affiliation details as unnecessary. Remove the field from the institution model, directory form and intake preview; omit it from collection guidance.
- The local database contained two institutions, both with empty affiliation details, before migration. Preserve existing audit history and the label used to display any historical affiliation-detail events.

### 2026-09-15 — Controlled VBSPU affiliation status

- DEC-048 (user-authorised schema change): add the controlled `is_affiliated_to_vbspu` Yes/No field to institutions. This replaces the earlier free-text affiliation-details field; it does not restore it.
- Mark every existing institution as Yes during the migration, as explicitly directed by the user. New institutions require a Yes/No choice.
- Use the field in the VC internal-college eligibility check alongside the existing Government/Aided and college-type requirements.

### 2026-09-15 — Academic designation and optional administrative post

- DEC-049 (user-authorised expert-entry change): collect an expert's academic designation and subject(s) first. A current administrative post is optional and recorded separately from academic designation.
- If staff select Yes for a current administrative post, collect its type and optional end date. A blank end date explicitly means it is not known.
- Preserve institution/employment history. Existing appointment records are migrated without duplication: prior Professor, Assistant Professor and Other values are retained as academic designations and treated as no administrative post; prior Principal values remain Principal posts.

### 2026-09-15 — Expert directory is the allocation source

- DEC-050 (user-authorised allocation change): evaluate active experts directly from the expert directory. Do not require a manually created EC candidate-list membership before an expert can be considered.
- EC approvals and candidate-list records remain available as supporting maintenance/audit records. They no longer gate ordinary panel allocation.
- Continue to apply SRS role, subject, category, own-college, availability/conflict and final-lock utilisation rules to every directory candidate.
- Expert institution links and own-college exclusion remain requirements. No expert schema or allocation policy changed.

### 2026-09-12 — Approved persistent foundation implemented

- DEC-029 records the user's LGTM approval of the consolidated first-slice package.
- Added University-only accounts/role grants, directories, saved Hindi drafts, transactional audit and stale-edit rejection. No college portal, allocation or final-lock actions introduced.
- Created an isolated PostgreSQL 17.11 database and applied migrations. Replaced the verified old local preview server with the foundation server; retained original homepage content.
- Added PostgreSQL permission/integrity/concurrency tests and desktop/mobile browser verification. Detailed results and local operation are in document 12.

### 2026-09-09 — University foundation workshop

- DEC-028 (confirmed): administrators create named staff accounts; authorised processing staff share all college requests; each expert has exactly one current college.
- Prepared [the revised University foundation schema workshop](11-university-foundation-schema-proposal.md), with relationships, first-slice field proposals, permissions, examples, migration/verification approach and a revised allocation-focused delivery sequence.
- Included a consolidated first-slice proposal after the user's answers. Remaining proposed implementation choices await package approval; no models, migrations or application code changed.

### 2026-09-09 — Common utilisation count

- DEC-027 replaces the earlier separate-count choice with one common count per expert for now, across appointment types and nomination roles.
- Updated current requirements, Q-11 and the counting summary; added a worked regression example combining subject-expert and VC-nominee selections.
- Preserve the original separate-count decision as superseded history. No schema or application code changed.

### 2026-09-09 — Pending offers do not change SRS ranking

- DEC-026 (confirmed clarification): otherwise eligible experts whose earlier offers are not finalised may be considered for another panel. Retain SRS utilisation, oldest nomination date and fixed sequence ordering; only locked final membership counts.
- Withdraw the assistant-proposed unreserved-first tier and shortage-only fallback. No extra pending-load score, quota or ranking priority is approved. This clarifies/supersedes DEC-023's earlier interpretation and any reservation-block interpretation of DEC-021; original discussion remains below for history.
- Updated current requirements and Q-14; retained only outstanding-offer lifecycle, withdrawal/replacement, actual date conflicts and concurrency details for later review.
- Own-college exclusion remains mandatory. No application code or homepage content changed.

### 2026-09-09 — Pending workload, own-college exclusion and deferred copy

- DEC-023 (confirmed direction): prefer avoiding experts with outstanding offers; allow reuse when eligible subject pools are scarce; distribute workload fairly. Updated Q-14 to distinguish this direction from still-open algorithm and lifecycle details.
- DEC-024 (confirmed rule): experts cannot serve on their own college's panel; scarcity and overrides cannot waive this. Applies to all nominee roles and replacements.
- DEC-025 (deferred task): make homepage wording more practical and less slogan-heavy later; user explicitly instructed no homepage work now.
- Updated requirements and question register only. No homepage, application code or allocation behaviour changed.

### 2026-09-09 — First working foundation

- Implemented and ran a local Django 5.2.17 / Python 3.13 preview, with dependency lock, PostgreSQL configuration and prepared Docker setup.
- Added Hindi workspace, request preview/edit and appointment-type composition screens; kept subject-expert composition visibly provisional and reservations inactive.
- Added 23 automated checks and desktop/mobile browser verification. Browser testing found and resolved form-provenance and back-to-edit state-loss issues.
- Docker engine remained unavailable; native Python 3.13 verification succeeded. Compose configuration validated; no database schema or integration success claimed.

### 2026-09-09 — Reservation question deferred

- User explicitly asked to retain the reservation question in the open list; Q-14 now identifies acquisition, scope, expiry/release and replacement holds as undecided.
- Added a quick status summary of the original five broad SRS-question groups, with reservations as a sixth, later-added topic. Resolved answers remain resolved.
- No reservation defaults or dependent code authorised by this deferral.

### 2026-09-09 — Utilisation basis and pending-reservation discussion

- Confirmed separate counts and final-lock-date annual attribution.
- Proposed reservation-to-final-lock lifecycle, release of unselected experts and transactional conflict handling.
- Kept reservation scope, start and expiry policies explicit for discussion. No allocation code or reservation schema created.

### 2026-09-09 — Pre-coding SRS reread

- Reread the original PDF in full: all 30 numbered sections on pages 1–16 and the visual summary on page 18; page 17 is blank.
- Cross-checked prescribed fields, availability reasons, conflicts, category conditions, ranking keys, annual history, overrides, all 15 reports, audit fields, access rules and finalisation blockers against current requirements.
- Retained confirmed user changes: University POC Hindi intake; full approved candidate pool; six-name offers; final-lock-only counts and reversal on replacement; provisional independently versioned subject-expert composition.
- Remaining accounting/scheduling questions include shared versus role-specific counts, annual attribution and pending offers. No answers inferred from the reread. No application code created during this review.

### 2026-09-09 — Provisional composition and modular rules

- Recorded the user's permission to proceed with the same SRS composition for subject-expert appointments pending VC confirmation.
- Specified separate versioned appointment-type policies, shared fairness ranking and traceable panel rule snapshots.
- Required new versions for policy changes and explicit regeneration for affected drafts; no silent edits to issued panels or locked histories.
- Added regression scenarios for policy isolation, provisional status and historical preservation. No application code or migrations created.

### 2026-09-09 — VC discussion and sample clarifications

- Recorded University POC Hindi intake and removed college portal/account assumptions.
- Reviewed all four pages of the two sample PDFs and recorded all 14 user answers in current requirements.
- Added subject-expert scope; retained SRS authority over differing sample rules.
- Distinguished offered panels, recorded final choices and locked final membership; revised utilisation and replacement effects.
- Marked conflicting prior documents as historical/superseded and updated the project entry point.
- Kept lecturer composition and detailed final-lock/year/role accounting explicitly unresolved. No application code or schema created.

### 2026-09-08 — Consolidated Phase 1 proposal

- Advanced the workshop into one complete approval package after the user asked to move forward.
- Kept unanswered account-request scope, email login, multiple university roles and related lifecycle choices explicitly proposed.
- Included schema, constraints, verification/activation, permissions, audit, migration order and tests.
- Inspected runtime availability: Docker/Compose installed; engine unavailable in this session; system Python 3.11. Proposed Python 3.13 container execution remains unchanged.
- Adjusted Phase 1 estimate to 4–5 working days for the user-selected registration workflow. No application code created.

### 2026-09-08 — Phase 0 approval and Phase 1 workshop

- Recorded the user's foundation approval with its explicit discussion-only scope.
- Updated project status and the first-demo baseline status.
- Prepared a conceptual Phase 1 schema workshop and asked the first three account-policy questions.
- Subsequently confirmed multiple named college accounts, verified user-requested access, and one active college per person (DEC-010–012). Detailed schema and authentication questions remain open.
- No application code or migrations created.

### 2026-09-08 — Initial foundation review pack

- Created project entry point, foundation architecture/workspaces proposal, and phased delivery roadmap.
- Created a first-demo walkthrough with 13 proposed acceptance scenarios.
- Mapped all 30 numbered SRS sections and the final visual summary to delivery and verification; listed all 15 reports.
- Recorded 22 open decisions, seven external dependencies, and the confirmed user preferences.
- Created no application code, database schema, migrations, account records, deployment, or external communications.

## Recording later decisions

For each material decision record: date, question ID, approved behaviour, example/edge cases, alternatives considered, decision source, affected requirements/schema/tests, and migration or operational effects. Quote or accurately summarise the user's approval scope; do not infer broad approval from approval of one screen or one rule.

When requirements change, retain the previous decision as superseded and update the affected phase plan before implementing a material scope change.
