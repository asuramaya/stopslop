# What customers say

**Kestrel Health, platform team.** "We moved 14 TB/day off our old stack after a Tuesday outage where the search index fell 40 minutes behind and nobody knew. The thing that sold us was not the ingest rate. It was that the query planner tells you when a result set is partial, so an on-call engineer stops trusting an empty graph."

**Ravi Krishnamurthy, SRE at Loomfield Logistics.** "Our retention bill dropped from about $31k a month to $9k, mostly because we stopped shipping debug logs from staging into hot storage and the tiering rules made that easy to see. Setup took me an afternoon and one support ticket, which they answered in under an hour."

**Dana Whitlock, infrastructure lead at Arbor Financial.** "Honest version: the first migration was rough. Our custom syslog format needed a parser we had to write ourselves, and the docs for that were thin at the time. They've since rewritten that page. Eighteen months in, we have not lost a log line, and our audit team pulls its own queries without asking us."

**Toyin Adeyemi, staff engineer at Pellucid.** "I care about one number: time from alert firing to seeing the log that explains it. It used to be six or seven minutes of tab-switching. Now it's under thirty seconds, because the trace ID links straight through."
