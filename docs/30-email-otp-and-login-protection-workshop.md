# Email OTP and login protection

Status: **deferred on 22 September 2026.** The code remains isolated behind
`EMAIL_OTP_ENABLED`, which is forced off in the current Railway deployment.
The active login protection is password throttling plus Cloudflare Turnstile.
Gmail API OAuth 2.0 is retained only as a future option; it must not be
configured or presented as an active control.

## Objective

Require two steps for every University staff login:

1. Username and password.
2. A six-digit verification code sent to the account's registered official email address.

Add Cloudflare Turnstile to reduce automated password-guessing attempts. It supplements, rather than replaces, the existing login-attempt throttling.

## Approved direction to implement after this workshop

- Use email OTP, not SMS or an authenticator application.
- Use Cloudflare Turnstile in Managed mode on every production login. It is normally invisible and presents a checkbox only when risk signals require one.
- Keep the existing five username attempts and thirty IP attempts per fifteen minutes. Turnstile is an additional bot check, not a replacement.
- Do not send passwords by email. The email contains only the short-lived OTP.
- No college accounts or external public access are introduced.

## Email OTP login journey

1. Staff enter username and password on the University login page.
2. The system checks the password, account activity, and the account's registered email address. It does **not** create an authenticated session yet.
3. It creates a pending sign-in challenge, stores only a salted hash of a newly generated six-digit code, and sends that code to the registered email address.
4. The staff member enters the code on a second screen. A correct code completes the login; an incorrect, expired, or consumed code does not reveal account details.
5. If the account has a temporary password, the existing compulsory password-change screen follows the OTP check.

The code expires after **10 minutes**, can be used once, and has at most **five verification attempts**. A resend invalidates the earlier code. Send attempts are limited to **three per account per hour** and count toward the existing IP throttle.

## Account and recovery rules

- An active account must have a non-empty official email address before it can use email OTP.
- New accounts remain inactive until an Admin has assigned roles, issued credentials, recorded an official email address, and explicitly activated the account.
- Existing active accounts without an email stay usable only until the email-OTP rollout date. At that date, they must be updated by an Admin before the next login.
- If a staff member cannot access their registered email, an Admin verifies the person through the University’s offline process, updates the email with a reason, and issues/reset credentials if required. The application does not offer email-link account recovery.
- Admin changing another user's email or password requires the Admin’s own current password and a reason. The target's active session is invalidated on the next request.

## Data design

Add a small, expiring `EmailLoginChallenge` record:

| Field | Purpose |
|---|---|
| Staff account | The intended account. |
| OTP hash | A salted one-way hash; never the readable code. |
| Expires at | Ten-minute expiry. |
| Attempts remaining / consumed at | Enforces one-time use and five-attempt limit. |
| Request IP hash | Supports rate controls without retaining an unnecessary readable IP in this record. |
| Created and sent timestamps | Supports expiry and resend controls. |

The database does not store the readable OTP, password, Gmail OAuth client secret, refresh token, or Turnstile secret. Those credentials remain deployment environment secrets.

## Email delivery boundary

Use Gmail's API through OAuth 2.0. The dedicated sender is `emailadmin.vbspu@gmail.com`. The application asks only for Gmail's `gmail.send` permission, then creates short-lived access tokens from a revocable refresh token. It never stores or uses the Gmail account's normal password or an App Password.

The application uses `emailadmin.vbspu@gmail.com` as the sender. Local development uses a safe console-only provider unless Gmail API delivery is explicitly enabled; it never sends messages externally by default.

For the one-time sender authorisation, create an OAuth **Desktop app** in the Google Cloud project, download its client JSON to `.local/gmail-oauth-client.json`, and run `manage.py authorize_gmail_sender --settings=config.foundation`. The command opens the Google consent screen locally and writes the refresh token only to `.local/gmail-oauth-refresh-token.json`. Copy that value into Railway's secret settings, then remove the local token file when it is no longer needed.

Email delivery is recorded as sent or failed without storing the code. A failed delivery allows a controlled resend and never completes sign-in.

## Turnstile CAPTCHA

Cloudflare Turnstile's Free plan permits up to 20 widgets and unlimited verification requests, sufficient for this single login page. It can be used without moving the website's DNS or hosting through Cloudflare.

Implementation:

- Embed one Managed-mode Turnstile widget on the login form.
- Pass the browser token to the Django login view.
- Validate that token server-side with Cloudflare before checking a password.
- Keep the site key public in the page and store the Turnstile secret only in deployment configuration.
- Enable it in Railway through environment settings; use Cloudflare's documented test keys locally.

If Turnstile is unavailable, production login fails closed with a short retry message. Local development stays explicitly configured with test keys or the feature disabled; it must never silently run production without server validation.

## Screens and roles

| Screen | Access | Purpose |
|---|---|---|
| Login | Unauthenticated staff | Password, Turnstile, then OTP request. |
| Verify email code | Pending sign-in only | Enter or resend one-time code. |
| Account record | Admin | Maintain official email through the existing staff-account workflow. |
| Credential issue/reset | Admin | Continues existing temporary password procedure. |

No role has access to another person's OTP, email code, or email-delivery secrets.

## Audit and privacy

Record account email changes, OTP issued, verification succeeded, verification failed, code expired, resend limit reached, and credential recovery action. Audit records identify the staff account and action time but contain no code, password, or authentication secret.

## Acceptance evidence

1. A correct password alone cannot reach any University workspace.
2. The correct email OTP completes login once; reuse and expiry are rejected.
3. Password change required still blocks operational pages after OTP succeeds.
4. A POC, Reviewer, VC, or Master-data user cannot alter another account's email, credentials, or OTP records.
5. A wrong code, resend limit, and login throttle do not disclose whether an account exists.
6. Turnstile is server-validated; a forged, expired, or reused token cannot pass login.
7. Failed email delivery never creates an authenticated session.
8. Audit records contain no readable password, OTP, or provider secret.

## External items needed before production activation

- A Google Cloud project owned by `emailadmin.vbspu@gmail.com`, with Gmail API enabled and an OAuth consent screen published as “In Production”.
- OAuth client ID, client secret, and the dedicated sender's `gmail.send` refresh token held only in Railway environment settings.
- A project-operator-controlled Cloudflare account, plus the production hostname and Turnstile keys. Control can be transferred to the University later without changing the login flow.
- The date when email OTP becomes mandatory for existing staff accounts that currently have no email address.
