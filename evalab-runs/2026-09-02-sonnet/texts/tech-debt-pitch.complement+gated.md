Requesting one quarter of dedicated time for technical debt

Team,

I'd like to allocate one quarter, roughly one engineer-quarter of capacity spread across the team, to pay down technical debt before it slows the next round of feature work.

Three areas need attention. The payments module still runs on the pre-2024 retry logic, which caused two of our last four production incidents. Our test suite takes 40 minutes to run, up from 12 minutes a year ago, which means engineers skip it locally and catch failures in CI instead. And the API gateway has three different auth patterns depending on which team wrote the endpoint, which makes onboarding new engineers slower than it should be.

None of this is visible in a demo, so it competes poorly against feature requests for planning time. But the cost shows up as incident response hours, slower onboarding, and CI time that adds up across every engineer, every day.

I want to fix the payments retry logic in the first three weeks, since it's tied to actual outages. Spend four weeks parallelizing and trimming the test suite. Use the remaining time to consolidate the gateway's auth code into one pattern and document it.

I'm asking for a firm commitment, not a "when things are slow" allowance, because that time never materializes. If a quarter is too much, I'd rather cut scope to the payments fix and the test suite than spread thin across all three.

Happy to walk through the incident data or the test suite timing in more detail.
