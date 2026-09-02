243 words, and it passes this repo's own `slopwatch` gate clean.

---

# Halyard

Your team already has a chat tool. The question is whether it costs you more than it saves.

Most chat apps are built for the whole company, so engineering gets whatever is left over: threads that collapse after a day, a search box that cannot find the outage postmortem from March, and an integrations directory nobody has audited since 2019.

Halyard is built narrow. Threads never expire and never collapse, so a design review from two years ago opens with the context it had the day it closed. Search covers message bodies, code blocks, file contents and thread titles, and returns in under 200 ms on a workspace of 4 million messages.

**Incidents.** Type `/incident` and Halyard opens a channel, pins the timeline, and records who said what and when. When it is over you get a Markdown timeline to paste into the postmortem. No bot subscription. No second vendor.

**What your procurement team will ask about.** SOC 2 Type II. SAML and SCIM on every plan, including the cheap one. Self-hosting against your own Postgres. A documented export format, JSON rather than a ZIP of screenshots, so leaving costs you an afternoon instead of a quarter.

**Pricing.** $6 per person per month. Bots and service accounts are free. No per-integration fees.

We do not do stories, huddles, or an assistant that summarizes conversations you should have read.

Import from Slack or Discord takes about an hour for a 200-person workspace.

---

The name and every number are placeholders — swap in your real latency, message ceiling, price, and compliance list. The structure assumes managers are buying on three things: search that survives turnover, an exit path, and a bill they can defend. If your differentiator is elsewhere, tell me and I'll re-aim the middle three blocks. Draft is at `/tmp/halyard.md` if you want it linted again after edits.
