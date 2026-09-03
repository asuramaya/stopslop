Security is everyone's job, not just the security team's.

We have three people on security and over two hundred engineers shipping code every week. When security stays a gate that one team enforces at the end, it becomes the slowest part of the pipeline, and the first thing people route around.

Most of the vulnerabilities we shipped in the past year were not exotic. Unvalidated inputs. Missing auth checks on new endpoints. Secrets committed to branches before anyone reviewed them. Every one of those was visible to the engineer who wrote the code, at the moment they wrote it.

Every team now owns the security of what it ships. Security engineering sets standards, builds tooling, and reviews the highest-risk changes. Everyone else runs the checks, reads the linters, and treats a security finding in code review the same way they treat a failing test.

This surfaces issues when they cost an hour instead of a week.

Some PRs that used to pass will get blocked on something the reviewer did not check for a month ago. That is the point. If you hit a check that seems wrong, tell us. If you find something that should be a check and is not, tell us that too.

Details on the new review requirements are in the security-review doc linked below.
