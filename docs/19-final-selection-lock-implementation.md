# Final selection and reviewer lock — implementation handover

13 September 2026. The user approved document 18 and its final-category boundary. This delivery is intentionally limited to first-time final selection and lock.

## Delivered workflow

1. A processor can create one final-selection draft from one complete saved allocation result. The result stays the authoritative offered record; the system copies each offered component with identity/category/institution facts.
2. The POC records management and VC decision references/dates, then selects **one Principal, four Professors and one VC nominee** from that offer. Category supplements from the offer may also be selected.
3. The POC submits the draft. Missing final role counts, duplicate people, missing SC/ST/OBC representation, or missing decision references prevent submission.
4. This original workflow has been superseded: VC/Admin now directly approve and lock the VC's final selection. Registrar can view the proposal but cannot lock it.
5. Lock rechecks selected people: active status, own-college exclusion, availability and conflict assessments recorded for the original allocation date/revision. It then creates exactly one immutable utilisation entry for every selected member, records the July–June lock year and writes audit/review history in one transaction.

The VC nominee remains **outside** the final SC/ST/OBC coverage test, as explicitly approved with document 18. A category missing from management's selected Principal/four Professors must be supplied through a selected category supplement; otherwise submission/lock is blocked. Category addendum generation is not part of this delivery.

## Data integrity

Current tables: `FinalSelection`, `FinalMember` and `UtilisationEntry`. PostgreSQL guards prevent changing/deleting a locked final selection, its selected membership or contribution rows. A unique contribution per final member prevents double counting. Lock retry returns the existing lock rather than creating new entries.

The final lock uses the server's lock time to assign the July–June year. Management's decision date is preserved but does not backdate utilisation. Existing opening history is still incomplete, so committed entries are known events but do not establish complete historical totals or “never nominated” status.

No post-lock replacement, cancellation, unlock/correction, letter issuance, notification, general override, VC-login workflow or historical bulk import was added. Those require their own approved policy and accounting design.

## Verification

- 30 allocation tests passed, including the final-selection workflow, category and missing-assessment blocks, reviewer-only lock, idempotent retry and database immutability checks.
- Django checks, migration drift checks and linting passed.
- Additive migrations `0003`–`0005` were applied to the local development database without removing existing records.

Run: `.venv/Scripts/python.exe -m pytest tests/test_allocation.py --ds=config.foundation -q`.
