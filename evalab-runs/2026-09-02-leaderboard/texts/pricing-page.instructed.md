# Pricing

Every plan reviews pull requests on the diff, comments inline, and skips files you tell it to skip. The tiers differ in how much history the reviewer can see and who can change its rules.

## Solo — $12/month

One developer, unlimited private repos. Reviews run on the diff plus the files it touches. Comments arrive within about 90 seconds of a push. You get the default rule set: null handling, error swallowing, race conditions in async code, and the usual injection paths. Rules are read-only on this tier.

## Team — $29 per developer/month

Adds repository-wide context. The reviewer indexes your codebase, so it can tell you that the helper you just wrote already exists in `lib/dates.ts`, and it stops flagging patterns your team has deliberately standardized on.

You can write your own rules in plain English (`prefer our Result type over throwing in the api/ directory`) and scope them to paths. Review history is queryable — useful when someone asks why a rule exists six months later.

Includes GitHub, GitLab, and Bitbucket. SSO via Google or Okta.

## Enterprise — from $18,000/year

Self-hosted or in your VPC, so no source code leaves your network. SAML, SCIM provisioning, audit logs with 7-year retention, and a signed DPA.

Rules can be managed centrally and pushed to every repo, with per-team overrides. Includes a named support contact and a 4-hour response SLA on production issues.

All plans are free for public repositories and for the first 30 days. No card needed to start.
