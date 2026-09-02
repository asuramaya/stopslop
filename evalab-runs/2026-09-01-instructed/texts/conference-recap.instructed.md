# What we brought back from DataCon

Six of us went to DataCon last week. Here is what stuck.

The vendor floor was quieter than last year, and the talks were less about model size. Three of the four keynotes were about eviction policies, retry budgets, and what happens when a downstream service returns 503 for nine minutes. That is a real shift from 2024, when the same stage was mostly demos.

Priya sat in on the schema evolution track and came back with a concrete change to how we version our event payloads. We have been adding optional fields and hoping consumers cope. Two teams described the same failure we hit in March, where a consumer parsed an absent field as zero and silently corrupted a rollup. Both fixed it by making the schema registry reject additive changes without an explicit default. We are going to try that in Q4.

The hallway conversations were more useful than the sessions. Marcus spent forty minutes with an engineer from a logistics company who runs the same Kafka-to-warehouse path we do at roughly ten times our volume. Their answer to backpressure was less clever than ours and had failed less often.

One thing we got wrong: we sent everyone to the same afternoon block on Tuesday and missed the entire observability track. Next year we will split up and write notes to a shared doc as we go.

The recordings go up in three weeks. Ask Priya for the schema talk; skip the opening keynote unless you want the vendor pitch.
