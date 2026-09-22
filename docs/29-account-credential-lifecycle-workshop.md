# Staff account credential lifecycle

Status: implemented on 21 September 2026. The account database migration is applied locally.

## Purpose

Replace the local command-line password setup with a university-administered account lifecycle suitable for production deployment. Passwords must never be displayed after initial handover, recorded in audit history, included in exports, or sent through the application in plain text.

This applies to the named VC account (`vc_vbpsu`) and every future University staff account. It does not create college accounts or change business-role permissions.

## Proposed user journey

### 1. Admin creates a named staff account

The existing staff form continues to collect name, username, email (optional), active state and roles. A newly created account remains inactive and has no usable password.

The Admin then opens **Credentials** for that account and chooses one of two actions:

- **Generate a temporary password**: the system creates a strong random password and displays it once on a no-cache confirmation page.
- **Set a temporary password**: the Admin enters a temporary password which must satisfy the existing Django password policy.

The Admin records a required provisioning/reset reason. The password is handed to the staff member outside the system, for example in person or through an approved University communication channel. The application does not email or store the plaintext password.

On successful provisioning, the account becomes active only if the Admin explicitly selects activation. The account is flagged **password change required**.

### 2. Staff member signs in for the first time

After a successful temporary-password login, the application sends the staff member directly to **Set your password**. Until that succeeds, every operational URL redirects there; sign-out remains available.

The staff member chooses a new password, with confirmation and the current Django password validators. On success, the temporary-password status and expiry are cleared, the session remains valid, and the normal role dashboard opens.

### 3. Staff member changes their own password later

Every signed-in account has an **Account / Change password** option. The user supplies the current password and a new confirmed password. This action is available to every active staff member, including Admins and the VC.

### 4. Admin resets a password

An Admin opens a named staff account and uses **Reset credentials**. The same generated-or-entered temporary password workflow applies.

Resetting a password does not change roles. It does not reactivate an inactive account unless the Admin explicitly selects activation. Changing the stored password invalidates the target account's existing sessions at their next request, and the target must choose a new password after login.

For a privileged action, the Admin must confirm their own current password and provide a reason. This reduces the risk of someone using an unattended Admin session to take over another account.

## Proposed data changes

Add the following non-sensitive fields to `StaffUser`:

| Field | Meaning |
|---|---|
| `must_change_password` | Whether the account is restricted to password change after sign-in. |
| `temporary_password_expires_at` | The deadline for the current temporary password; empty for a normal password. |
| `password_changed_at` | Time of the last completed password change or Admin credential issue. |

The existing Django `password` hash remains the only password storage. There is no plaintext password field, reset-token table, email token, recovery question, or password visible in audit records.

The proposed temporary-password lifetime is **48 hours**. On expiry, login is blocked and an Admin must issue a fresh temporary password. This is a configurable production setting rather than a hard-coded University policy.

## Routes and screens

| Screen | Who can use it | Purpose |
|---|---|---|
| Account password change | Signed-in staff | Change own password; fulfils first-login requirement. |
| Credential issue/reset | Admin | Generate or set a temporary password, activate if intended, record reason. |
| One-time credential handover | Admin | Displays generated password once, with no-store headers. |
| Expired credential notice | Unauthenticated staff | Explains that an Admin must reset the password. |

The current Admin staff-record form remains responsible for roles, activation and ordinary account details. Credential controls are deliberately separate so a role edit cannot accidentally reveal or replace a password.

## Security and audit rules

- Password forms use CSRF protection, no-cache response headers and password inputs.
- Login throttling remains in force. The app does not reveal whether a username exists or whether a temporary credential expired.
- Every issue, reset, expiry, successful self-change and failed privileged reset is recorded with actor, target account, timestamp and reason. Audit data never includes a password, password hash, generated value or entered value.
- An inactive account cannot authenticate. A temporary-password account cannot access application work until it has changed its password.
- Deactivating a staff account remains separate from credential reset and retains its business/audit history.
- Existing local management commands remain emergency/bootstrap tools only; production staff administration uses the web flow.
- Production deployment adds HTTPS-only secure cookies and privileged-account MFA as a separate readiness item. MFA is not silently claimed by this password feature.

## Migration and existing accounts

Existing active accounts keep their current usable passwords and are not forced to reset during migration. Accounts without usable passwords, including `vc_vbpsu`, remain inactive until an Admin issues credentials through the new screen.

The migration defaults `must_change_password=False` and leaves expiry empty. No roles, audit history, requests, nominations or documents are changed.

## Acceptance evidence

1. Admin provisions the inactive VC account, copies a one-time temporary password, and activates it.
2. VC signs in and is forced to choose a new password before viewing the dashboard or proposed panels.
3. VC can access only VC-authorised screens after completing the change.
4. Admin resets the VC password without altering its VC role; the old password no longer works and the next login requires a new private password.
5. An expired temporary password is denied without revealing account detail.
6. POC, Reviewer and VC cannot access another account's credential-reset URL.
7. Audit records show the credential action and reason but never password material.
8. Existing active accounts continue working after the migration.

## Deferred decisions and dependencies

- Email/SMS password delivery and forgotten-password self-service require an approved University communication service and are not part of this proposal.
- MFA method, identity-provider/SSO integration, credential retention policy and emergency break-glass administration remain production-readiness decisions.
- The proposed 48-hour temporary-password lifetime should be confirmed by University IT before production deployment.

