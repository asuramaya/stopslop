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

`padding` GREW from 8 prompts to 30 after the 2026-09-01 runs, which used
the first 8. Growing it is safe where editing one would not be: an id
already recorded still names the same prompt, so an old result and its
recordings stay valid, and result.json lists the ids a run covered.
Thirty exists because eight yielded four prompts that carried signal, and
a comparison resting on single-digit flag counts settles nothing.

Neither set mentions style, tone, or any check. A prompt that said
"write plainly" would prime both arms and hide the effect being
measured.

Keep this list stable. Changing a prompt invalidates every recording and
every past result, and a moving prompt set is how an evaluation quietly
becomes a demo.
"""
import json


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
    {
        "id": "job-posting",
        "text": "Write a job posting for a senior backend engineer at a "
                 "mid-sized fintech company. Around 250 words.",
    },
    {
        "id": "about-page",
        "text": "Write the About page for a company that makes scheduling "
                 "software for medical clinics. Around 250 words.",
    },
    {
        "id": "onboarding-welcome",
        "text": "Write the welcome page new engineers see on their first "
                 "day at a software company. Around 250 words.",
    },
    {
        "id": "product-comparison",
        "text": "Write a page comparing a managed database service with "
                 "running your own, for a technical audience choosing "
                 "between them. Around 250 words.",
    },
    {
        "id": "year-in-review",
        "text": "Write an engineering team's year in review post for an "
                 "internal blog. Around 250 words.",
    },
    {
        "id": "award-nomination",
        "text": "Write a nomination for an internal engineering award, "
                 "for a team that improved the deployment process. "
                 "Around 200 words.",
    },
    {
        "id": "open-source-readme-intro",
        "text": "Write the opening pitch section of a README for a new "
                 "open source charting library. Around 200 words.",
    },
    {
        "id": "roadmap-intro",
        "text": "Write the introduction to a public product roadmap for a "
                 "developer tools company. Around 200 words.",
    },
    {
        "id": "postmortem-culture",
        "text": "Write an internal post arguing for blameless postmortems "
                 "at a company that does not do them yet. Around 250 "
                 "words.",
    },
    {
        "id": "hiring-brand",
        "text": "Write the engineering culture section of a careers page. "
                 "Around 250 words.",
    },
    {
        "id": "webinar-invite",
        "text": "Write the invitation copy for a webinar about database "
                 "performance tuning. Around 200 words.",
    },
    {
        "id": "release-blog",
        "text": "Write a blog post announcing version 2.0 of an API "
                 "client library. Around 250 words.",
    },
    {
        "id": "customer-testimonial",
        "text": "Write a customer testimonial section for the website of "
                 "a log aggregation service. Around 200 words.",
    },
    {
        "id": "tech-debt-pitch",
        "text": "Write an internal proposal asking leadership for a "
                 "quarter of engineering time to pay down technical debt. "
                 "Around 250 words.",
    },
    {
        "id": "mentorship-post",
        "text": "Write a post about starting a mentorship program on an "
                 "engineering team. Around 250 words.",
    },
    {
        "id": "conference-recap",
        "text": "Write a recap post about what a team learned at an "
                 "industry conference. Around 250 words.",
    },
    {
        "id": "security-culture",
        "text": "Write an internal post about making security everyone's "
                 "responsibility at a software company. Around 250 words.",
    },
    {
        "id": "api-philosophy",
        "text": "Write the design philosophy section of an API's public "
                 "documentation. Around 200 words.",
    },
    {
        "id": "team-charter",
        "text": "Write the charter for a newly formed platform "
                 "engineering team. Around 250 words.",
    },
    {
        "id": "pricing-page",
        "text": "Write the copy for the pricing page of a code review "
                 "tool, covering three tiers. Around 250 words.",
    },
    {
        "id": "migration-announcement",
        "text": "Write an announcement telling customers that a service "
                 "is moving to a new platform next quarter. Around 250 "
                 "words.",
    },
    {
        "id": "developer-advocacy",
        "text": "Write a post about why a company is investing in "
                 "developer relations. Around 250 words.",
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


def load_set(path):
    """A prompt set from a file, so a run can measure YOUR writing tasks.

    Every number this project publishes comes from two prompt sets I
    wrote. That is fine as a default and useless as an answer: the
    `technical` set barely trips a check at all, the `padding` set was
    chosen to trip them, and neither is anybody else's work. A tunable
    starting point that can only be measured on the author's own prompts
    is not tunable.

    Two formats, both plain. A JSON list of {"id", "text"} objects, or a
    markdown file where each `## heading` starts a prompt and the
    heading is its id -- the second because a prompt set is writing
    tasks, and people keep writing tasks in markdown.
    """
    with open(path) as f:
        raw = f.read()
    if path.endswith(".json"):
        loaded = json.loads(raw)
        if not isinstance(loaded, list):
            raise ValueError(f"{path}: expected a JSON list of prompts")
        prompts = []
        for index, entry in enumerate(loaded):
            if not isinstance(entry, dict) or "text" not in entry:
                raise ValueError(
                    f"{path}: prompt {index} needs at least a 'text' field")
            prompt = {"id": str(entry.get("id") or f"prompt-{index}"),
                       "text": entry["text"].strip()}
            turns = entry.get("turns")
            if turns:
                if not isinstance(turns, list):
                    raise ValueError(f"{path}: prompt {index}'s 'turns' must "
                                      "be a list of follow-up requests")
                prompt["turns"] = [str(t).strip() for t in turns if str(t).strip()]
            prompts.append(prompt)
    else:
        prompts = []
        current = None
        buffer = []
        collecting = "text"

        def flush():
            if current is None:
                return
            body = "\n".join(buffer).strip()
            if collecting == "text":
                current["text"] = body
            elif body:
                current.setdefault("turns", []).append(body)

        for line in raw.splitlines():
            if line.startswith("## "):
                flush()
                if current and current.get("text"):
                    prompts.append(current)
                current = {"id": line[3:].strip().lower().replace(" ", "-"),
                            "text": ""}
                buffer, collecting = [], "text"
            elif (line.rstrip() == "###" or line.startswith("### ")) \
                    and current is not None:
                # A `### heading` under a prompt is a FOLLOW-UP TURN: the
                # next thing asked of the document once it exists. Real
                # documents are written over many turns, and a harness
                # that only measures first drafts is measuring a mode of
                # writing that mostly does not happen.
                flush()
                buffer, collecting = [], "turn"
            elif current is not None:
                buffer.append(line)
        flush()
        if current and current.get("text"):
            prompts.append(current)
    if not prompts:
        raise ValueError(
            f"{path}: no prompts found. JSON needs a list of objects with a "
            "'text' field; markdown needs '## id' headings with text under "
            "them.")
    seen = set()
    for prompt in prompts:
        if prompt["id"] in seen:
            raise ValueError(
                f"{path}: duplicate prompt id {prompt['id']!r} -- ids name "
                "rows in every report and a duplicate makes two prompts "
                "indistinguishable in the results")
        seen.add(prompt["id"])
    return prompts
