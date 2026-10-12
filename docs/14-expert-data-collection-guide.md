# Expert and approved-list data collection

Approved expert/list schema, 12 September 2026. This guide is for University staff preparing records; operational nomination rules are not changed by data collection.

## What staff should gather

Keep one row per person in the expert list. A person who is both Principal and Professor must not be duplicated. Record the current post and academic rank separately in their institution/post information. Multiple approved duties are represented as memberships linked to that same person.

| Group | Information to collect |
|---|---|
| Expert collection row | A unique collection reference chosen for the sheet; full name; current institution name; General/OBC/SC/ST category if verified; mobile and email if available; subjects; current post and verified academic rank |
| Institution/post | Existing institution identity; Principal/Professor/Assistant Professor/Other post; Professor/Assistant Professor/Other/Unknown academic rank; known start/end dates; whether current; verified internal/external classification; evidence/reference |
| Approval document | Authority name, EC/other authority type, official reference, approval date and source description |
| Candidate list | Title, nominee role, approval reference, effective date, prescribed valid-through date or explicit verification that no end date was prescribed |
| List applicability | Principal/HoD/subject-expert appointment type and approved subject, or explicitly approved all-subject applicability |
| Membership | Existing expert identity, candidate-list version, any additional approval, individually prescribed validity dates, active/withdrawn status and withdrawal reason |

One current institution per complete expert. An external university can be the institution. Previous affiliations belong in history; do not overwrite the person or give them a new identity on transfer. The removed **college affiliation-details** field is not needed.

Do not guess category, academic rank, dates or internal/external status. Blank/unknown information is allowed during preparation and is shown as incomplete. A Principal title alone does not verify Professor rank. Assistant Professors are supported for the permitted category supplement, not automatically for main Professor/VC roles.

English and Unicode Hindi are both accepted. Keep official spelling as supplied. Translation/transliteration remains a separately reviewed activity; there is no automatic conversion in this release. Phone numbers are text, preserving country codes and leading zeroes.

### Single sheet for staff collection

**Include the current institution beside every expert's name.** Staff can collect identity and current institution/post together in one sheet using these headings:

`source_key,name,institution_name,category,mobile,email,subjects,designation,academic_rank,classification,verification_reference,status`

Use institution and subject names as supplied; the university maintainer maps these to existing directory identities before entry/import. No employee ID is required. `source_key` is only the unique collection-row reference, not the allocation sequence. Record retired/transferred status explicitly: these mean permanently inactive under DEC-037; no transfer-document upload is mandatory.

This is the staff collection sheet, **not a directly uploadable CSV format**. The current import preview separates identity from institution/post history as shown below. That separation preserves institution history without duplicating the expert. Do not omit institution from collection merely because it is stored in a separate record internally.

## Sequence and history

The system assigns a permanent sequence when a person is created. Do not enter arbitrary sequence numbers in collection files. Creating multiple memberships does not create new sequences. Any pre-existing University-prescribed sequence must be reviewed before importing it; it must not silently be replaced by collection order.

CSV preview shows proposed relative creation order, not reserved sequence numbers. Actual sequence values may contain gaps and may change between preview and a future commit if other experts are created.

Do not supply editable utilisation totals as expert master fields. Annual/lifetime counts and last nomination show **history not loaded** until the opening-history and accounting phase is approved. Offers alone will not increase the common count.

## Downloadable CSV formats

Sign in with directory-maintenance permission and open **Experts → Data import check** at `/office/catalog/import/`. Download the required format and the existing-name/identity mapping. Templates contain headers only; the mapping contains no mobile or email information.

Keep headers unchanged. Save as UTF-8 CSV (UTF-8 BOM is supported), with no merged cells. Maximum upload size is 1 MB and 1,500 data rows. Use `YYYY-MM-DD` dates and lowercase `true` / `false` values.

The collection guide above can be used by staff in their own sheet. The CSV identifiers below are for the maintainer's controlled mapping step; staff need not invent UUIDs. A missing or ambiguous identity requires review; names are never matched fuzzily or merged automatically.

| Template | Exact columns |
|---|---|
| Expert identity only — institution is in the next linked CSV | `source_key,name,category,mobile,email,subject_ids` |
| Institution/post history | `expert_sequence,institution_id,designation,academic_rank,classification,evidence,start_date,end_date,is_current` |
| Approvals | `authority,authority_type,reference,approval_date,source_description` |
| Candidate lists | `title,nominee_role,approval_id,effective_date,valid_through,no_end_prescribed` |
| List scope | `pool_id,appointment_type,subject_id,all_subjects` |
| Memberships | `pool_id,expert_sequence,approval_id,valid_from,valid_through,is_active,withdrawal_reason` |

Values:

- `category`: `general`, `obc`, `sc`, `st`, or blank when unknown.
- `designation`: `principal`, `professor`, `assistant`, `other`.
- `academic_rank`: `professor`, `assistant`, `other`, `unknown`.
- `classification`: `internal`, `external`, `unverified`. Verified rank/classification requires the evidence reference.
- `authority_type`: `ec`, `other`. Record the actual approval authority; do not invent EC approval for another source.
- `nominee_role`: `principal`, `professor`, `scst`, `obc`, `vc`.
- `appointment_type`: `principal`, `hod`, `subject_expert`.
- `subject_ids`: existing subject UUIDs separated by `|`. `institution_id`, `approval_id`, `pool_id` and `subject_id` use the matching record IDs from the mapping download.
- `expert_sequence`: the existing expert's permanent sequence, used to resolve memberships/history. Newly collected experts must first acquire system identities through the later reviewed commit process or current manual entry.

Employment start is included and end is excluded. For example, an appointment ending `2026-10-01` is no longer in force on that day. List/membership valid-through dates include the stated day. Missing historical dates stay unknown. A current appointment has no end date. For pool validity, blank end date alone is incomplete; `no_end_prescribed=true` records explicit verification that no end date was prescribed.

## What the preview does

It reports invalid headers/encoding, dates, values, lengths, duplicate row keys, unresolved references, conflicting current institutions/scopes and selected approval/membership contradictions. It preserves the supplied row text for review. Rows without reported errors are **not saved** and do not establish operational nomination eligibility.

There is no import commit button, direct Google Sheets connection, bulk update or automatic identity creation from these files yet. The actual commit, rollback and historical-data import design will be reviewed after the source data is available. Manual expert/list entry is available now.
