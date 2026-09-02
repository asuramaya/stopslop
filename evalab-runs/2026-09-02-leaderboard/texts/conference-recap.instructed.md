# What we brought back from SIGCONF

Six of us went to SIGCONF last week. Here's what stuck, minus the stuff you can read in anyone's slide deck.

The keynote on incident response was fine but not why we're writing this. The hallway conversation afterward was. An SRE from a payments company told us they'd stopped paging on error-rate thresholds entirely and moved to paging on customer-visible symptoms only. Their on-call volume dropped from about 40 pages a week to 9. We've been arguing about alert fatigue for two quarters without anyone proposing something that concrete.

Second thing: three separate teams, unprompted, described abandoning a shared monorepo test suite because CI times had crossed 45 minutes and people started skipping it. All three landed on per-package test gates. We're at 31 minutes and climbing, so this is a warning we should probably act on before it becomes a migration.

The vendor floor was mostly noise. Two exceptions worth a demo: a tracing tool that handles async boundaries better than what we run now, and a schema-diff service that we're skeptical about but that solves a problem we've hand-rolled twice.

What we got wrong going in: we split up to cover more sessions. That meant nobody had a second opinion on anything, and half our notes are one person's read on a talk. Next time we send pairs to the tracks that matter and skip the rest.

Ana is writing up the alerting change as a proposal for the platform sync on the 15th.
