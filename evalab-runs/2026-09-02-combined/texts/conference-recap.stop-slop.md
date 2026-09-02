Four of us flew to Austin for RenderATX last week. We came back with a list of things we had wrong.

Priya sat in on the incident review session and cornered the speaker afterward. His team writes postmortems within 24 hours. We allow a week. He said memory decays past that point and people start narrating a story instead of a sequence. Priya tried the 24-hour version Monday on the checkout timeout, finished the timeline before lunch, and Marcus found the retry loop we missed in August.

Two booths pitched agent frameworks. We asked both for a reference customer running more than fifty thousand calls a day. Neither had one. Marcus took the collateral anyway and put a reminder on his calendar for March.

The hallway beat the stage. An engineer from a payments company drew us her staging setup on a napkin: one shared cluster, a namespace per branch, teardown on merge. Her bill dropped by half and her team stopped queueing for a free environment. Nadia brings a version of that to the platform meeting Thursday.

One talk moved me. The speaker wants teams to delete tests that have never failed in two years, on the grounds that they cost time in CI and prove nothing about the code as it stands now. I argued with him at the bar for forty minutes and I still think he is half right. We are going to measure our own suite first and see how many tests qualify.

Nadia has the full notes in Notion. Ask her for the incident review slides, since the speaker never posted them.
