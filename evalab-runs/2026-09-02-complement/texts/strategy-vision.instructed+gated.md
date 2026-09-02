## Vision

Two years from now, a team that wants to ship a new service should be able to do it without talking to us.

Today that path runs through four hand-offs: a ticket for a cluster namespace, a ticket for secrets, a review of the Terraform someone copied from a neighbouring repo, and a week of waiting for the first deploy to go green. We estimate the median new service takes 19 working days from first commit to production traffic. We want that under three. The platform is the mechanism. Not a portal or a wrapper, but a set of paved paths that carry the operational defaults with them: a service template that already has health checks, tracing, alert routing and a rollback lever wired up, so those become properties of the platform rather than things each team remembers or forgets.

That shifts what our group is for. We stop being the queue that every infrastructure change waits in and become the group that owns the defaults everyone inherits. Fewer tickets, more leverage per change, and a clearer answer when something breaks at 3am, because the failure modes are ones we designed rather than ones that accumulated.

We are explicit about the cost. Platform work does not show up in a quarterly product review, and for the first three quarters it will look like we shipped nothing customers can see. The payoff lands when the fourth team onto the paved path spends days instead of weeks, and every team after that pays less again.
