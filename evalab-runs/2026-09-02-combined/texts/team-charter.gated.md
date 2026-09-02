## Platform engineering charter

We exist so that product teams can spend their time on product.

Right now, every team writes its own deploy scripts, wires its own alerts, and files its own ticket to get a database. The duplication is expensive, and it is why standing up a new service takes about three weeks.

We own the paved road, by which we mean the default path from a commit to production. That covers CI, deployment, runtime infrastructure, observability plumbing, secrets, and the service catalog. We own the reliability of that road too, not just its existence. What we do not own is product code, and we do not carry the pager for services we did not write.

Our first-year commitments are narrow on purpose.

- Time from empty repo to a running service in production: three weeks down to one day.
- Eighty percent of production services on the standard pipeline.
- A published SLO for the pipeline itself, reported monthly, met or explained.

On how we intend to work. Internal teams are customers, not ticket queues; if a team routes around the paved road, that is our bug to fix, not their failure to comply. We make the standard path the easy path rather than mandating it.

Nothing ships without an escape hatch, because the teams doing the strangest work are often doing the most important work.

We will say no to bespoke infrastructure built for one team, to emergency work that belongs to a service owner, and to any request whose real fix is a conversation between two teams.

We will revisit this charter in six months and change whatever the evidence says to change.
