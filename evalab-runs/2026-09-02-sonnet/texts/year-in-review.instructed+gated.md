This year we shipped fewer features than planned. Most of that was the right call.

The migration off the legacy queue took two extra months. The old system dropped messages under load, silently, and we found out from customer complaints instead of our own dashboards. Fixing that meant rewriting the retry logic and adding real observability, not adding a bigger queue. It has run in production for four months without a repeat incident.

We cut the on-call rotation from six people to four. Three services nobody owned anymore got retired.

Testing changed the most. We went from a single end-to-end suite that took forty minutes and failed for reasons unrelated to the code, to a layered setup: unit tests that run in seconds, integration tests that run on merge, and a smaller end-to-end suite that checks only the paths that break in production. CI time dropped from forty minutes to under nine.

Next year's plan is smaller in scope and harder in practice: move the billing service off the monolith without a migration window. It has to run both ways at once for a while. We have not done a cutover like that before.

None of this happened because of a single decision. When something broke, we fixed the cause instead of the symptom, even when the symptom was cheaper to fix. Keep that habit into next year.
