# Pricing

Every plan reviews pull requests the same way: full-repo context, inline comments, no diff-only guessing.

## Solo — $0

For one developer and public repositories. Unlimited reviews on public repos, one private repo, 200 reviews a month. Comments land within about 90 seconds of a push. You get the same analysis engine the paid tiers use; what you don't get is team-wide configuration or history beyond 30 days.

## Team — $18 per developer per month

For teams between 3 and 60 people. Unlimited private repositories, shared rule sets checked into your repo, and review history you can search back through the life of the account. Two things people upgrade for: custom rules written in plain language ("flag any new endpoint without a rate limit"), and the ability to block a merge when a review finds a defect above a severity you pick. Billing counts developers who actually opened a PR that month, so a quiet month costs less.

## Enterprise — talk to us

Self-hosted or VPC deployment, SAML and SCIM, audit logs exported to your SIEM, and a written data-handling agreement. We'll also tune the rule set against your existing codebase before rollout, which takes roughly two weeks and is included. Pricing starts at $30,000 a year and depends on repository count and deployment model.

## Common questions

Reviews are never used to train models. Deleted code is purged from our systems within 30 days.

Annual billing on Team saves two months. Switching between tiers is prorated, and downgrades keep your history read-only rather than deleting it.
