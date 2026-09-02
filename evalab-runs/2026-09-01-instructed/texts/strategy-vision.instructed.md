## Vision

Two years from now, a team that wants to ship a new service should be able to do it without talking to us first. Today that is not the case. Every new service starts with a copied Terraform module, a hand-edited CI pipeline, and a Slack thread where someone on platform explains why the copied module doesn't work anymore. We estimate that pattern costs each product team roughly three weeks of engineer time per service, and it costs us about a third of our on-call load.

The end state we are aiming at has three parts. A service template that produces a running, observable, deployable service in under an hour. A single deployment path that every service uses, so a change to rollout policy happens once instead of eleven times. And ownership boundaries that are legible from the code: if you can find the service, you can find who is paged for it.

None of this is new technology. It is mostly consolidation of things we already run, plus deleting the four deployment paths we no longer want to support. The hard part is not the build. It is that consolidation requires product teams to migrate, and migration competes with their roadmaps. We are budgeting for that explicitly rather than hoping teams find the time.

We will know this worked if two numbers move: time from empty repo to production traffic, currently about 19 days median, and the share of incidents whose root cause is infrastructure divergence between services, currently 41 percent of last year's Sev-2s. If those numbers are flat in 2028, the investment failed and we should say so.
