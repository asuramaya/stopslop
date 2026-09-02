# What We Shipped, and What It Cost Us

Twelve months ago we had a deploy process that took forty minutes and required someone to sit and watch it. Priya rebuilt it in March. Deploys now take four minutes and nobody watches them. That change alone bought back roughly ninety engineer-hours over the year.

The migration off the legacy job queue took longer than the two sprints we budgeted. It took five. Marcus found the reason in week three: sixteen services wrote to the queue directly, and eleven of those had no owner listed anywhere. We tracked down owners for nine. Two we deleted after nobody claimed them for a month.

On-call got better. Pages dropped from 34 a month in January to 9 in November. Most of that came from Dana's work on retry logic in the payments path, which had been generating the same three alerts since 2023.

We also missed things. The search reindex project sat untouched from June to October because we kept pulling people onto customer escalations. Sarah raised this in three separate retros before we acted on it. We should have listened the first time.

Next year the queue migration finishes, and we finally staff search reindexing with two people instead of borrowing whoever is free.

Thanks to everyone who reviewed a PR at 11pm, wrote the runbook nobody wanted to write, or sat on a bridge call for three hours. Ravi did all three in the same week in August.
