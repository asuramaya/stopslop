Payments migration is done, moved off the old queue onto Kafka. Found a message-ordering bug in staging, so testing ran three days over, but it's been solid since we cut over August 28.

Maria Chen (backend) starts September 8, Tom Okafor (infra) starts September 15. Two weeks pairing on-call before they take their own shifts.

Offline-sync is now due October 6, not September 22. The extra Kafka testing kept two engineers off it three extra days, and that work is sequential, handing it off now would cost more time than it saves.

Thanks to Priya and Jake for covering on-call this month.

We'll onboard Maria and Tom, ship offline-sync, and start the Postgres upgrade next month.
