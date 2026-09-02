**Nomination: Platform Delivery Team — Engineering Excellence Award**

I'm nominating the Platform Delivery Team for rebuilding how we ship code.

Eighteen months ago, a production deploy took four hours, required two engineers on a call, and failed often enough that we scheduled them for Thursday nights so Friday could be spent rolling back. Teams batched changes for weeks because deploying was painful, which made each deploy larger and riskier.

The team replaced that with a pipeline anyone can trigger from a merged pull request. They wrote the canary stage that catches bad builds at 5% of traffic, the automatic rollback that fires on error-rate regression, and the migration tooling that finally made schema changes routine. None of this was glamorous work. It meant months of untangling deploy scripts nobody had owned since 2019.

The numbers: median deploy time went from 4 hours to 11 minutes. Deploy frequency rose from roughly 6 per month to about 40 per week. Change failure rate dropped from 18% to 3%, and the two failures we had last quarter both rolled back automatically before anyone paged.

What I value most is that other teams now deploy without thinking about it. That's the mark of infrastructure done right, and this team earned it.
