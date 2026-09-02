# Pricing

Every plan reviews unlimited public repos. Pick a tier by how much private code you push through it.

Free — $0. For one person, or a weekend project. 200 reviewed pull requests a month, one private repo, review comments written on the diff. No card. If you're evaluating us, start here and don't talk to anyone.

Team — $19 per developer / month. Unlimited private repos, unlimited reviews. This is where the tool earns its keep. It reads your merged history and learns the conventions, so by week three it stops flagging the pattern your team settled on in 2021. Includes required-check status on PRs, custom rule packs, and Slack or Linear notifications. Billed monthly, cancel whenever. We don't do annual lock-in.

Enterprise — talk to us. Self-hosted or in your VPC, so source never leaves your network. SAML and SCIM, audit logs, per-repo policy, and a support channel with an engineer in it instead of a ticket queue. Contracts typically start around $30k a year; we quote against seat count and deployment shape.

Change tiers any time and it takes effect immediately, prorated. Free-tier reviews don't roll over. Students, nonprofits and OSS maintainers get Team at no cost — email us a link to the repo.

~230 words. Two things to check before you ship it. The numbers are placeholders (200 PRs, $19, $30k). And the "learns your conventions from merged history" claim in Team is the one line that has to be literally true of your product. If it isn't yet, cut it — an overclaim on the tier people actually pay for is the kind of thing that shows up in a churn interview six months later, long after anyone remembers who wrote the sentence. I ran the whole thing through this repo's own `slopwatch` ruleset; it passes clean.
