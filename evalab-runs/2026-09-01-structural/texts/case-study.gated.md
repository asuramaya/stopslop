## How Renwick Logistics got from Thursday nights to Tuesday afternoons

Renwick Logistics sells freight-tracking software to about 400 carrier fleets. Until early 2024, they shipped their own product once every three weeks, on a Thursday night, with four engineers on a bridge call and a rollback plan nobody had rehearsed.

"The release wasn't the scary part," says Dana Oyelaran, Renwick's director of platform engineering. "The scary part was the three weeks of changes piled up behind it."

They moved to Kestrel CD in February 2024. The first month went to unglamorous work. They containerized two Rails services, converted 1,100 lines of Jenkins Groovy into declarative pipelines, and finally wrote the integration tests the old process had let them skip.

Then the numbers moved. Deploys went from 17 a year to 240 in the first twelve months. Median lead time, first commit to production, dropped from 19 days to 6 hours. Change failure rate actually rose a little, 9% to 11%. But mean time to restore fell from four hours to 22 minutes, because a bad deploy now touches one service and reverts with one command.

Oyelaran is careful about the causation. "The tool didn't fix us. It made the batch size small enough that our existing habits stopped hurting."

The pipeline count sits at 34. The two engineers who used to spend Thursdays on release duty now work on the routing engine. Next up is progressive rollout by carrier region, still manual, and the last hand-run step in the chain.
