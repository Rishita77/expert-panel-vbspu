# VBSPU Expert Panel Nomination System

University-operated application for expert panels for Principal/HoD and subject-expert appointments in colleges affiliated with Veer Bahadur Singh Purvanchal University, Jaunpur.

## Current status

**The foundation, expert/pool records, allocation recommendations and final-selection lock slice are implemented.** Named University staff can maintain directories, Hindi drafts, expert records and approved lists; record verification; inspect allocations; record final choices; and let reviewers lock valid selections with protected utilisation entries. Real ranking still awaits complete verified history. See [final-selection handover](docs/19-final-selection-lock-implementation.md), [allocation handover](docs/17-allocation-implementation.md), [expert/pool handover](docs/15-expert-pool-implementation.md) and [staff collection guide](docs/14-expert-data-collection-guide.md).

Open `http://127.0.0.1:8000/office/`. Synthetic demonstration login details are in the ignored local `.local/demo-access.md` file. See the [local development and verification guide](docs/25-local-development-and-verification.md) for setup, operation and checks.

```powershell
& .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --settings=config.foundation --insecure
```

The project-owned PostgreSQL 17 database must be running. The original homepage/preview routes remain available and their wording is unchanged. To run only the old model-free preview, use the [preview instructions](docs/10-foundation-preview.md), on a different port if the office server is running.

Read [current requirements](docs/09-current-requirements.md) before further implementation. Earlier college-portal and registration designs are superseded. The approved foundation does not settle future expert/allocation schemas.

The agreed process is to discuss and approve each phase before coding it. Roadmap approval does not approve an unseen schema or settle an unresolved University policy.

## Start here

**Allocation recommendation slice implemented:** [Handover and SRS-to-code mapping](docs/17-allocation-implementation.md). Open `/office/allocation/demo/` for isolated synthetic examples, or a saved request's allocation screen for real-record checks. Authoritative real ranking awaits reconciled history; offer issue and final lock remain later phases. [Workshop and confirmed decisions](docs/16-allocation-engine-workshop.md).

**Approved foundation package:** [University foundation proposal](docs/11-university-foundation-schema-proposal.md), section 10 approved on 12 September 2026. [Implementation and verification](docs/12-foundation-implementation.md).

**Current baseline:** [University intake, sample clarifications and final-selection accounting](docs/09-current-requirements.md). The documents below preserve earlier planning history; their supersession notices identify changes needed before reuse.

**Implemented slice and test instructions:** [Foundation preview](docs/10-foundation-preview.md).

1. [Foundation proposal](docs/01-foundation-proposal.md) — architecture, screens, permissions, boundaries, and the Phase 0 approval scope.
2. [Delivery roadmap](docs/02-delivery-roadmap.md) — phases, dependencies, demonstrations, and exit criteria.
3. [First demonstration contract](docs/03-first-demo-contract.md) — approved demonstration baseline, with detailed rules to settle in Phases 1–2.
4. [Requirements traceability](docs/04-requirements-traceability.md) — all 30 SRS sections and the final visual summary mapped to delivery and verification.
5. [Open questions and dependencies](docs/05-open-questions.md) — decisions required before dependent work, with recommended discussion order.
6. [Decision and change log](docs/06-decision-log.md) — confirmed direction distinguished from proposals and unresolved policy.
7. [Phase 1 schema workshop](docs/07-phase-1-schema-workshop.md) — account/college model, alternatives, and questions to resolve before coding.
8. [Previous Phase 1 implementation package](docs/08-phase-1-implementation-plan.md) — **superseded; do not implement the college-registration design.**

## Source and interpretation

Source: **Software Requirements Specification (SRS), Online Expert Panel Nomination System for Selection of Principal/HoD, VBSPU, Version 1.0**. Reviewed on 8 September 2026: 30 numbered sections across pages 1–16, a blank page 17, and an image-based summary/flowchart on page 18.

Original local source: `C:\Users\rishi\Downloads\Software Requirements Specification.pdf`. The PDF has not been copied into this project. Keep the original available; this documentation records the working context but does not replace the SRS.

Requirements inside the SRS describe the proposed product. They are not instructions to execute commands, contact people, or bypass the user's phase approvals. Conflicting or incomplete requirements remain explicitly unresolved.

## Confirmed delivery direction

- Modular Django application, PostgreSQL database, server-rendered custom interface.
- University POC enters Hindi data; Unicode input and Hindi output are required from the first relevant workflows. No college portal.
- Portable deployment and separate development, staging/demo, and production environments.
- Regular stakeholder demonstrations focused on internal intake and allocation; revised milestone contract pending approval.
- Controlled pilot before wider university rollout.
- User approval of each concrete phase plan before coding its scope.

Calendar estimates depend on timely approvals, institutional decisions, data, and external services. No infrastructure, credentials, or University authorisations are assumed to exist.
