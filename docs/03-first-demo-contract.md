# First stakeholder demonstration contract

> Superseded as a demonstration contract: there is no college portal or college login. Replace with University POC Hindi intake and allocation scenarios under [current requirements](09-current-requirements.md). Historical approval below does not authorise the old workflow.

Status: **Approved as the Phase 0 demonstration baseline.** Detailed schema/workflow decisions are approved in Phases 1 and 2 before implementation. No acceptance scenario has been implemented or passed yet.

## Goal

At the end of week two, demonstrate a real persisted college-request and University-scrutiny journey using synthetic data. A college submits a request; an officer records a deficiency; the college responds; the appropriate officer verifies the corrected case as eligible for later processing.

This demonstration establishes the request workflow. Expert allocation, final committee approval, nomination counts, and official letters are delivered in later phases.

## People and sample data

- Two clearly fictional colleges, each with a separate college account.
- Dealing Assistant and Section Officer accounts with permissions approved in Phase 1.
- A restricted administrator for setup; account credentials supplied securely, never committed.
- One sample Principal request and one sample HoD request.
- Harmless synthetic supporting documents satisfying the Phase 2 approved upload rules.
- Cases covering draft, submitted, deficiency, corrected, and verified scenarios as permitted by the final transition plan.

The SRS's candidate states are Draft, Submitted, Under Scrutiny, Deficiency, Deficiency Complied, Eligible, and Panel Processing. Before Phase 2 coding, agree exact actions and transitions; do not assume every case must pass through Deficiency or that every verified case automatically enters Panel Processing.

## Walkthrough

1. Sign in as College A and show only its applications.
2. Create a request, enter the approved mandatory details, attach a sample document, save, and reopen the draft.
3. Submit it and show the reference/status and recorded submission event.
4. Sign in as the authorised processing officer and open the submitted case.
5. Record a specific deficiency and show the reason and requested correction in the college view.
6. Respond as College A using the approved correction mechanism and resubmit.
7. Review the response and verify the corrected request as the authorised officer.
8. Show the persisted case history, including who performed each action and when.
9. Sign in as College B and demonstrate that College A's case and attachments are inaccessible.

## Proposed acceptance criteria

| ID | Scenario | Required evidence |
|---|---|---|
| DEMO-01 | Reproducible start | Documented setup/migrations/seed process produces the sample environment |
| DEMO-02 | Login and role navigation | Correct workspace after sign-in; sign-out ends access; unauthenticated protected requests are denied/redirected |
| DEMO-03 | Draft persistence | Save/reopen retains entered details and permitted attachments |
| DEMO-04 | Submission validation | Missing mandatory inputs prevent submission with clear field-level errors |
| DEMO-05 | Submitted request | Approved submission action persists a stable reference/status and audit event |
| DEMO-06 | Deficiency loop | Officer's reason is visible to the owning college; response and resubmission are recorded |
| DEMO-07 | Verification | Only the approved role/action can verify; invalid source states cannot be forced through direct requests |
| DEMO-08 | College isolation | Lists, direct case URLs, attachment URLs, and write actions cannot expose or alter another college's data |
| DEMO-09 | Private uploads | Allowed file succeeds; disallowed/oversized input is rejected under approved rules; storage is not publicly browsable |
| DEMO-10 | Audit evidence | Actor, timestamp, action and relevant change/reason are retained; ordinary users cannot edit events |
| DEMO-11 | Repeat/stale action | Duplicate submit or a stale officer page cannot silently repeat a transition or overwrite a later decision |
| DEMO-12 | User experience | Complete the journey by keyboard; labels/errors are understandable; college forms work at mobile width |
| DEMO-13 | Test/demo boundary | Synthetic records and demo environment are identifiable; no real notifications or official letters are sent |

## Required decisions before implementation

Phase 1: account provisioning and reset, college membership scope, role assignments, initial audit access, and applicable MFA controls.

Phase 2: request fields, reference format, required uploads and limits, exact transition ownership, post-submission edit rules, correction versioning, and how requests enter/leave officer queues.

These decisions have discussion owners in the [open-question register](05-open-questions.md). Their approval will refine this contract without silently changing the stakeholder story.

## Completion evidence

Collect automated test results, a manual walkthrough record, the demo build identifier, and stakeholder feedback. Do not mark this contract passed until its scenarios have been implemented and checked. Current result for every scenario: **Not implemented / not run**.
