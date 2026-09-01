# From three weeks to twelve times a day: Kestrel Freight

Kestrel Freight builds routing software for European trucking fleets. Until last spring, it released once every three weeks, on a Thursday evening, with four engineers sitting on a rollback call.

The delay was not caution. Their test suite ran 90 minutes on a single shared machine, and failed often enough that a red build told nobody anything. Feature branches lived for weeks, and merging them was its own project. Two of the last four releases had to be backed out.

Kestrel moved to Northbound CD in March. The first month was mostly deletion. They cut 300 tests that asserted on implementation details, split the rest across parallel runners, and got the suite down to nine minutes. Per-branch preview environments meant product managers stopped queueing for staging.

"The part I did not expect was the arguments ending," says Petra Vos, their platform lead. "When a deploy costs ten minutes instead of an evening, nobody negotiates about whether a change is worth shipping."

Ten months in, they deploy 12 times a day, up from roughly one every 15 working days. Lead time from merge to production fell from 6 days to 40 minutes. Change failure rate went from 14% to 3%, mostly because a deploy now carries one change instead of three weeks of them.

Kestrel has not grown its platform team. The two engineers who used to maintain release scripts moved to the observability stack, and the Thursday call no longer exists.
