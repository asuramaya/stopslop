Note: no real customer was specified, so this is a fictional case study with placeholder specifics. Swap in your own name, quotes, and numbers.

---

**Meridian Freight went from nine releases a year to 340**

Meridian Freight runs load-matching software for about 4,000 regional carriers. For years, shipping a change meant a Thursday-night window, a checklist in a shared doc, and two engineers on standby in case the rollback went sideways. Releases went out every six weeks. Sometimes seven.

"We weren't slow because the code was hard," says Dana Okonjo, who runs platform engineering there. "We were slow because nobody wanted to be the person who broke dispatch on a Thursday night."

They moved to [Platform] in March 2025 and started with the two least frightening services: an internal admin tool and the carrier onboarding API. Pipeline templates replaced the checklist. Every merge to main now builds, runs the test suite, and lands in staging without anyone touching a terminal. Production still requires a human click, and Okonjo has no plans to remove it.

Nine months in, they had shipped 340 production deploys, against 9 in the same stretch the year before. Median time from merge to production dropped from 38 days to just under 4 hours. The change-failure rate fell from 18% to 6%, mostly because each change got smaller.

The cultural shift caught them off guard. Engineers stopped batching work. A one-line copy fix used to wait for the next train, so nobody bothered filing one; now it ships the same afternoon and the tickets show up.

Meridian has 31 of its 44 services on the platform today. The remaining 13 are stuck behind a Java 8 upgrade.
