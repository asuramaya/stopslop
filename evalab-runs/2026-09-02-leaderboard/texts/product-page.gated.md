# Keel — chat for teams that ship

Your team already has a chat tool. The question is whether it's costing you an hour a day.

Keel is built around threads that don't die. Every message lives in one, and a thread carries its own state: open, blocked, done. When someone asks "did that deploy ever finish," they scroll one thread instead of reconstructing a channel from three months of scattered replies.

Search works on the first try. Full text across messages, files, and code snippets, with filters on author, repo, and date. Median query returns in under 200 ms on a workspace of four million messages.

Incidents get a room and a record. Type `/incident` and Keel opens a channel, pages the on-call rotation from PagerDuty, and starts a timeline. Close it and you get a Markdown postmortem draft with the timestamps already filled in — who decided what, and when.

We left things out on purpose. No stories, no reactions leaderboard, no AI summary of a nine-message conversation you can read in twenty seconds.

The things procurement will ask you about: SAML and SCIM on every paid plan, not only enterprise. Data export as JSONL, no support ticket required. Self-host against your own Postgres if your security team insists. SOC 2 Type II, report under NDA.

Migration from Slack runs about two hours for a 200-person workspace, history included. We do it with you on a call.

Free for 30 days. $6 per user per month after that.

Worth flagging that every number in there is invented, from the 200 ms and the four million messages to the two-hour migration, the $6 seat price, and the SOC 2 status. The copy leans on specifics rather than adjectives on purpose, which is what makes it read like a person wrote it, but that only works if the specifics are true. Swap in your real ones before this ships.
