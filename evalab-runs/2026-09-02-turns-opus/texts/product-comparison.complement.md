For a team of three or four, use scheduled batch runs. A cron entry and a `SELECT ... WHERE processed_at IS NULL` query take an afternoon to write, and you can debug them by running the script by hand. A queue adds a broker to operate, a worker deployment to keep alive, and a dead-letter queue that helps only if someone checks it. That is ongoing work a team without an on-call rotation will not do.

Move a specific job to a queue when it earns the move: a user watches a spinner for it, or the batch tick takes longer than the interval between ticks. Managed platforms (Sidekiq on Heroku, Celery with SQS, your framework's built-in queue) get you there in a day, so the migration costs you a day, not a rewrite. Standing up a broker in week one for four nightly jobs wastes that week.

Make jobs idempotent from the start. It costs little while the code is fresh, it makes batch reruns safe, and it removes the hardest part of the migration when you switch.
