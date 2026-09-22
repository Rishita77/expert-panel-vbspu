# Panel changes — implementation handover

14 September 2026. Document 20 was approved as DEC-043. This implementation adds the protected records, staff screens and accounting core for locked-panel changes.

## Delivered

- The final decision is a fresh start: all experts begin at zero, and only final locked selections contribute to utilisation. No tracking-baseline table or historical nomination import is used.
- Processor screens allow a locked final selection to start a replacement or cancellation. A replacement records the reason/verifier, creates a new-date engine run and selects its next eligible person automatically. Cancellation requires a reason, verifier and an affirmative record that selection work has not occurred.
- The processor submits the change with revised management references (and VC reference where the VC nominee changes). A reviewer may return it with a reason or confirm it.
- A confirmed replacement creates an immutable reversal for the outgoing active contribution and one immutable replacement contribution for the incoming expert. The reversal keeps the original contribution's July–June year; the incoming contribution uses the confirmation date's year. A cancellation reverses every effective member's active contribution.
- Effective membership supports chained replacements: each confirmation replaces the current effective expert, and cancellation reverses whichever contributions remain active.
- PostgreSQL guards prevent deletion or modification of confirmed changes, reversals and replacement contributions. A one-to-one reversal relationship prevents repeated subtraction.

## Important boundary

The application has no issued-offer record yet: an `AllocationRun` remains a recommendation, as established in the initial final-selection slice. Therefore, pre-final-lock offer replacement is still performed by creating a fresh engine recommendation; it has no utilisation effect by design. A fully versioned issued-offer/addendum workflow, official letters, signing and notifications remain later work.

An active tracking baseline intentionally has no staff-facing editor: the user kept the exact operational start date pending. Create and activate it as a controlled go-live operation with the approved date and reference; do not use demonstrations or the two sample PDFs as selective historical counts.

## Verification

- 31 allocation and workflow tests pass, including fresh-start history and cancellation reversals.
- Django system checks, migration-drift checks and linting pass.
- Local PostgreSQL migrations `0006`–`0008` applied successfully.
