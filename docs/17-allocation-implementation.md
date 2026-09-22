# Allocation recommendations — implementation handover

13 September 2026. User authorised coding after the SRS mapping and clarified questions. This is a recommendation/verification slice, not an operational nomination release.

## What staff can do

- Open a saved request and choose **विशेषज्ञ आवंटन**. The engine resolves the applicable approved sources using appointment type/subject and today's allocation date. No operator list selection or sequence editing.
- Record availability/conflict decision, reason and verifier's name/designation. The logged-in recorder is retained separately. No transfer-document upload. Retirement/transfer marks permanent inactivity across roles; changes to the expert master cannot reactivate that person.
- Save an evaluation and revisit its immutable snapshot. Request edits are identified on older results; regeneration creates another run. Verifications apply to the request revision and allocation date for which they were entered.
- Use the clearly labelled synthetic demonstration to see full allocation, unequal count/date ranking and shortages. Change between Principal, HoD and provisional subject-expert policy. Synthetic names/history are isolated from University expert records.

Routes: `/office/allocation/demo/`; saved requests link to `/office/allocation/request/<id>/`; snapshots use `/office/allocation/run/<id>/`. Existing office home links to the demonstration. The public homepage slogans remain unchanged.

## Explicit rule-to-code and test map

| Source | Executable rule | Code / verification |
|---|---|---|
| SRS 10/11/14/15/29, DEC-027/034 | Common annual count, lifetime oldest last nomination, permanent sequence; verified never nominated first on tied counts | `engine.rank_key`, `History.valid`; priority and unknown-history tests |
| SRS 10/16 | Allocation-date current July–June ranking year | `engine.nomination_year`; June/July boundary test |
| SRS 4.1/5/6/26 | Role/rank, internal/external VC institution, categories, active source/member/expert and date validity | `services.candidate_facts`, `generate`; existing expert eligibility tests and allocation adapter tests |
| DEC-024/034 | Own-college absolute exclusion; allocation-date-only eligibility | `candidate_facts`; own-college and future-selection-date test |
| DEC-034, SRS 5/26 | VC first, Principal then five Professors, one person per proposal | `engine.allocate`; cross-role collision, duplicate and shortage tests |
| SRS 6 | Inspect main six; add missing SC/ST and/or OBC, allowing verified Assistant Professor supplement | Composition/adapter; all four representation combinations and VC-not-substituting test |
| DEC-026 | No pending-offer count, reservation or priority weight | Pure candidate contract contains no pending weight; deterministic repeated-allocation/no-mutation test |
| SRS 12/13, DEC-037 | Case unavailability/conflict skips, recorded verifier/reason; retirement/transfer permanently inactive | `Assessment`, `assess`, database history/reactivation guards; rollback and permanence tests |
| DEC-038 | One approved source per role/type/subject; no union or chooser | Source resolver and pool approval overlap rejection; crossed-scope and duplicate-source tests |
| SRS 24/30 | Preserve evaluated facts, policy and ordering; no casual manipulation | `AllocationRun.snapshot`, atomic audit, PostgreSQL append-only triggers; immutable snapshot and permission tests |
| DEC-035/036 | Partial PDFs do not establish zero or complete historical counts | `history.verified_history` deliberately returns no values until approved reconciliation; unknown-history blocks authoritative ranking |

## Implementation choices and boundaries

The pure engine receives validated candidates and history and returns structured results; it has no database, clock or counting side effect. Source retrieval, eligibility, ordering, composition and templates are separate. Independent policy snapshots already exist in `policies.py`; a new policy must not edit earlier results.

Existing user/college/expert/pool identities are reused. Two additive nomination tables hold append-only assessments and run snapshots. The request, actor, allocation date and revision are relational fields; evaluated source, candidate and policy facts are retained in the JSON snapshot to avoid introducing a second mutable master directory. Snapshot contents omit expert contact details. Request/run reads are restricted to processors/reviewers; master or account-admin permissions alone do not grant allocation access. Writes require current processor authority under the shared access mutex.

The history provider is intentionally unpopulated for real records. The two supplied PDFs are confirmed final-selection examples from a larger set. Actual requests currently produce eligibility/source evaluation and a history/shortage block, not made-up recommendations. The synthetic demonstration exercises the same pure composer with explicitly constructed history, not fake values assigned to real experts. Historical collection/reconciliation and ledger integration remain necessary before real allocation can rank authoritatively.

Unknown availability is not declared clear. Known case exclusions are honoured; any later complete recommendation with unresolved verification must remain provisional. The current real-history block prevents official use regardless. Formal scrutiny, VC decision/override, issuing offers, final selection/lock, replacements/cancellations and count mutations are not implemented here. No official letter is issued.

Retirement/inactivity never changes prior counts automatically. Original final-selection records must be retained by the later ledger. An exceptional correction to a permanently inactive decision is not exposed as an ordinary reactivation operation.

Pool approval now rejects overlapping source scopes across lists under the shared mutation lock. Existing overlapping demo data is retained, not deleted or arbitrarily merged; such data is reported as requiring correction if encountered. New versions of the same source retain the normal supersession workflow.

## Verification and demonstration

- 91 tests passed together: allocation, expert/pool and foundation PostgreSQL tests.
- After separating the history input, all 27 allocation tests passed, including two added checks for verified-history integration and simultaneous evaluations producing identical recommendations without reservations. Total distinct tested cases across allocation, expert/pool, foundation and preview: 116.
- 23 original preview tests passed. Ruff checks and migration drift checks passed.
- Browser journey passed: complete synthetic panel, fairness example, shortage, mobile overflow, saved real-request evaluation and reviewer read-only access. Screenshots in `test-results/allocation-desktop.png` and `allocation-mobile.png` were visually reviewed.
- PostgreSQL migrations `nominations.0001_initial` and `0002_history_guards` applied to the isolated local database. Existing records were preserved. The browser walkthrough adds a saved evaluation to an existing demonstration request; it does not reset user data.

Repeat checks with `.venv/Scripts/python.exe -m pytest tests/test_allocation.py tests/test_experts.py tests/test_foundation.py --ds=config.foundation -q`; preview separately uses `tests/test_preview.py`. Browser runner is `tests/allocation_browser.cjs`, using the bundled Playwright runtime and ignored local demonstration credentials.

Next: reconcile the University history when supplied and connect its verified values; discuss the concrete final-selection/lock/authority and replacement-accounting phase. A complete demo is not evidence of production readiness or authoritative opening utilisation.
