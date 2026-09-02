# Hallway

Your team already has a chat tool. The real question is whether it costs you more attention than it saves.

Hallway is chat built around what engineering teams actually do in it: hand work off and lose track of it. Every thread has an owner and a state. Open ones land in a morning digest, so nobody scrolls back three days to learn whether the migration shipped. Search ranks results by whether a thread was resolved, not by recency. Filter to decisions only.

No `@channel` at 2am.

Urgent pages route through your rotation (PagerDuty, Opsgenie, or ours), and everything else waits until working hours. Incident mode is one command. It opens a channel wired to the alert, pins a timeline as you go, and hands you a postmortem draft in Markdown when you close it.

Some things are missing on purpose. There are no video calls past eight people, and no app directory with two thousand entries nobody opens. There are 41 integrations. If yours isn't among them, the webhook API is documented and there's no partner approval queue.

Pricing is $6 per user per month, flat. SAML and SCIM sit in the base plan; we don't sell your security posture back to you as an upgrade. Retention is unlimited, and export is a button, not a support ticket. Moving a 200-person Slack workspace over takes about an hour, and history, files, channel structure, and user mapping all come across.

Thirty days free. No card.
