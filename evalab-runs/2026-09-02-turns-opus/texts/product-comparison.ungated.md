Replacing the closing paragraph:

If you're three or four people, start with the batch. One cron entry, one script, one log to read when the pager goes off at 3am and there's no on-call rotation to read it for you. A queue costs you a broker to run, workers to keep alive, and a class of failure that only shows up under load — standing operational cost for latency nobody has asked for. Move a job to a queue the first time someone complains about waiting on it, and move only that job. The complaint is the signal. Until it arrives, the batch is the cheaper thing to own.

One knock-on: the earlier line "Rough rule: use a queue when someone is waiting on the result" now hedges against the recommendation it sets up. Cut "Rough" — "The rule: use a queue when someone is waiting on the result. Use a batch when nobody is and the volume is high."
