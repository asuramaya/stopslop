Engineering update — September

Nothing to report on the migration, which is the point. The old cluster's DNS comes out in October and then we stop paying for it.

Dani owns the build system now. Marcus shipped his first payments fix on the 22nd, that refund bug from June. And thanks to Ade and Vera for covering the on-call weeks nobody else could take, Labor Day included.

The reporting rewrite moved again, from mid-October to mid-November. Last month I said I'd rather move the date once than move it every month, and then I moved it again, so here's what happened. The audit found 41 stored procedures, not 25. Eleven of them write to tables no live service reads, and we can't drop those until we know who does. That was two unplanned weeks.

November comes from a real count this time, not a guess. October is still the three biggest reports.

Names and specifics still placeholders.
