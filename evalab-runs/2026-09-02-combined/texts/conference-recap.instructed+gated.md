Four of us went to KubeCon in Atlanta last week. Here is what stuck.

The hallway track beat the sessions, again. We came in with a list of talks and left with a list of names. A platform engineer from a mid-size logistics company spent forty minutes walking us through how they killed their internal PaaS after two years and moved everyone to raw Helm charts plus a good template repo. They argued that the abstraction cost more to maintain than the thing it abstracted. We had been sketching a similar internal layer since June. That conversation saved us a quarter.

Two talks were worth the trip. Natasha Ridley's session on eBPF-based network policy showed real numbers from a 4,000-node cluster, including where the approach falls apart under high pod churn. And a lightning talk on OpenTelemetry collector configs convinced Marcus that our current sampling strategy is throwing away the traces we most need.

The vendor floor was thinner than last year and more honest about it. Fewer AI banners than we expected. Several booths we visited had shipped nothing since 2024 and said so when asked directly.

Two things change as a result. We are reviewing the internal platform proposal against the logistics team's postmortem before we write more code, and Marcus is auditing our tail sampling rules this sprint.

Nothing at the conference moved us on the service mesh question, so that decision stays where it was. We heard three incompatible recommendations and no data that separated them.

Slides and our notes are in the shared drive under conferences/2026-kubecon.
