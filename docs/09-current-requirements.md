# Current requirements — University intake and allocation

Updated 12 September 2026. **Current requirements baseline.** The separate [foundation first-slice package](11-university-foundation-schema-proposal.md) was approved and implemented (DEC-029); that does not approve later schemas or unresolved policies. This document records the user's VC-discussion changes and answers to the 14 sample-review questions. It takes precedence over conflicting earlier project proposals.

Pre-coding review completed on 9 September 2026: original SRS reread in full, including its visual summary, and checked against this baseline. The user requires doubts to be raised before dependent action: no unapproved business-rule defaults, including provisional rules beyond those explicitly authorised in DEC-018. General readiness to code does not silently settle outstanding schema or policy decisions.

## 1. Authority and scope

### Registrar scrutiny and VC allocation handoff (22 September 2026)

The POC submits the request. The Registrar/Reviewer then only scrutinises it: they return an invalid request or accept a valid request for VC action. The VC generates, views and verifies the proposed panel only after that acceptance, then completes the VC nominee and final-selection decisions. The POC and Registrar cannot view proposed names. Admin retains every role's authority. This supersedes earlier statements that allow the Registrar to generate or verify proposed panels.

### Fresh-start utilisation policy (DEC-042, approved 14 September 2026)

Complete pre-system nomination history is no longer required to proceed. At the agreed operational go-live date, initialise every expert with zero system-tracked utilisation. Initial ties use permanent sequence; subsequent final locks drive common annual counts and last-nomination ordering within the tracked period. Use “no nomination recorded since go-live” instead of claiming “never nominated”. The two sample PDFs remain historical references and do not selectively contribute counts. All other eligibility, own-college and representation rules remain in force.

The exact start date must be fixed before operational launch. This policy supersedes earlier complete-opening-history blockers in the plans and handovers. The history provider applies it only after a controlled baseline activation, preserving demonstration/operational separation.

### Panel changes (DEC-043, approved 14 September 2026)

Processors prepare replacements/cancellations and reviewers confirm them. Before final lock, a fresh recommendation is count-neutral. After lock, reverse the removed expert's active contribution in its original year and create the replacement's contribution in the confirmation year; use surviving contributions for last-nomination order. Replacement allocation uses its new allocation date. Cancellation is limited to selections confirmed not to have occurred. See [implementation handover](21-panel-changes-implementation.md) for the delivered boundary.

### Final selection and lock (DEC-041)

The final selection is provisionally one Principal plus four Professors, with a separate VC nominee and required category members. The POC records management and VC decision references; reviewer locks. Lock is blocked until SC/ST and OBC representation is complete among selected main/category members; VC does not satisfy that category test. Only lock changes utilisation. The detail is implemented in [document 19](19-final-selection-lock-implementation.md); future policy changes require a new version and preserve prior locks.

### Allocation implementation baseline (DEC-038–040)

User approved the explicit SRS-to-allocation rule mapping and authorised coding after simplifying source selection. Use one applicable approved pool per role/type/subject, with automatic resolution and retained versions. No competing-list chooser or union. Apply VC eligibility directly from SRS 4.1 and category rules from SRS 6; no fresh confirmation of established rules is required. Approved membership scope establishes applicability; do not add an unapproved personal-subject condition.

The recommendation slice uses current July–June utilisation at allocation (SRS 10), lifetime date ties, VC then Principal then Professors, followed by any category supplements. Report shortages without relaxing eligibility or silently changing recommended VC choices. Real history is not complete; the live history input remains unknown until reconciled records/ledger integration. [Document 17](17-allocation-implementation.md) distinguishes executable demonstrations and record checks from future operational issue/lock.

### Availability/status clarification (DEC-037)

- Record who verified each availability/conflict decision. Preserve the entering user's audit identity separately when someone else performed verification; this does not create a separate verifier role or confer approval powers.
- Retired and transferred experts are permanently inactive for future allocations across roles. This supersedes the workshop proposal to reassess eligibility automatically after retirement/transfer. Changing a recorded institution must not automatically reactivate a transferred expert.
- A transfer-document upload is not mandatory. Retain the status decision, reason and verifier in history without inventing a documentary prerequisite.
- Preserve historical nominations and utilisation; inactivity alone does not cancel an existing final selection or reduce its count. Existing-panel replacement remains governed by its separately approved workflow.

### Allocation workshop update — 13 September 2026

The expert/pool workshop is approved and implemented within document 15's boundary (DEC-032/033), including coexisting Principal post/Professor rank and inline checks maintained by existing staff.

DEC-034 confirms: use lifetime latest locked nomination for date ties, placing verified never-nominated experts first when annual counts tie; unknown history is not zero. Check institution/rank/list eligibility on allocation date only. Process VC first, then the six-name panel without duplicating the VC person. These supersede older open questions on those exact points. Other workflow/authority details remain in [the allocation workshop](16-allocation-engine-workshop.md); no whole-engine implementation approval is implied.

- The original SRS governs business rules where the sample letters differ.
- Explicit user clarifications govern the changes recorded here, including intake, appointment scope and utilisation accounting. In particular, issuing/approving an offered panel is no longer the event that increases utilisation.
- Support both Principal/HoD and subject-expert/lecturer appointments. The user authorises the same SRS composition provisionally for subject-expert appointments pending VC confirmation. Keep appointment-type policies separate so this can change independently; do not adopt the sample's two-VC/five-expert arrangement.
- Only University personnel use the application. Colleges supply information outside the system; the University POC enters requests on their behalf.
- POC entry must support Hindi/Unicode text using the operator's Hindi input method, with Mangal or a compatible Devanagari display font. Preserve Hindi in records and letters; do not require duplicate English names or infer names from scans.
- No college accounts, public college registration, college memberships or college portal. College directory records remain necessary to identify the requesting institution.
- Allocation is the primary product focus. The Django/PostgreSQL architecture remains suitable; the detailed account/schema proposal in document 08 is superseded.
- **Own-college exclusion is mandatory:** an expert may never be nominated to a panel for their own college. Apply this to all appointment types and nomination roles, including VC/category nominees and replacements. A small pool or manual override cannot waive it. Compare verified institution identities, not Hindi/English name spellings; detailed affiliation modelling belongs to the schema review.

### College directory simplification (DEC-030)

The user removed free-text college affiliation details from the schema. Do not collect affiliation reference/details in the college directory, request preview or college data-collection sheet. Record the controlled **Affiliated to VBSPU: Yes/No** field instead. College collection columns are: name, official code if available, district, address, management type, affiliated to VBSPU and active/inactive status. Expert-to-college identity/history and mandatory own-college exclusion remain unchanged.

### Foundation access and affiliation decisions (DEC-028)

- Administrators create named University staff accounts; no staff self-registration.
- Authorised processing staff share access to view/edit all college requests. This does not confer offer approval or final-lock authority.
- Each expert has exactly one current college. Preserve previous affiliations as history; multiple current college affiliations are not permitted. External-university affiliation representation and the date used for eligibility checks require the expert schema review.

### Expert/list workshop decisions (DEC-031)

- One permanent sequence number per expert, reused across approved lists. Generation/import method is proposed separately in the next-phase package.
- One expert may have multiple approved subjects/list memberships, with approval covering each membership.
- Existing directory-maintenance staff may record approval references and make candidate lists available. This records an existing university approval; it does not grant EC approval.

## 2. Answers to the 14 sample questions

**Coverage clarification (DEC-036):** the two supplied final-selection PDFs are examples from a larger set, as confirmed by the user. They do not establish complete current-year or lifetime utilisation. The remaining historical records and agreed coverage must be reconciled before authoritative opening counts/date ties; missing experts cannot be classified as never nominated from these examples alone.

**Historical-source clarification (DEC-035):** the user confirms that `panel for subject expert and vc nominee.pdf` and `principal or Hod.pdf` contain finally selected members. They are historical final-selection evidence, not merely offered-panel examples. They still serve as format references without overriding the SRS's future composition rules. Before opening-history import, establish coverage, identities, historical finalisation dates and subsequent changes. This confirmation alone does not establish complete lifetime/current-year history or authorise database counts to be changed.

| Question | Confirmed answer | Design consequence |
|---|---|---|
| 1. Appointment scope | Subject-expert appointments are definitely in scope alongside Principal/HoD. | Separate appointment-type policies; initially use the shared SRS composition, provisionally for subject-expert requests (DEC-018). |
| 2. Governing source | SRS governs all rules over the samples. | Samples are format references; they cannot silently override counts, rank or eligibility rules. |
| 3. Allocation output | System provides a six-name panel; management committee makes the final selection. | Model offered panel and final selected membership separately; do not make the engine choose management's final subset. |
| 4. Utilisation trigger | Count only those selected for the final committee; answer 13 further specifies final selection must be locked. | Draft, offered panel and unlocked final selection do not increase utilisation. |
| 5. Candidate source | Entire approved candidate list, filtered/selected by SRS rules. | Generate the offered panel from the broader eligible pool; not a fixed six-person pool or cycling whole predefined panels. |
| 6. Principal/HoD composition | Follow SRS. | Six-name expert panel is one Principal plus five Professors, with the distinct VC nominee and category provisions as specified in the SRS. |
| 7. Lecturer composition | Follow SRS; subsequently authorised to use the same composition provisionally pending VC confirmation. | One Principal + five Professors, one separate VC nominee and SRS category supplements initially; independent versioned subject-expert policy allows later revision. |
| 8. Eligibility | Follow SRS. | Use SRS rank/institution/availability/conflict conditions; do not add different sample-only eligibility rules without confirmation. |
| 9. Category boundary | Follow SRS. | Apply the detailed six-member-panel check for SC/ST and OBC; do not substitute the sample's broader committee boundary. Final-selection validation still needs an explicit review. |
| 10. Lecturer categories | Follow SRS. | No exemption inferred from the lecturer sample's missing clause; retain SRS representation requirements. |
| 11. Final choices | POC will record the finally selected candidates. | Provide internal capture of management's selection; no college-facing selection UI. |
| 12. Supplemental categories | Follow SRS. | Add an approved SC/ST or OBC expert when required; SRS permits Assistant Professor for this supplemental role. |
| 13. Replacement | Record reason and suggest next eligible expert through engine. After final selection, removed expert's utilisation is reduced; only locked final membership counts. | Support offered-panel replacement and post-final replacement, preserve prior records, and adjust utilisation only on the relevant locked final change. |
| 14. Letter format | Build around supplied samples; only minor necessary changes. | Preserve recognisable Hindi letter structure, using SRS-governed composition and approved wording changes. |

## 3. Proposed workflow reflecting the confirmed decisions

University POC enters college request in Hindi → internal eligibility/scrutiny → engine recommends from the approved candidate pool → offered panel reviewed/issued → management selects outside the system → POC records final choices → authorised final lock → utilisation updated → traceable replacements where necessary.

The exact actors allowed to review, issue and lock remain subject to the later authority matrix. A POC recording choices does not automatically have authority to lock them. This workflow is a working interpretation to guide the revised schema discussion, not an implementation approval.

### Count behaviour now established

| Event | Utilisation effect |
|---|---|
| Calculate recommendations | None |
| Save, approve or issue an offered six-name panel | None |
| Record final choices but leave unlocked | None |
| Lock final choices | Count each final member according to the approved role/year accounting policy |
| Replace an offered-panel expert before final lock | None; retain original, reason and recommendation evidence |
| Suggest a replacement after final lock | Suggestion alone must not alter the final membership or counts |
| Authorise and lock a change to final membership | Remove the replaced member's contribution and add the replacement's contribution consistently; retain both records and the reason |

The last two rows express the implementation consequence of counting only locked final membership: the old locked version remains authoritative until an authorised replacement is locked. Confirm the replacement authorisation/unlock mechanics in the schema workshop.

Recommended implementation direction: use auditable nomination events/adjustments and final membership versions, with totals derived or transactionally maintained from them. A decrement must not erase the original selection or audit record. Do not implement freely editable counters. This is a design proposal, not a final ledger schema.

The July–June nomination year remains governed by the SRS, with the **final-lock date** determining the nomination year. The user now chooses **one common utilisation count per expert for now**, shared across appointment types and nomination roles (DEC-027). This supersedes the earlier separate-count decision. Only locked final selections contribute; pending offers do not. Preserve appointment type and role in nomination history so a later approved accounting change can be designed without losing those facts. Treatment of replacements across year boundaries remains unresolved.

### Pending offers — retain SRS ranking

**Clarified by the user (DEC-026):** an otherwise eligible expert whose earlier offered panel is not yet finalised may be considered when the engine allocates another panel. The SRS distribution rules remain authoritative: applicable utilisation count, oldest last-nomination date, then fixed sequence. Pending offers do not introduce a second ranking rule.

- Only locked final membership contributes to official utilisation. Pending offers are not added to that count.
- Pending status alone does not exclude or demote an expert. Do not introduce an unreserved-first tier, pending-load score, quota or shortage-only reuse threshold. The earlier two-tier mechanism was an assistant proposal and is withdrawn.
- Apply all hard eligibility checks, including own-college exclusion and actual availability/conflicts. An outstanding offer is not itself proof of unavailability.
- Keep pending offers distinguishable from final membership for visibility and history. An expert may appear in more than one pending offer while remaining eligible under the governing rules.
- Distribution follows the existing SRS order; do not promise that it prevents repeated pending offers when final counts have not changed.

Offer lifecycle details remain for the schema/workflow review: the event that establishes an outstanding offer, withdrawal/replacement handling, date conflicts and concurrent revalidation. These details must not silently reintroduce reservation blocking, expiry rules or a different ranking order. Q-14 now retains those workflow details rather than reopening pending eligibility or ranking.

## 4. Remaining questions — do not reopen answered policy

### Provisional composition and modular policy design

The user has authorised using the same composition for now: **one Principal + five Professors, a separate single VC nominee, and category supplements as required by the SRS**. For subject-expert appointments this is explicitly provisional, pending VC confirmation. This is no longer a question blocking design progress; it is not represented as confirmed University policy.

Design requirements for the revised schema/engine plan:

- Give Principal, HoD and subject-expert appointment types independently identifiable, versioned policies, initially with the same composition values. Do not use one mutable shared object whose edit changes every appointment type.
- Keep composition, role eligibility, representation checks and letter-template selection outside the common fairness-ranking algorithm. Use validated policy data for counts and approved rule implementations for behaviour; no unrestricted rule scripting or general-purpose policy editor is required.
- The shared ranking engine continues to use the approved utilisation, last-nomination and sequence rules. A change in lecturer composition alone must not change fairness accounting or the Principal/HoD policies.
- Record the policy version and relevant rule snapshot on every generated panel. The draft, offered panel, final-selection validation and replacements must have a traceable rule context; the exact snapshot schema belongs to the approved schema workshop.
- Revise policy by creating a new version. New allocations use the authorised effective version; earlier issued panels, locked final selections, letters and utilisation history are not silently rewritten.
- For in-progress drafts, applying a revised policy must be an explicit regeneration with fresh validation and audit, not an invisible change on page reload. Migration of already issued cases requires a separately authorised correction workflow.
- Mark the subject-expert policy as provisional in internal policy/panel review context. VC confirmation can confirm that version or lead to a new one; do not invent an expiry date or imply official confirmation.

This modularity is authorised design direction. The detailed schema, permissions for publishing rule changes and phase implementation still follow their existing approval gates.

### Later schema/engine gates

- Final-selection size and role constraints: which offered members may management select, and what final-composition/category validations must hold at lock? A category represented in the offered six may not be chosen for the final committee; define the required response.
- Common utilisation across appointment types and roles is confirmed for now. Define the corresponding last-nomination/lifetime history details in the schema review; do not reintroduce separate allocation counts without a later approved change.
- Annual attribution: final-lock date is confirmed; define same-year versus cross-year replacement adjustments and effects on last-nomination/lifetime totals.
- Pending panels: eligibility and SRS ranking are settled. Define outstanding-offer lifecycle, withdrawal/replacement handling, date conflicts and concurrent revalidation. Pending offers are not final utilisation or an extra ranking factor.
- Lock and correction authority, supporting evidence of management's choices, cancellation of the entire final committee, and replacement approval mechanics.
- Rank ties for never-selected experts, fixed sequence ownership, exhausted pools and simultaneous processing.
- Hindi entry/letter visual acceptance, approved font distribution, template wording changes and official signing mechanism.

These are details not answered by simply choosing SRS over samples. They stay at the relevant discussion gates; they are not automatic blockers for independent approved work.

## 5. Regression scenarios for the revised plan

- An expert with one locked subject-expert selection and one locked VC-nominee selection in the same nomination year has common utilisation of two; changing appointment type or nominee role does not reset the count. Additional pending offers leave that total unchanged.

- Offered six have zero new utilisation; management selects a subset; only locked selected members contribute.
- Saving or repeatedly submitting the same final lock cannot double-count.
- Offered-panel replacement preserves original expert/reason without increment or decrement.
- Proposed post-lock replacement has no effect until approved/locked; locked change reduces the removed expert and increases the replacement once.
- Changes preserve the original decision and history; counters cannot become negative from duplicate processing.
- Panel has required category representation but selected subset omits it: expected behaviour must be settled before final-lock validation is built.
- Subject-expert composition initially matches the user-authorised provisional SRS mapping, not the unapproved sample numbers; its provisional status is visible internally.
- A new subject-expert policy version changes only new allocations of that type; Principal/HoD policies and earlier issued/locked records remain unchanged.
- Explicit draft regeneration uses and records the chosen new version; letters and replacements retain a traceable link to the applicable panel policy.
- Unicode Hindi survives input, save/reopen, search and rendered letter with conjuncts/matras intact.
- College staff have no login or portal; POC actions are individually attributable to a University account.
- Own-college expert is excluded from every nomination role and replacement, including when the subject pool is scarce; spelling differences between college names cannot bypass this exclusion.
- An eligible expert with a pending offer remains in the candidate pool; pending status neither increases utilisation nor changes the SRS ranking. An otherwise identical candidate set ranks the same regardless of pending-offer status.
- After a final lock, subsequent allocations use the updated applicable utilisation and nomination history; pending offers alone do not produce those updates.

## Deferred homepage content edit

The user finds the main page too slogan-heavy and wants practical university-office wording later. **Do not modify homepage content now.** Record this as a future content task; no copy or layout changes are authorised by the current feedback.

## 6. Source references

- Original SRS v1.0: `C:\Users\rishi\Downloads\Software Requirements Specification.pdf`.
- Three-page lecturer/subject-expert examples: `C:\Users\rishi\Downloads\panel for subject expert and vc nominee.pdf`.
- One-page Principal/HoD example: `C:\Users\rishi\Downloads\principal or Hod.pdf`.

All four sample pages were visually inspected; OCR is unreliable for the Hindi text. No scanned signature was adopted as a signing credential. Sources were read, not modified.
