#!/usr/bin/env python3
"""The fixed prompt set.

Chosen to be the writing this tool actually meets: documentation, an
incident write-up, an error message, a design note. Each asks for real
content rather than a topic to riff on, because a vague prompt invites
padding and would flatter the gate -- padding is exactly what these
checks catch, so the ungated arm would look bad for a reason that has
nothing to do with the gate.

None of them mentions style, tone, or any check. A prompt that said
"write plainly" would prime both arms and hide the effect being
measured.

Keep this list stable. Changing a prompt invalidates every recording and
every past result, and a moving prompt set is how an evaluation quietly
becomes a demo.
"""

PROMPTS = [
    {
        "id": "readme-section",
        "text": "Write the 'Configuration' section of a README for a "
                 "command-line tool called qcache that caches SQL query "
                 "results on local disk. It has three settings: a cache "
                 "directory, a maximum size in megabytes, and a time to "
                 "live in seconds. Around 200 words.",
    },
    {
        "id": "incident-report",
        "text": "Write an incident report for this: a deploy at 14:05 UTC "
                 "shipped a database migration that dropped an index used "
                 "by the login query. Login latency went from 40ms to 9s. "
                 "Nobody noticed for 25 minutes because the alert only "
                 "fired on error rate, not latency. A rollback at 14:32 "
                 "fixed it. Around 250 words.",
    },
    {
        "id": "error-message-docs",
        "text": "A tool fails with 'error: lock held by another process'. "
                 "Write the documentation entry a user finds when they "
                 "search that string: what it means, the two situations "
                 "that cause it, and what to do in each. Around 200 words.",
    },
    {
        "id": "design-note",
        "text": "Write a short design note arguing for storing user "
                 "sessions in a signed cookie instead of a server-side "
                 "session table, for a service with about 50000 daily "
                 "users. Include the main drawback of the choice you "
                 "argue for. Around 250 words.",
    },
    {
        "id": "runbook",
        "text": "Write a runbook for rotating the TLS certificate on a "
                 "load balancer: how to tell it is close to expiry, how "
                 "to request and install the replacement, how to verify "
                 "it took effect, and how to roll back. Around 250 words.",
    },
    {
        "id": "api-changelog",
        "text": "Write the changelog entry for version 3.0 of a REST API "
                 "that removes the /v1/users/{id}/friends endpoint, "
                 "replaces it with /v2/users/{id}/connections which "
                 "returns a paginated response, and changes the date "
                 "format from Unix timestamps to ISO 8601. Around 200 "
                 "words.",
    },
]


def by_ids(ids=None):
    if not ids:
        return list(PROMPTS)
    wanted = set(ids)
    chosen = [p for p in PROMPTS if p["id"] in wanted]
    unknown = wanted - {p["id"] for p in PROMPTS}
    if unknown:
        raise ValueError(f"unknown prompt id(s): {sorted(unknown)}")
    return chosen
