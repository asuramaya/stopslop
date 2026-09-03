**Who to ask for what**

- **Local environment / sandbox access issues** — ask your onboarding buddy first; they set up the same thing two weeks ago.
- **Ledger and reconciliation logic** — ask the ledger service owner (see `CODEOWNERS`); this is the module most people misread on first pass.
- **Processor integration questions (Stripe, Adyen)** — ask whoever's on payments integration rotation that week; check the team calendar.
- **Production incidents or anything that smells like a live money issue** — page on-call directly, don't wait for a Discord reply.
- **Access requests (prod, vault secrets, processor dashboards)** — file through the access-request bot in `#payments-team` on Discord; approvals need a manager sign-off.
- **"Is this idempotent enough" or design review** — bring it to the team's weekly design review, or ping the tech lead directly if it's blocking you.
- **General "who do I even ask"** — your onboarding buddy is the default answer; they'd rather field a dumb question than have you guess on a payments code path.

**On-call**

The team runs a weekly on-call rotation, one engineer at a time, visible on the team calendar. You won't be added to the rotation until you've shipped a few changes and finished shadowing at least one on-call shift with a current rotation member. Until then, if you're ever unsure whether something is on-call-worthy, treat it as if it is and page — nobody on this team will fault you for a page that turns out to be nothing.
