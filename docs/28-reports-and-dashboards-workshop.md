# Reports and dashboards phase

Status: approved for implementation. User has prioritised this phase and deferred Admin-managed scoped audit access until last. SRS sections 22 and 23 remain the source requirements; later conversation decisions govern roles and fresh-start counting.

Reconciled on 22 September 2026: the Registrar/Reviewer scrutinises a request, while the VC/Admin generates and verifies proposed panels and final-locks selections. This does not change the report population or access boundary: Registrar, VC and Admin receive dashboards/reports; POC does not. The fresh-start ledger, confirmed replacement contributions and reversals remain the sole reporting source.

## Delivery order

1. Shared reporting calculations and Registrar/VC/Admin dashboard.
2. Nomination, utilisation and representation reports, with filters and CSV downloads.
3. Cancellation/replacement reports and reconciliation; resolve the two source-data gaps below.
4. Demonstrate the complete reporting journey and record acceptance evidence.
5. Resume remaining readiness work. Deliver scoped audit browsing/grants last; existing transaction logging continues throughout.

Each step is a stakeholder demonstration checkpoint, not a committed calendar deadline.

## Dashboard proposal

Registrar, VC and Admin receive the SRS dashboard. POC retains a request-status workspace without proposed names or university-wide expert utilisation reports.

Cards: total requests, pending requests, issued panels, active experts, active SC/ST experts, active OBC experts and active experts with zero use in the selected July–June year. Show generated proposals, locked committees and issued documents as separate measures.

Proposed definitions: pending requests are submitted or offered requests without a locked final selection. Draft/returned requests have their own queue. Issued panels count distinct cases with an approved final letter, not PDF downloads or repeated document versions. Cancelled cases are identified separately.

Expert table: name, academic designation and administrative post, institution, category, current-year common count, lifetime system count, last nomination date and active status. Filters: nomination year, subject, college, nomination role and category where meaningful. Every card explains its population and links to the corresponding filtered records.

## SRS report coverage

| ID | Report | Proposed output |
|---|---|---|
| 01 | Professor-wise nominations | Expert totals and locked nominations in Professor seats |
| 02 | Principal-wise nominations | Expert totals and locked nominations in Principal seats |
| 03 | VC nominee utilisation | Expert totals and locked VC nominations |
| 04 | College-wise selection committees | Locked committees with final composition and approved changes |
| 05 | Subject-wise nominations | Request subject, committees and expert contributions |
| 06 | Month-wise nominations | Lock-month contributions and reversals shown separately |
| 07 | July–June annual utilisation | Effective contributions per expert and year |
| 08 | SC/ST representation | Final non-VC representation; main versus supplemental seats |
| 09 | OBC representation | Final non-VC representation; main versus supplemental seats |
| 10 | Experts not nominated during year | Active directory experts with zero effective use; not a declaration of eligibility for a specific case |
| 11 | Experts nominated maximum times | Highest common annual totals, retaining tied experts |
| 12 | Cancelled nominations | Confirmed cancellations, original members, reasons and reversed contributions |
| 13 | Replacement experts | Removed/replacement experts, role, reason, approval time and count effects |
| 14 | Manual deviations | Requires explicit authorised override records; do not infer deviation from normal VC selection of four offered Professors |
| 15 | Expired EC panels | Requires clarification of which expert-directory approval validity expires; do not substitute inactive experts or generated panels |

Roles 01–03 describe nomination seats rather than a person's current job title. They remain breakdowns of one common utilisation count, not separate fairness counters.

## Counting and history

Use one shared calculation path for engine history, dashboard and reports. Start from the approved zero-history boundary. Count only locked selections and confirmed replacement contributions; subtract confirmed reversals. Draft/offered names never increase utilisation.

Proposed reporting date is final-lock date, and replacement approval date for incoming replacements, in the application timezone. Years run 1 July–30 June. Prior-year figures show surviving contributions attributed to their original nomination year, with reversals visible separately; this is a current corrected report, not an unimplemented historical-as-of view.

Use stored decision snapshots for historical category, college and subject facts wherever available. Inspect missing replacement snapshots and capture required facts for future decisions before claiming historical accuracy. Never fabricate missing past facts from a current master record.

No editable counters or duplicate reporting database. Query services live in a reporting module; screens and CSV exports share filtering and access checks. Any necessary schema additions return for explicit approval with fields and constraints.

## Acceptance

- Dashboard totals reconcile with report detail and the nomination ledger.
- An offered panel has zero utilisation effect; a lock adds only chosen members.
- Replacement reduces the removed expert and adds the incoming expert; cancellation reverses the applicable contributions.
- Common totals reconcile with role breakdowns and July–June boundaries.
- POC cannot access restricted report URLs or exports.
- CSV handles Hindi, preserves filter meanings and neutralises spreadsheet formula-like text.
- Missing data and unavailable reports are labelled explicitly; an unsupported report is not presented as an empty completed report.
- No new automated tests, as requested. Use configuration checks and a controlled manual walkthrough.

## Approved scope boundary

The dashboard populations, lock-date reporting, corrected historical totals, role access and CSV-first exports above are approved. Report 15 needs a separate answer about directory approval validity; its dependent schema remains pending. Report 14 depends on the authorised override workflow and must stay visibly unavailable until its records exist. These two dependencies do not block reports 01–13 or the dashboard.
