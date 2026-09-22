# Allocation correction proposal

Status: discussion only. The user authorised this planning document after reporting an empty allocation. No implementation or database changes are authorised by this document. No additional tests are to be created.

## Evidence and intended result

Reviewed the original SRS Version 1.0 numbered sections 1–30, current decisions, and current allocation/history code. This review used extracted PDF text; it does not claim a fresh visual review of the final image flowchart or annotated PDF.

The reported run stops at VC processing. The preceding read-only database inspection found no TrackingBaseline records. Expert 18 has a Professor designation and Computer Science subject, but cannot rank without the tracking baseline. Experts 15–17 have unknown academic designations; 15 and 19 have no subjects. These are observed records, not instructions to overwrite them.

The intended offered result is one VC nominee, one Principal, five Professors, and additional category members when needed. Final management selection remains the separately agreed provisional one Principal plus four Professors, separate VC, and required category members.

## Rule reconciliation

| Rule/source | Confirmed direction | Current implementation or gap | Proposed correction |
|---|---|---|---|
| SRS 4.1, 5, 19: composition | VC 1; Principal 1; Professors 5; supplements when needed. Same provisional structure for subject-expert requests | Policy has the correct numbers, but early return hides subsequent roles | Preserve numbers; display all role sections and dependencies |
| SRS 5, 7, 26, 29: candidate source | Latest user decision: consider experts directly without manually maintaining list membership | Directory now supplies candidates; EC validity/approval no longer gates generation | Retain directory sourcing. Explicitly document this user override of the original EC-list workflow; do not claim it is unchanged SRS behaviour |
| SRS 4.1, 14: VC subject | Higher-education expert at Professor level; institutional conditions apply | Every VC candidate must match request subject | Proposed: no same-subject requirement for VC. SRS does not explicitly impose it; confirm this interpretation before coding |
| SRS 5, 8, 9, 29: main-panel subject | SRS describes subject-specific applicability but does not spell out personal subject matching for each seat | Blanket personal-subject check applies to every role | Proposed: Professors match request subject; Principal may be from another subject. Principal scope requires confirmation |
| SRS 6, 15: supplemental subject | Required category; Professor or Assistant Professor level; same fairness ordering | Blanket personal-subject check also applies here | Confirm whether supplements may come from other subjects; do not infer a restriction or exemption |
| SRS 4.1, 26: VC institutional eligibility | External to VBSPU, or affiliated Government/Aided college; own-college exclusion always applies | Nullable affiliation is used as a truth value: unknown can pass as external | Require explicit institutional facts. Unknown must not mean external. Reconcile appointment classification and institution affiliation; conflicts require staff correction |
| SRS 4–7: role facts | Academic designation separate from optional administrative post; Principal is not automatically Professor | Latest directory change also removed evidence checks | Restore an explicit distinction between entered and verified facts; offer inline verification with recorded staff identity instead of another hidden maintenance step |
| Post end date; allocation-date decision | Administrative post may have unknown end date; eligibility evaluated on allocation date | Post end date is stored but not checked for Principal eligibility | Apply known end date to post eligibility while retaining academic eligibility. Confirm whether the stated end date itself is included |
| SRS 10, 14–17; fresh-start decision | Common July–June utilisation; final lock only; no pre-system history required | No active baseline means unknown history for everyone | Add visible tracking setup and explicit start date. New experts start at zero within that tracked period; never fabricate pre-system history |
| SRS 10–11: ordering | Lowest common annual count, oldest tracked last nomination, fixed sequence | Ranker implements this; missing baseline prevents use | Retain ordering; show numbers and a plain explanation after setup |
| SRS 7, 10, 30: sequence | Permanent system-generated sequence; no staff manipulation | Already generated, but poorly explained in intake | Display read-only sequence after saving and in expert details. Gaps are valid; do not renumber records |
| Fresh-start last date | No nomination recorded since tracking began until first final lock | Unknown and never-nominated wording is misleading | Distinguish tracking not configured, no tracked nominations, and actual last locked date. No historical-date input is required |
| SRS 12–13: availability/conflicts | Named verifier, case-specific exclusions; retired/transferred permanently inactive | Assessment exists; absent assessment may yield provisional results | Show verification status for recommended people. Keep provisional recommendations separate from a panel ready for issue/lock |
| Own-college; SRS 26: distinct people | Absolute own-college exclusion and no duplicate person across seats | Implemented | Preserve across recommendations, final selections and replacements |
| VC-first decision | VC then Principal then Professors; no automatic backtracking | Early return stops evaluation after any failed stage | Preserve committed selection order; show downstream diagnostics without prematurely allocating the same person to another role |
| SRS 6: representation | Main six satisfy SC/ST and OBC; VC does not count; supplement if absent | Implemented after main stages, hidden if an earlier stage fails | Show pending representation when main composition is unresolved; calculate when composition is known |
| SRS 17–18; final-lock decisions | Offers count zero; final lock adds; confirmed replacement reverses removed contribution | Ledger and reversals exist | Preserve audit and transactional behaviour; inspect effects manually in the approved example |
| SRS 24, 26: saved results | Historical snapshots immutable; incomplete results cannot be issued as complete | Existing runs remain unchanged | New evaluation creates a new run. Clearly label older results and incomplete/provisional outcomes |

## Proposed staff screens

### Expert entry and details

Collect identity, institution, academic designation, subjects, category, and optional administrative post/end date in one entry flow. Display the generated sequence after saving. Alongside these facts show verification status and an action for authorised directory staff to confirm the recorded facts, with actor/time and a short reference or note. A document upload is not required. Collecting a fact must not silently verify it.

For existing experts, show the specific missing or contradictory facts and a direct correction link. Never infer a designation from a name or fill missing subjects automatically. Explain that verification is separate from availability for a particular request.

### Tracking setup

Before tracking is configured, show one request-level message: 'Nomination tracking has not started. Configure the start date to rank experts.' Eligibility diagnostics may still be viewed. Do not repeat a misleading historical-data failure for each expert.

Proposed setup owner: administrator. Present start date, nominated setup actor/reason, and a read-only inventory of existing locks/replacements before activation. Do not silently activate on first allocation. The start date and treatment of existing demonstration contributions require explicit approval. Keep production activation separate from local demonstration configuration.

### Reviewer allocation result

Top summary: requesting college, post, subject, allocation date, tracking start/year, and overall status. Then show all components:

| Component | Required | Display |
|---|---:|---|
| VC | 1 | Recommended name, or the precise reason none can be recommended |
| Principal | 1 | Recommendation, shortage, or 'provisional candidates—VC selection unresolved' |
| Professors | 5 | Recommendations and actual number available, or provisional candidate diagnostics |
| SC/ST and OBC | As needed | Satisfied in main six, supplemental member required, or pending main composition |

Show the recommended panel first. Put long excluded-candidate explanations behind expandable role sections; separate missing records from actual eligibility exclusions. Each recommended name shows academic designation/post, institution, category, tracked count, last tracked nomination, sequence, and verification status.

If VC cannot be selected, display later roles' candidate diagnostics but do not call them committed seats. If an earlier role has selected people, exclude those people from subsequent roles. No silent fairness bypass to improve panel completion. Exact shortages remain visible and issue/finalisation remains blocked while required conditions are incomplete.

## Delivery order after approval

1. Finalise the subject/verification/date decisions below and freeze the rule table.
2. Resolve tracking configuration, including explicit treatment of demonstration history.
3. Make expert facts and verification complete within the staff flow; identify existing records for staff correction.
4. Correct role eligibility and incomplete-result diagnostics; retain ordering and immutable snapshots.
5. Update screen wording and current documentation so old list/history instructions are visibly superseded.
6. Perform the manual walkthrough below with the user. No new tests, test scripts or fixtures will be added.

## Manual acceptance walkthrough

Use an explicitly approved local example with enough distinct eligible people. Agree expected recommendations on paper before using the engine. Use actual staff-entered facts or a clearly authorised synthetic dataset; do not silently edit the current directory.

- Confirm one VC, one Principal and five Professors when sufficient eligible candidates exist, with no duplicates or own-college members.
- Confirm zero tracked counts and sequence ordering at fresh start; inspect recorded counts/dates after a final lock.
- Confirm required category supplementation and that VC category does not satisfy the main-panel check.
- Remove availability for the first-ranked candidate and verify the next person and explanation.
- Inspect no-VC, insufficient-Professor, missing-record and unconfigured-tracking scenarios: every role remains understandable, without claiming completion.
- Confirm a Professor who is also Principal can qualify for both roles but occupies only one seat; inspect known/unknown post end dates under the agreed date rule.
- Confirm older generated results stay unchanged when a new allocation is generated.

The walkthrough is proposed verification, not evidence of results already obtained. No tests or application commands were run as part of authoring this proposal.

## Decisions needed before dependent implementation

1. Subject scope: proposed same-subject matching for the five Professors, no same-subject restriction for VC or Principal; confirm whether category supplements are also unrestricted by subject.
2. Tracking: choose a start date for local use and determine whether existing demonstration locks are excluded or included. Inspect a concrete inventory before deciding; preserve records either way.
3. Verification: approve the inline directory-staff confirmation described above, distinct from request-specific availability/conflict verification.
4. Post expiry: proposed final date is inclusive; after it, Principal-role eligibility ends while Professor eligibility can continue. Unknown remains explicitly unknown, not an invented date.

These are proposals, not institutional rules already approved. No schema or engine implementation should silently resolve them.
