# Delivery roadmap

Current sequencing update: reports and dashboards are next; Admin-managed scoped audit-view access is deferred until last at the user's request. See [reports and dashboards workshop](28-reports-and-dashboards-workshop.md) for the next phase proposal. Audit recording continues throughout.

> Historical roadmap requiring revision. College onboarding is removed; allocation is prioritised; subject-expert scope and final-lock accounting are confirmed. A shorter revised schedule was discussed but is not an approved phase plan. See [current requirements](09-current-requirements.md).

Status: roadmap authorised by the user on 8 September 2026; phase-level approvals remain separate.

## Schedule and working method

Planning allowance: about 50 working days over ten weeks. Day 1 starts at kickoff; no calendar launch date is committed. Waiting for approvals, University decisions, data, credentials, procurement, or significant revisions extends the calendar.

First working stakeholder demonstration: end of week two. Demonstrate progress weekly thereafter. First operational release: controlled pilot, followed by a wider-rollout decision.

For every phase: discuss intended behaviour and alternatives → challenge data/rules with examples → record a concrete plan and acceptance criteria → obtain user approval → implement → verify → demonstrate → record feedback and completion evidence.

| Phase | Timing | Discussion and approval gate | Deliverable and exit evidence |
|---|---|---|---|
| 0 — Foundation | Days 1–2 | Architecture, workspaces, role boundaries, traceability, first-demo contract | Reviewed foundation proposal and recorded user decision |
| 1 — Application foundation | Days 3–5 | Account/college schema, access assignments, initial permissions, audit structure, local/staging setup | Reproducible startup; login/logout; role home screens; automated access checks; synthetic seed data |
| 2 — Requests and scrutiny | Week 2 | Application schema, required documents, state transitions, deficiency/resubmission ownership | College request and scrutiny journey; private upload checks; correction loop; verified case; passing first-demo contract |
| 3 — Experts and panels | Week 3 | Source-panel/pool meaning, expert classifications, membership/validity, import and historical data policies | Expert and EC-panel management; eligibility preview; validated import preview and rejection report |
| 4 — Allocation | Weeks 4–5 | Eligibility and ranking examples, representation boundary, VC conditions, availability/conflicts, exhausted pools, simultaneous recommendations | Week 4 ranked recommendations; week 5 draft composition with explanations and validated category/conflict handling |
| 5 — Approval and history | Week 6 | Authority matrix, deviations, count semantics, annual boundary, replacement/cancellation, transaction and concurrency behaviour | Approved nomination; counts reconcile; replay-safe approval; preserved original/replacement history |
| 6 — Letters and communication | Week 7 | Numbering, approved content, template versioning, signing, recipients/channels, retry semantics | Approved-case PDF; signing status; authorised downloads; recorded delivery/retry; full sample journey |
| 7 — Reporting and readiness | Weeks 8–9 | Report definitions, data reconciliation, workload, retention, recovery, operations ownership, security acceptance | Week 8 all 15 reports and audit walkthrough; week 9 release candidate, restore evidence, browser/security/performance checks and runbooks |
| 8 — Controlled pilot | Week 10 | Pilot cohort, training, real-data approval, support/escalation, acceptance and rollback conditions | Supervised selected-college use; triaged feedback; blocking issues resolved; signed-off pilot findings and rollout recommendation |

## Dependency rules

- Resolve panel-versus-pool meaning before implementing panel membership or allocation assumptions in Phase 3.
- Agree account scope before permissions; document rules before uploading; workflow transitions before status-change actions.
- Resolve counting semantics before storing approval-dependent counters. Historical data import also depends on the counting policy when used for fairness.
- Approval and letter generation depend on the approved authority and signing policies; do not label an unsigned draft as an official issued document.
- External credentials and hosting procurement are tracked from Phase 0 even when their integration is scheduled later.
- If a decision is unresolved, hold dependent implementation and continue independent work already approved. Demo simulations must be clearly identified.

## Demonstration discipline

- Maintain one reproducible synthetic dataset, including multiple colleges and varied roles.
- Use a stable, access-controlled demo environment separate from production.
- Prepare a short scripted user journey, visible outcome, negative case, and verification evidence for each demo.
- Capture feedback as defect, clarification, or scope change with an owner and target phase.
- Mark sample/draft letters and route demo notifications only to test recipients.
- Do not reset or seed production through a demo command.

## Phase completion record

Record the approved scope, implementation version, acceptance results, demo date, feedback, unresolved dependencies, and user decision. Finishing code alone does not establish acceptance or authorise production use.

## Wider rollout

The pilot exit review decides readiness for broader college onboarding. Include training, support capacity, master-data quality, operating ownership, service monitoring, recovery evidence, and unresolved issues. University-wide launch is a subsequent authorised action, not an automatic consequence of a successful demo.
