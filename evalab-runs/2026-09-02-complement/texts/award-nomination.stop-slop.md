I nominate the Delivery Platform team for the Engineering Excellence Award.

In January a release took 47 minutes and pulled two engineers off other work to watch dashboards. A rollback meant calling Priya and hand-editing a config file. Teams shipped on Tuesday afternoons to avoid a Friday page.

Marcus, Dana, and Wei rebuilt the pipeline over two quarters. They cut the build to nine minutes by caching dependencies at the layer that changes least. They wrote the canary controller that watches error rates for ten minutes and reverts without waking anyone. They deleted 4,000 lines of shell that four teams had each copied and edited on their own.

Deploys per week went from 11 to 140. Median time from merge to production dropped from three days to 22 minutes. Change failure rate fell by half, and the two bad deploys we did have were back to a good version in under five minutes, because the rollback path works now.

They taught the rest of us too. Wei ran four office-hour sessions for teams moving onto the new pipeline. Dana wrote the runbook our new hires read in their first week.

I have not been paged for a broken deploy since March, and neither has anyone else on my team.
