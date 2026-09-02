# Platform Engineering — Team Charter

## Why we exist

Product teams spend too much of their week on work that isn't their product: wiring up CI, chasing deploy failures, guessing at the right Terraform module, waiting on someone in another channel to grant access. We exist to absorb that work once, so it doesn't get re-solved fifteen times a year.

## What we own

The paved road from a commit to production traffic: build and CI infrastructure, deployment tooling, environment provisioning, observability defaults, and the internal documentation that makes all of it discoverable. We own these as products with users, not as infrastructure we happen to babysit.

## How we work

We treat other engineers as customers, which means we do discovery before we build. A new platform capability starts with two or three teams who have the problem now, not with a roadmap item.

We make the paved road optional and obviously better. Teams can go around us; if enough of them do, that's our bug, not theirs.

We prefer deleting a step over documenting it.

## What we don't do

We are not a ticket queue for one-off infrastructure requests, and we are not on the critical path for routine changes. If a request only ever helps one team, we help them do it themselves and write down how.

## How we'll know it's working

Time from first commit to first deploy for a new service. Change failure rate. The share of teams on the paved road by choice. We publish these quarterly, including when they get worse.

*Reviewed every six months. Anyone can propose an amendment.*
