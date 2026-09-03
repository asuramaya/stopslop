# Engineering update — September

The reindex pipeline slipped again. New date: 9 October, and I won't defend that hard until the schema work lands.

Two reasons. The new document schema stores facets as nested JSONB, and the old indexer flattened them on write. Rebuilding that flattening step is about eight days of work Marcus scoped last week. Then I pulled Priya and Tom onto the cluster decommission when the storage bill came in high. Right call for the month, wrong one for this date. I'd do it again.

The relevance A/B test moves to November. Nothing else is downstream.

Thanks to Dani and Marcus, who covered every on-call shift from the 8th to the 26th while the rest of us were on the decommission.

No more dates on the pipeline until Marcus has the facet-flattening step running against a full corpus snapshot. I'd rather go quiet for three weeks than move this a third time.

October: facet flattening, decommission done on the 6th, on-call rotation rewrite live on the 13th.
