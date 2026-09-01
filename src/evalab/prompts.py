#!/usr/bin/env python3
"""The fixed prompt sets.

TWO of them, and mixing up which one a number came from would wreck any
claim built on it.

`technical` supplies real content in every prompt: a specific incident,
named settings, a concrete API change. It is the writing this tool
actually meets in a repository, so its flag rate is a fair BASE RATE.
The 2026-09-01 run measured that rate at roughly one flag per 200 words,
which is the finding that matters most about this project.

`padding` asks for register rather than content: launch copy, an opening
that explains why a topic matters, a case study. These are real tasks
people are really assigned, and they invite filler because the writer has
to manufacture the substance. This set was CHOSEN to produce flags, so
its flag rate is not a base rate and must never be quoted as one. It
exists for one purpose: to give the held-out comparison enough signal to
answer whether a blocking gate teaches writing or teaches avoidance. That
question needs text that trips the gate, and `technical` did not supply
enough of it.

Neither set mentions style, tone, or any check. A prompt that said
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


# Register rather than content. Every one is a task a real person gets
# handed, and every one leaves the writer to supply the substance, which
# is where filler comes from. Selected to produce flags: this set's flag
# rate is not a base rate for anything.
PADDING_PROMPTS = [
    {
        "id": "launch-announcement",
        "text": "Write a launch announcement blog post for a new dark "
                 "mode feature in a note-taking app. Around 250 words.",
    },
    {
        "id": "why-it-matters",
        "text": "Write the opening section of a blog post explaining why "
                 "observability matters for engineering teams. Around 250 "
                 "words.",
    },
    {
        "id": "product-page",
        "text": "Write the product page copy for a team chat application, "
                 "aimed at engineering managers who are choosing between "
                 "tools. Around 250 words.",
    },
    {
        "id": "conference-abstract",
        "text": "Write a conference talk abstract for a talk about moving "
                 "a monolith to microservices. Around 200 words.",
    },
    {
        "id": "remote-work-post",
        "text": "Write a post about what a software company learned from "
                 "a year of remote work. Around 250 words.",
    },
    {
        "id": "newsletter-intro",
        "text": "Write the introduction to a monthly engineering "
                 "newsletter whose theme this month is technical debt. "
                 "Around 200 words.",
    },
    {
        "id": "case-study",
        "text": "Write a customer case study about a company that adopted "
                 "a continuous delivery platform and now deploys more "
                 "often. Around 250 words.",
    },
    {
        "id": "strategy-vision",
        "text": "Write the vision section of an internal engineering "
                 "strategy document about investing in platform work over "
                 "the next two years. Around 250 words.",
    },
]

PROMPT_SETS = {
    "technical": PROMPTS,
    "padding": PADDING_PROMPTS,
}


def get_set(name):
    if name not in PROMPT_SETS:
        raise ValueError(f"unknown prompt set {name!r} -- "
                          f"have {sorted(PROMPT_SETS)}")
    return PROMPT_SETS[name]


def by_ids(ids=None, prompt_set="technical"):
    available = get_set(prompt_set)
    if not ids:
        return list(available)
    wanted = set(ids)
    chosen = [p for p in available if p["id"] in wanted]
    unknown = wanted - {p["id"] for p in available}
    if unknown:
        raise ValueError(f"unknown prompt id(s): {sorted(unknown)}")
    return chosen
