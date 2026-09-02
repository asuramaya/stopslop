# Managed Postgres or your own

Amazon charges about twice the EC2 price for an RDS instance with the same vCPU and memory. The premium buys an on-call team you do not meet. They patch the minor version and keep your WAL archive honest enough that point-in-time recovery works at 3am on a holiday.

Run Postgres yourself and you inherit that shift. Someone on your team writes the pgBackRest config. Someone restores a 400 GB snapshot into a scratch box each quarter to prove the backups are real, because a backup you have not restored is a rumor. Budget a quarter of an engineer, indefinitely.

The trade cuts the other way on control. RDS gives you no superuser and a fixed extension allowlist, so a patched build or an unsigned extension is off the table. Aurora hides the storage layer, which means you cannot tune fsync behavior or move the WAL onto local NVMe. On your own hardware, NVMe delivers write throughput that gp3 will not reach at the same monthly spend, and you can pin shared_buffers where your workload wants it.

Cost flips around the point where your database stops fitting on one box. Below that line, the RDS markup costs less than the hours it replaces. Above it, you pay a percentage on a large number, and hiring a DBA gets cheaper than the bill.

Pick managed if your on-call rotation lacks someone who has restored a database under pressure. Pick self-hosted if you have that person and a workload the allowlist blocks.
