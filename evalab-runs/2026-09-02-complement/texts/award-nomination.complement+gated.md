Nomination for the Engineering Excellence Award, Release Engineering

I am nominating the Release Engineering team for their work rebuilding how we ship to production.

A year ago, a deploy took four hours of babysitting, ran only on Tuesday and Thursday afternoons, and required a designated person to stay online in case a rollback was needed. Nobody enjoyed it, and most teams batched two weeks of changes into a single release because the process was painful enough to avoid.

The team replaced that with a pipeline anyone on call can run. Deploys are now roughly nine minutes, they run on demand, and a rollback is one command that finishes before the alert page clears. Change failure rate dropped from about 12% to under 3% over two quarters, and deploy frequency went from twice a week to roughly forty times.

What I want to highlight is how they did it. They spent the first six weeks interviewing the teams who would use the pipeline, then shipped it in stages so nobody had to migrate on a deadline. They wrote the documentation themselves and answered questions in the support channel for months after launch.

They made a job everyone dreaded into something people barely think about.
