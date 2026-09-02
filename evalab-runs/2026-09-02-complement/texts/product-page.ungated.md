Passes the repo's own gate (`slopwatch`: PASS, 2 non-blocking notes; `codewatch`: clean). Product name and numbers are placeholders — swap in real ones.

---

# Hallway

Chat that's still useful in six months.

Most team chat tools are built for the people who enjoy chat. Hallway is built for whoever has to reconstruct, in March, why the team picked Postgres back in October.

Threads are the unit, not the channel. A reply lands inside its parent and stays there. Decisions get pinned to a short doc that lives beside the thread and updates when someone edits it, so the answer isn't 400 messages upstream.

Search covers everything back to day one, and returns in under 200 ms on a four-million-message workspace. No paywalled history tier. We tried that pricing and hated it.

What engineering managers ask about first:

- SSO, SCIM, and audit log export on every paid plan. Not the enterprise tier. Every plan.
- Retention set per channel, so #incidents keeps seven years and #random keeps thirty days.
- Self-hosting against your own Postgres and S3 bucket, from the same binary we run.
- Outbound webhooks and a documented API; 40 ms p99 on message POST.
- Migration from Slack or Teams that carries threads and files across. We run it. Two days for a 300-person org.

Six dollars per person per month. Integrations don't cost extra and neither do guests.

Where we're weak: voice and video are basic, and the mobile app is a year younger than the desktop one. If your team lives in huddles, we aren't the pick yet. If your team lives in threads and has to answer for its decisions later, book 20 minutes and bring your hardest question.

---

262 words. The bet it makes: managers comparing tools have already read three pages of adjectives, so the copy leads with a concrete failure mode, names prices and latencies, and admits a weakness — the admission is what makes the rest credible. Draft is at `/tmp/hallway.md` if you want it edited in place.
