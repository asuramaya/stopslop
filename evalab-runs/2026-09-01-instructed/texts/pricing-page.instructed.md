# Pricing

Every plan runs the same review engine. What changes is how many repositories it watches and who can change the rules.

## Solo — free

One private repository, unlimited public ones. Reviews open on every pull request and comment inline on the diff. You get the default rule set: correctness bugs, unhandled errors, dead branches, and the dependency checks. History is kept for 30 days.

Good for a side project or for trying the thing before you ask anyone to pay for it.

## Team — $18 per developer per month

Unlimited repositories. Add your own rules in YAML, disable the checks that generate noise in your codebase, and require a passing review before merge. Reviews run against your project conventions once you point the tool at a style guide.

Also included: a weekly digest of what got flagged and what got ignored, so you can tell which rules earn their keep. Billing counts developers who opened a pull request that month, not seats on a license.

## Self-hosted — from $2,400 per month

Runs inside your network. Nothing leaves it. You supply the model endpoint, whether that is an internal deployment or a provider key you control.

Includes SSO through SAML or OIDC, audit logs of every review and override, and a named engineer for setup. Priced by repository count above 200, with a floor of $2,400. Annual contracts only.

Migration from Team keeps your custom rules and review history.

---

Questions about the middle tier are the ones we answer fastest. Email sales@ or start on Solo and upgrade when the free repository limit gets annoying.
