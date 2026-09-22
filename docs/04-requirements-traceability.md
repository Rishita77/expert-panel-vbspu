# SRS requirements traceability

> This is the original SRS mapping, not the complete current acceptance baseline. The user's later clarifications replace college self-service and panel-approval counting with University POC intake and locked-final-member accounting, and add subject-expert scope. Apply the [current requirements overlay](09-current-requirements.md) to affected rows before implementation or verification.

Source: SRS v1.0, reviewed 8 September 2026. Section numbers below refer to the source PDF, not this documentation.

The original section table records full-feature acceptance obligations, not claims that entire SRS sections are complete. The following first-slice coverage is now implemented; remaining obligations stay planned.

| Coverage | Implemented evidence | Remaining boundary |
|---|---|---|
| SRS-03 / SRS-25 | University staff roles, direct-URL read/write permissions, deactivation and shared case access; `tests/test_foundation.py` access matrix and browser checks | Later scrutiny/approval/export powers |
| SRS-08 | Institution/subject directory and saved Hindi draft fields, minimum draft validation, Unicode round-trip | Submission evidence, private documents and required final request rules |
| SRS-24 | Attributable before/after history, role grant/revoke provenance, atomic audit rollback tests | Nomination/approval/replacement audit and operational tamper protection |
| SRS-28 (partial) | PostgreSQL migrations/constraints, CSRF/session checks, concurrent edit/admin tests and desktop/mobile walkthrough | Production security, workload/recovery acceptance and monitoring |

See [foundation implementation and verification](12-foundation-implementation.md). No allocation or final-lock requirement is claimed implemented.

## Section mapping

Allocation update (DEC-040): `apps/nominations/engine.py` implements the SRS fairness/composition rules with explicit user overrides; `services.py` evaluates approved records and saves immutable snapshots. `tests/test_allocation.py` covers ordering, date boundaries, categories, duplicates, own-college, history blocks, verification, permissions and concurrent evaluations. See [the exact rule-to-code map](17-allocation-implementation.md). This is partial SRS-04/05/06/10–16/24/26/29/30 coverage: real history, operational approval/issue/final lock and accounting remain incomplete. Do not mark entire SRS sections complete based on synthetic demonstrations.

| ID | SRS section / pages | Requirement | Owning modules | Phase | Verification obligation |
|---|---|---|---|---|---|
| SRS-01 | 1 / p1 | Transparent, rule-based expert nomination for Principal/HoD requests | applications, nominations, audit | 2–7 | Complete traceable request-to-nomination journey |
| SRS-02 | 2 / p1 | Request through issued letter/history; July–June year | applications, approvals, documents, nominations | 2–6 | Journey completion and agreed annual-boundary cases |
| SRS-03 | 3 / p2 | Stakeholder responsibilities | accounts | 1 onward | Approved action/role matrix enforced server-side |
| SRS-04 | 4 / p2 | One VC nominee; at least Professor; prescribed internal/external eligibility | experts, nominations, approvals | 3–5 | Eligible/ineligible rank and institutional combinations |
| SRS-05 | 5 / p2–3 | EC-approved panel; 1 Principal + 5 Professors; post/subject/approval/validity metadata | panels | 3 | Approved pool interpretation, membership constraints and active applicability |
| SRS-06 | 6 / p3–4 | SC/ST and OBC representation; additional approved category nominees; Assistant Professor exception | nominations, panels, experts | 3–4 | Both present, each singly absent, both absent, no eligible supplement; boundary decision applied |
| SRS-07 | 7 / p4–5 | Expert identity, institution, category, panel/approval/status and utilisation information | experts, panels, nominations | 3–5 | Validated master records; history-derived count reconciliation |
| SRS-08 | 8 / p5 | College details, vacancy/request details, supporting documents | institutions, applications, documents | 1–2 | Required field validation; Principal/HoD requests; private uploads |
| SRS-09 | 9 / p6 | Scrutiny, deficiency and eligibility workflow | applications, accounts | 2 | Approved transitions; ownership; correction loop; invalid action rejection |
| SRS-10 | 10 / p6 | Rank by annual count, oldest last nomination, fixed sequence | nominations | 4 | Worked examples for each ordering key and all approved tie cases |
| SRS-11 | 11 / p7 | Utilisation takes precedence over illustrative round-robin | nominations | 4 | Unbalanced counts after earlier skips/replacements produce approved ranking |
| SRS-12 | 12 / p7 | Availability/status exclusions and recorded skip reasons | experts, nominations | 3–4 | Each approved status treatment; next eligible candidate and reason history |
| SRS-13 | 13 / p7–8 | Case-specific conflicts exclude without permanent sequence alteration | nominations | 4 | Conflict blocks affected case; original sequence retained; declaration recorded |
| SRS-14 | 14 / p8 | VC recommendation and alternate eligible choice retained | nominations, approvals | 4–5 | Recommendation/decision separation, eligibility enforcement, recorded deviation |
| SRS-15 | 15 / p8 | Fair allocation of category experts; count after approval | nominations, approvals | 4–5 | Category ranking and no utilisation change for unapproved draft |
| SRS-16 | 16 / p9 | Annual July–June cycle; retain previous years and lifetime totals | nominations, reporting | 5, 7 | Boundary dates and complete retained prior-year history |
| SRS-17 | 17 / p9 | Count only on final approval; preserve nomination transaction details | approvals, nominations, audit | 5 | Atomic writes, replay safety, concurrent approvals, transaction detail completeness |
| SRS-18 | 18 / p10 | Replacement chooses next eligible; retains original and reason/date/approver | nominations, approvals | 5 | Approved replacement chain and counting policy; original record unchanged |
| SRS-19 | 19 / p10 | Distinct VC, six EC experts and optional category supplements in output | nominations, documents | 4–6 | Approved composition and visible representation source |
| SRS-20 | 20 / p11 | Approval workflow through letter and utilisation update | applications, approvals, documents | 2–6 | Authorised sequence, pending-approval block, no count-before-approval |
| SRS-21 | 21 / p11–12 | Official reference/date/details, conditions and signature provision | documents, approvals | 6 | Approved template content, numbering/versioning, signature status, authorised issue |
| SRS-22 | 22 / p12 | VC/Registrar expert-utilisation dashboard and summary cards | reporting | 7 | Correct totals, filters, role access and drill-down reconciliation |
| SRS-23 | 23 / p12 | Fifteen prescribed reports | reporting | 7 | All report definitions below verified against recorded history |
| SRS-24 | 24 / p13 | Actor/action/time/change/reason/authority audit; ordinary users cannot edit | audit | 1 onward | Audit completeness per feature; restricted reads/writes; historical evidence retained |
| SRS-25 | 25 / p13 | Role-based access; college isolation; restricted expert information | accounts and all modules | 1 onward | Read/write/download/export isolation and privilege escalation checks |
| SRS-26 | 26 / p13–14 | Block invalid VC, panel, composition, category, inactive/duplicate/conflicted experts and pending approval | nominations, approvals | 4–5 | Separate negative finalisation case for every mandated blocker |
| SRS-27 | 27 / p14 | Exceptional authorised override with required reason and full record | approvals, audit | 5 | Required justification, authorised decision, recommendation retained; no eligibility bypass |
| SRS-28 | 28 / p14–15 | Security, availability, integrity, performance, scale, backups, traceability | cross-cutting, deployment | 1–8 | Agreed workload and recovery targets; security review; restore drill; monitored pilot |
| SRS-29 | 29 / p15 | Core allocation process | nominations, approvals | 4–6 | End-to-end approved examples; eligibility revalidation at finalisation |
| SRS-30 | 30 / p16 | System selects; operators cannot manipulate sequence; authorised departures recorded | nominations, accounts, audit | 3–5 | Sequence maintenance protection and explicit controlled deviation tests |
| SRS-VIS | Visual summary / p18 | Consolidated flow; notifications to college/authorities; web usability | notifications, interface | 2, 6–7 | Recipient/delivery checks and usable forms; differences in flow order resolved explicitly |

## Report inventory

All reports require role-appropriate access and consistent definitions. Filters/export formats and treatment of cancelled/replaced nominations are agreed before implementation. Counts must reconcile with the approved ledger semantics.

| Report ID | Required report | Principal evidence |
|---|---|---|
| REP-01 | Professor-wise nominations | Expert history matches rows and totals |
| REP-02 | Principal-wise nominations | Principal nomination records reconcile |
| REP-03 | VC nominee utilisation | VC role records and agreed count scope reconcile |
| REP-04 | College-wise selection committees | Correct college association and access scope |
| REP-05 | Subject-wise nominations | Subject/post filtering preserves historical subject facts |
| REP-06 | Month-wise nominations | Uses approved reporting date definition |
| REP-07 | July–June annual utilisation | Both boundary dates and retained previous years verified |
| REP-08 | SC/ST representation | Main-panel versus supplemental representation is traceable |
| REP-09 | OBC representation | Main-panel versus supplemental representation is traceable |
| REP-10 | Experts not nominated in the year | Zero-use and eligible-population definition agreed and tested |
| REP-11 | Experts nominated maximum times | Agreed counting scope and ties handled consistently |
| REP-12 | Cancelled nominations | Original records remain visible; approved count treatment applied |
| REP-13 | Replacement experts | Original-to-replacement relationship, reason, date and approver visible |
| REP-14 | Manual deviations | Recommended/selected experts, reason, actor and authority visible |
| REP-15 | Expired EC panels | Validity/status rules and historical panel records reconcile |

## Coverage review rules

- Link each implemented requirement to its approved phase decision and meaningful verification evidence.
- Explicitly distinguish an SRS requirement, a user-approved elaboration, and a proposed implementation choice.
- Revisit affected tests/reports whenever a policy decision changes.
- The image summary does not silently supersede the numbered requirements where order or meaning differs.
- Do not claim complete SRS coverage until every entry has implementation and acceptance evidence or an explicit user-approved disposition.
