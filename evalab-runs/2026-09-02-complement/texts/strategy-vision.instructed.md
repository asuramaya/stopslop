## Vision

Two years from now, a team that wants to ship a service should be able to do it without a platform engineer in the room. Today that is not true. Every new service costs us somewhere between three and six weeks of setup work before a line of product code runs, and most of that time goes into rediscovering decisions other teams already made: how to wire authentication, which deploy pipeline is current, what the on-call rotation expects from a health endpoint.

We want to replace that rediscovery with defaults. A generated service should come with deploys, metrics, logging, secrets handling, and a working staging environment already attached, and the team should be able to walk away from any of those defaults when they have a reason to.

The measurable form of this is time from repository creation to first production request. It is currently 22 days at the median across the last eleven services. We are targeting three days by the end of FY28, with no increase in change-failure rate.

There is a second thing we care about that is harder to count. Platform work compounds when it is boring and stable, and it decays fast when each team patches around it. So the work here includes deleting the four internal deploy paths we currently maintain, not only building the fifth. We expect the first year to feel slower than the status quo, because consolidation costs more than it returns until the last team moves off the old path.

If we are right, the second year pays for both.
