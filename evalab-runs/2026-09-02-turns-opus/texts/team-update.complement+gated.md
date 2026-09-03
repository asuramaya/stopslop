# Reporting rewrite — where it stands

New date: 10 November. That's three weeks past the 19 October date I gave last month, about seven weeks past what we first committed to.

I set that date before anyone had opened the reporting code with the new cluster under it. Three of the nightly rollup queries now take 40+ minutes instead of 4, because they were tuned for the old planner. Sam's rewritten two; the third needs a summary table we haven't built. Also, finance's two custom reports lean on a column we dropped in the migration, so they need a backfill first.

Thanks to Marcus and Priya for splitting the whole September on-call rotation so Sam could stay off the pager.

Both slips are on me for the same reason: I priced the reporting work without accounting for what the migration would do to it. This time the rollup rewrite, the summary table, and the backfill are estimated separately with a week of slack. Sales knows. If it moves again I'll come with a scope cut, not a third date.
