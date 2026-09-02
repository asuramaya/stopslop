RDS and Cloud SQL charge two to four times what the equivalent compute and disk cost you on a plain VM. That premium buys an on-call rotation you don't have to staff.

Run Postgres yourself and you own the failure modes. You configure streaming replication, then test the failover and discover your promotion script assumes a 60-second DNS TTL. You tune autovacuum before the orders table passes 400 million rows. You store base backups off the machine that holds the data, and you restore one each quarter to prove they work. Each task costs an afternoon to build and years to keep working. Someone on your team wears the pager.

A managed service takes those afternoons back and gives you a smaller box in exchange. You lose superuser, so any extension outside the vendor's approved list is unavailable to you. The vendor schedules major-version upgrades, and you fit your maintenance window into theirs. Your slow-query debugging stops at whatever the console exposes.

Self-hosting pays off past a few terabytes, where the markup on storage alone funds a database engineer. It also pays off when you need pgvector at a version the vendor hasn't shipped, or when you have to pin the data to hardware you control for an auditor.

The honest test is headcount. If two people on your team have promoted a replica under load and want to keep that skill, run it yourself. If your last database incident ended with someone reading a wiki page written by an engineer who left, buy the managed version and spend the saved afternoons on your product.
