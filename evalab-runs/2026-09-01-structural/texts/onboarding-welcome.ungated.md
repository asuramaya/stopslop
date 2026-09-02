Clean through the repo's own slopwatch gate. ~270 words:

---

## Day one

Somebody already set up your laptop. The password is on the sticky note under the keyboard, and yes, you should change it before lunch.

First job: get `main` running locally. The README in `platform/` walks you through it, and it will fail somewhere around step 4 — it always does, for everyone, and we've stopped pretending otherwise. When it fails, ask in #dev-help. That's the whole test. We'd rather you burned ten minutes and a question than three hours and your patience.

Second: ship something. Anything. A typo fix in the docs counts. Most people get a commit into production before Friday, and the point isn't the commit — it's that you've now touched every part of the pipeline that matters: review, CI, deploy, rollback.

A few things nobody says out loud, so we'll write them down:

- You are not expected to understand the billing service. Nobody understands the billing service.
- Meetings without an agenda are optional. Decline them.
- If you break production, say so immediately and loudly. We've all done it. The postmortem asks what the system let you do, not what you did.
- Your first six weeks are for reading code and asking questions. Any pressure to be "productive" sooner is coming from you, not from us.

Your onboarding buddy is **[name]**. They've blocked out an hour each afternoon this week; use it or don't, but they'll keep showing up.

Coffee's on the second floor. The good stuff is in the cupboard, not the machine.

---

Swap the placeholders for your real ones — `platform/`, `#dev-help`, the buddy's name, and the billing-service joke should point at whichever service your team actually dreads. The specifics are what make it not read like a template.
