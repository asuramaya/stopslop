258 words, and it passes this repo's own slopwatch gate clean. Product name "Keel" is a placeholder — swap it. Draft is also at `/tmp/keel-copy.md`.

---

# Keel

**Team chat that doesn't cost you a day a week.**

Your team already has a chat tool. The real question is what it costs you: interruptions, the twenty minutes someone burns scrolling to find a decision, the on-call engineer who slept through a page because it looked like every other notification.

Keel is built around what engineering teams actually do — decide, ship, and respond.

**Decisions don't scroll away.** Pin any message as a decision and the thread that produced it comes along. New hires read the decision log instead of asking you.

**Incidents get their own room.** Page from the channel, and Keel opens a room, pulls the rotation from PagerDuty or Opsgenie, and writes the timeline as you go. When it's over you export a postmortem draft.

**Notifications have a hierarchy.** Four levels, not one. An @channel in #random cannot wake anyone at 3am. That's a rule, not a setting somebody forgets to turn on.

There is no AI summarizer, and we're not planning one. A channel too noisy to read is an organizational problem, and a robot recap just hides it from you.

Search covers everything from day one. We don't put message history behind a plan tier, and SSO, SCIM, and audit logs come with every paid seat. Self-hosting is there for teams who need the data inside their own VPC.

Importing a 200-person Slack workspace takes about an hour, channels and history intact.

$7 per user per month. Free under ten people.

[Start a workspace] · [Talk to us about migrating]

---

Two things to check before this ships: the migration time and the $7 price are invented placeholders, and the "no AI summarizer" stance is a real product commitment — keep it only if you mean it, since EMs will hold you to it.
