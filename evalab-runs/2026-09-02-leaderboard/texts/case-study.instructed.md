Northwind Logistics ships freight-tracking software to about 400 carriers. Two years ago they deployed on the second Tuesday of every month, at 11pm, with six engineers on a bridge call. Rollbacks happened roughly a third of the time.

They moved to a continuous delivery platform in March 2024. The migration took eleven weeks, and most of that time went to work the platform did not do for them: splitting a shared Postgres schema so services could deploy independently, and writing contract tests for the four internal APIs nobody had documented.

Now they deploy 30 to 45 times a week. The median change reaches production about 40 minutes after merge.

"The number we actually watch is time to restore," says Priya Raghunathan, who runs platform engineering there. "It used to be four hours because we had to reassemble the release. It's now under fifteen minutes, because a rollback is one commit."

Change failure rate went from 31 percent to 9 percent. Raghunathan attributes most of that to smaller batches rather than to any feature of the tooling: when a deploy contains one change, the cause of a failure is not in question.

Two things did not improve. Their end-to-end test suite still takes 22 minutes, which sets a floor on deploy latency they have not moved. And on-call load rose in the first quarter after the switch, before alert thresholds were retuned for a system that changed daily instead of monthly.

Northwind's next target is trunk-based development for the mobile client, which still runs on a two-week release train because of app store review.
