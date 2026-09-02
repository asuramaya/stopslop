## Vision

In two years, a team that wants to ship a new service should not have to make thirty decisions that have already been made thirty times. Today the median time from "we agreed to build this" to "it serves traffic in production" is eleven weeks, and roughly seven of those weeks go to work no product team should be doing: wiring auth, standing up CI, arguing about deploy topology, discovering that the metrics pipeline expects a schema nobody documented.

We want that number under two weeks, and we want the reduction to come from removing steps rather than from asking people to move faster.

The platform we are describing is opinionated. It picks one way to deploy, one way to emit telemetry, one way to store secrets, and it makes those paths the cheapest ones to take. Teams that need to leave the paved road can, but they will own what they build, and that trade should be visible at the time they make it rather than discovered during an incident eighteen months later.

This is a bet about where our engineering hours go. We currently spend an estimated 35 percent of senior engineering time on infrastructure work that is duplicated across teams. Recovering even half of that is worth more than any single roadmap item we have queued.

Success looks boring. There are fewer bespoke Terraform modules, fewer one-off runbooks, and fewer incidents whose root cause is a config difference between two services that were supposed to be identical. If the platform is working, most engineers will rarely think about it.
