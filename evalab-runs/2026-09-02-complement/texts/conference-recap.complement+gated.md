# Notes from three days at StateConf

Six of us went, and we came back with more disagreement than we left with. That seems like a good sign.

The talk that stuck was Priya Raghunathan's on incident retros. Her team stopped asking "what went wrong" and started asking "what did the on-call person believe at 2am, and why was that reasonable?" Our retro template asks the first question. We're rewriting it this sprint.

The database track was mostly a rerun of last year. Two talks on the same sharding pattern, neither with numbers past a synthetic benchmark. We skipped the third and sat in the hallway with a team from a payments company who had actually run the pattern in production for eight months. They said the rebalancing cost them a weekend every quarter. That conversation was worth more than the track.

Marcus came back convinced we should move our job queue off Postgres. Dana thinks the migration would cost us four months and buy latency we don't need. They're writing it up as a two-sided doc rather than arguing it in standup, which is the right call.

There's a smaller thing worth flagging. Three separate people asked us how we handle schema changes across our read replicas, and we gave three slightly different answers. Nobody on our team is wrong, exactly, but we clearly don't have one story. That's a gap worth closing before someone external asks.

Slides for the two talks we're recommending are in the shared drive. If you want the payments-team contact, ask Dana.
