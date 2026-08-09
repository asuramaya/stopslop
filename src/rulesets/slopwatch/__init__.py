"""Contract surface for the slopwatch ruleset -- see lint.py for the actual
checks and the module docstring there for why this ruleset exists (proving
stopslop's plugin contract generalizes beyond ASD-STE100).

CAPABILITIES has no "word_lookup": slopwatch has no real external standard
to look a single word up against, so it implements none of that contract --
proof the optional-capability design needs no stub methods for a ruleset
that doesn't use them.

It DOES have "terms". Five of its checks (weasel_attribution,
marketing_adjective, filler_verb, marketing_cliche, stock_adverb) are
fundamentally "match text against a list of words or phrases", and a
project can extend any of them. That used to be a separate capability
called "wordlists", distinct from ste100's "glossary" -- but the two were
never different concepts, only opposite POLARITIES of one (deny here, allow
there), named differently because ste100 was written first. Both are term
lists now; see lint.py's TERM_LISTS and core/terms.py.
"""
from rulesets.slopwatch import lint
from core import config as _core_config, paths, terms as _terms

TERM_LISTS = lint.TERM_LISTS

RULESET_ID = "slopwatch"
RULESET_NAME = "slopwatch"
CAPABILITIES = frozenset({"terms", "checks", "check_config"})

TRACKED_FILES = ["lint.py"]

# Each check is TWO facts: what it catches, and what to do instead. They used
# to be one prewritten sentence per check, in the coaching voice the
# .claude/<ruleset>-memory.md primer wants ("X keeps showing up -- do Y"),
# because the coaching primer was the only consumer when they were written.
#
# The dashboard's Checks table then reused the same strings under a "what it
# catches" heading, and 37 of the fleet's 43 checks rendered as one sentence
# template repeating down a column -- a slop detector whose own configuration
# screen was templated filler. The coaching frame is right where it came from
# and wrong here: the primer prefixes each line with a real count ("(12x) ..."),
# which is what makes "keeps showing up" a claim rather than boilerplate.
#
# So the sentence is not stored; each consumer composes its own from the two
# facts. Note what did NOT happen: no second string was added beside the first.
# One string carrying two facts became two fields carrying one each.
CHECKS = {
    "filler_opener": ("Throat-clearing openers: \"needless to say\", "
                      "\"at the end of the day\"",
                      "state the point directly from the first sentence"),
    "stock_adverb": ("Standalone filler adverbs: undoubtedly, arguably, "
                     "notably, importantly, ultimately",
                     "most add nothing; cut them unless one is carrying "
                     "real emphasis"),
    "colon_reveal": ("Short buildup, then a reveal: \"The best part: "
                     "it learns.\"",
                     "state it as a plain sentence"),
    "binary_contrast": ("The \"it's not X, it's Y\" construction",
                        "just state Y"),
    "em_dash_cluster": ("Em dashes clustering in one document",
                        "most drafts need 0-2; use commas, periods or "
                        "parentheses for the rest"),
    "weasel_attribution": ("Unnamed authority: \"studies show\", "
                           "\"experts agree\"",
                           "name the actual source, or cut the claim"),
    "entity_encoded_punctuation": ("An em dash, section sign or middle dot "
                                   "written as an HTML entity",
                                   "write the plain character instead"),
    "bold_bullet_lead": ("A bolded word opening a list item as a per-item tag",
                         "reserve bold for a rare callout"),
    "id_label_lead": ("Fake ID tags opening list items: \"R-1.\", \"US-01\"",
                      "number the list plainly instead"),
    "not_just_x_but_y": ("The \"not just X but Y\" construction",
                         "make the point once"),
    "vague_intensifier": ("Vague intensifiers with no number behind them: "
                          "very, really, quite, significantly",
                          "say how much, or cut the word"),
    "emoji_in_prose": ("Emoji or decorative checkmarks in body text",
                       "cut them"),
    "marketing_adjective": ("Marketing adjectives: seamless, robust, "
                            "cutting-edge",
                            "say what is actually true"),
    "filler_verb": ("Filler verbs: leverages, facilitates, unlocks",
                    "use a plain verb, or cut the sentence"),
    "marketing_cliche": ("Marketing cliches: \"hidden gem\", "
                         "\"let's dive in\"",
                         "say the specific thing instead"),
    "solicit_criticism": ("Fake-humility feedback requests: \"would love "
                          "your feedback on this\"",
                          "cut them"),
    "unearned_profundity": ("Dramatic turning points with nothing concrete "
                            "behind them: \"Everything changed.\"",
                            "name the actual event, or cut it"),
    "dramatic_fragmentation": ("One-line dramatic fragments: \"That's it. "
                               "That's the whole thing.\"",
                               "cut them, the preceding sentence already "
                               "made the point"),
    "canned_question_answer": ("A short rhetorical question with a canned "
                               "answer",
                               "collapse into one direct statement"),
    "negative_listing": ("The \"Not X. Not Y.\" listing construction",
                         "state the point once"),
    "terminology": ("A banned synonym of one of this project's canonical "
                    "terms, per its declared lexicon",
                    "one word, one meaning: use the canonical term the "
                    "word's own note names"),
    "identifier_in_prose": ("A snake_case identifier written as plain prose",
                             "name it in words, or mark it as inline code"),
}


def lint_and_gate(text, *, context=None, file_path=None):
    return lint.lint_and_gate(text, context=context, file_path=file_path)


def blocking_semantic_flags(semantic_flags):
    return lint.blocking_semantic_flags(semantic_flags)


def apply_mechanical_fixes(text, file_path=None):
    return lint.apply_mechanical_fixes(text, file_path=file_path)


def stats():
    # Derived, not a hand-maintained sentence -- the count in this string
    # drifted the moment terminology arrived, exactly the class of "second
    # copy of a fact" this codebase keeps deleting.
    return {"checks": f"{len(lint.ALL_CHECK_IDS)} "
                       f"({', '.join(sorted(lint.ALL_CHECK_IDS))})"}


def list_checks():
    """Every check this ruleset can run: what it catches, what to do
    instead, and whether it's currently enabled -- the modularity surface
    the dashboard's Checks table and `stopslop.py checks` both read.

    `catches` and `instead` are returned as separate fields, never
    pre-joined into a sentence, so each caller writes prose in its own
    voice: the dashboard is describing a setting, the coaching primer is
    reporting a repeat offence with a count attached. See CHECKS above."""
    project_root = paths.find_project_root(__file__)
    disabled = set(_core_config.disabled_checks(project_root, RULESET_ID))
    return {
        check_id: {"catches": CHECKS.get(check_id, ("", ""))[0],
                   "instead": CHECKS.get(check_id, ("", ""))[1],
                   "enabled": check_id not in disabled}
        for check_id in sorted(lint.ALL_CHECK_IDS)
    }


def set_enabled_checks(check_ids):
    """Enable exactly this set of checks for this project (disables every
    other known check) -- same "caller sends the full desired-enabled
    set" shape as set_enabled_glossary_packs, validated against the real
    check registry first."""
    unknown = set(check_ids) - lint.ALL_CHECK_IDS
    if unknown:
        raise ValueError(f"unknown check id(s): {sorted(unknown)} -- "
                          f"known: {sorted(lint.ALL_CHECK_IDS)}")
    disabled = sorted(lint.ALL_CHECK_IDS - set(check_ids))
    project_root = paths.find_project_root(__file__)
    _core_config.save_disabled_checks(project_root, RULESET_ID, disabled)


def set_checks_enabled(states):
    """Turn the named checks on or off, leaving every other check alone --
    {check_id: bool}. Merge semantics, the same shape set_check_config has, and
    the counterpart to set_enabled_checks's replace semantics: see
    core.config.merge_disabled_checks for which callers need which, and for
    the silent-mass-disable bug that made the distinction worth a second
    method rather than a comment."""
    unknown = set(states) - lint.ALL_CHECK_IDS
    if unknown:
        raise ValueError(f"unknown check id(s): {sorted(unknown)} -- "
                          f"known: {sorted(lint.ALL_CHECK_IDS)}")
    project_root = paths.find_project_root(__file__)
    _core_config.merge_disabled_checks(project_root, RULESET_ID, states)


def list_check_config():
    """Every check's own {threshold, action}: its current effective value
    and its built-in default -- read fresh each call, same as
    list_checks() (see lint._check_config()'s own docstring for why no
    caching is needed here). The modularity surface the dashboard's
    Checks table (threshold/action columns) and `stopslop.py checks`
    both read."""
    current = lint._check_config()
    return {check_id: {"threshold": spec["threshold"], "action": spec["action"],
                        "default_threshold": lint.DEFAULT_CHECK_CONFIG[check_id]["threshold"],
                        "default_action": lint.DEFAULT_CHECK_CONFIG[check_id]["action"]}
            for check_id, spec in current.items()}


def set_check_config(check_id, threshold=None, action=None):
    """Set one check's threshold and/or action, leaving whatever it
    doesn't name alone -- a caller tuning one field shouldn't have to
    already know or resend the other. Validated against the real check
    registry and the closed block/warn choice before anything is
    written."""
    if check_id not in lint.ALL_CHECK_IDS:
        raise ValueError(f"unknown check id {check_id!r} -- "
                          f"known: {sorted(lint.ALL_CHECK_IDS)}")
    if threshold is not None and (not isinstance(threshold, int)
                                   or isinstance(threshold, bool) or threshold < 1):
        raise ValueError(f"threshold must be a whole number >= 1, got {threshold!r}")
    if action is not None and action not in ("block", "warn"):
        raise ValueError(f"action must be 'block' or 'warn', got {action!r}")
    project_root = paths.find_project_root(__file__)
    spec = dict(_core_config.check_config(project_root, RULESET_ID).get(check_id, {}))
    if threshold is not None:
        spec["threshold"] = threshold
    if action is not None:
        spec["action"] = action
    _core_config.save_check_config(project_root, RULESET_ID, check_id, spec)


def list_term_lists(file_path=None):
    """Every term list this ruleset owns, with its polarity and per-layer
    counts -- the modularity surface the dashboard's Vocabulary tab and
    `stopslop.py terms` both read. Identical shape across all three
    rulesets now, which is the whole point of core/terms.py."""
    return _terms.list_term_lists(RULESET_ID, TERM_LISTS,
                                   paths.find_project_root(__file__),
                                   file_path=file_path)


def add_term(list_id, term, note="", force=False):
    """Add one term to a list's project layer. No validator: these lists
    have no external standard to check a word against, so `force` is
    accepted (for one uniform signature across rulesets) and unused."""
    return _terms.add_term(RULESET_ID, TERM_LISTS,
                            paths.find_project_root(__file__),
                            list_id, term, note=note, force=force)


def remove_term(list_id, term):
    return _terms.remove_term(RULESET_ID, TERM_LISTS,
                               paths.find_project_root(__file__), list_id, term)
