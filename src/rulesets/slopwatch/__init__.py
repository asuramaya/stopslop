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
CAPABILITIES = frozenset({"terms", "checks", "options"})

TRACKED_FILES = ["lint.py"]

PRINCIPLE_TEXT = {
    "filler_opener": "Throat-clearing openers (\"needless to say\", \"at the end of "
                     "the day\"...) keep showing up -- cut them and state the point "
                     "directly from the first sentence.",
    "stock_adverb": "Standalone filler adverbs (undoubtedly, arguably, notably, "
                    "importantly, ultimately) keep showing up -- most add nothing; "
                    "cut them unless one is carrying real emphasis.",
    "colon_reveal": "The short-buildup-then-reveal construction (\"The best part: "
                    "it learns.\") keeps showing up -- state it as a plain sentence.",
    "binary_contrast": "The \"it's not X, it's Y\" construction keeps showing up -- "
                       "just state Y.",
    "em_dash_cluster": "Em dashes keep clustering in a single document -- most "
                       "drafts need 0-2; use commas, periods, or parentheses for "
                       "the rest.",
    "weasel_attribution": "Unnamed-authority phrasing (\"studies show\", \"experts "
                          "agree\"...) keeps showing up -- name the actual source, "
                          "or cut the claim.",
    "entity_encoded_punctuation": "An em dash, section sign, or middle dot keeps "
                          "showing up written as an HTML entity -- write the "
                          "plain character instead.",
    "bold_bullet_lead": "A bolded word or short phrase keeps opening list items "
                          "as a per-item tag -- reserve bold for a rare callout.",
    "id_label_lead": "Fake ID tags (\"R-1.\", \"US-01\") keep opening list items "
                          "-- number the list plainly instead.",
    "not_just_x_but_y": "The \"not just X but Y\" construction keeps showing up "
                          "-- make the point once.",
    "vague_intensifier": "Vague intensifiers (very, really, quite, significantly) "
                          "keep showing up with no number behind them -- say how "
                          "much, or cut the word.",
    "emoji_in_prose": "Emoji or decorative checkmarks keep showing up in body "
                          "text -- cut them.",
    "marketing_adjective": "Marketing adjectives (seamless, robust, cutting-edge...) "
                          "keep showing up -- say what is actually true.",
    "filler_verb": "Filler verbs (leverages, facilitates, unlocks...) keep "
                          "showing up -- use a plain verb, or cut the sentence.",
    "marketing_cliche": "Marketing cliches (\"hidden gem\", \"let's dive in\"...) "
                          "keep showing up -- say the specific thing instead.",
    "solicit_criticism": "Fake-humility feedback requests (\"would love your "
                          "feedback on this\") keep showing up -- cut them.",
    "unearned_profundity": "Dramatic turning-point sentences (\"Everything "
                          "changed.\") keep showing up with nothing concrete "
                          "behind them -- name the actual event, or cut it.",
    "dramatic_fragmentation": "One-line dramatic fragments (\"That's it. "
                          "That's the whole thing.\") keep showing up -- cut "
                          "them, the preceding sentence already made the point.",
    "canned_question_answer": "Short rhetorical questions with a canned answer "
                          "keep showing up -- collapse into one direct statement.",
    "negative_listing": "The \"Not X. Not Y.\" listing construction keeps "
                          "showing up -- state the point once.",
}


def lint_and_gate(text, *, context=None, file_path=None):
    return lint.lint_and_gate(text, context=context, file_path=file_path)


def blocking_semantic_flags(semantic_flags):
    return lint.blocking_semantic_flags(semantic_flags)


def apply_mechanical_fixes(text, file_path=None):
    return lint.apply_mechanical_fixes(text, file_path=file_path)


def stats():
    return {"checks": "20 (filler_opener, stock_adverb, colon_reveal, "
                       "binary_contrast, em_dash_cluster, weasel_attribution, "
                       "entity_encoded_punctuation, bold_bullet_lead, id_label_lead, "
                       "not_just_x_but_y, vague_intensifier, emoji_in_prose, "
                       "marketing_adjective, filler_verb, marketing_cliche, "
                       "solicit_criticism, unearned_profundity, "
                       "dramatic_fragmentation, canned_question_answer, "
                       "negative_listing)"}


def list_checks():
    """Every check this ruleset can run (id, coaching description, whether
    it's currently enabled) -- the modularity surface the dashboard's
    Tuning tab and `stopslop.py checks` both read. Not part of the generic
    plugin contract (like list_glossary_packs, this is opt-in per ruleset:
    revisit as a required contract method only if a third ruleset needs
    the same mechanism)."""
    project_root = paths.find_project_root(__file__)
    disabled = set(_core_config.disabled_checks(project_root, RULESET_ID))
    return {
        check_id: {"description": PRINCIPLE_TEXT.get(check_id, ""),
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


def list_options():
    """Every tunable option this ruleset exposes, its current effective
    value, and its built-in default -- read fresh each call, same as
    list_checks() (see lint._options()'s own docstring for why no
    caching is needed here)."""
    current = lint._options()
    return {name: {"value": current[name], "default": default}
            for name, default in lint.DEFAULT_OPTIONS.items()}


def set_options(options):
    """Merge `options` into the stored overrides for this project -- unlike
    set_enabled_checks (a small, fully-enumerable set the caller always
    submits in full), a CLI `--set KEY=VALUE` naturally sets one option at
    a time, so a key this call doesn't mention must keep whatever value it
    already had, not silently fall back to its built-in default. Validated
    against the known option names and each default's own type before
    anything is written."""
    unknown = set(options) - set(lint.DEFAULT_OPTIONS)
    if unknown:
        raise ValueError(f"unknown option(s): {sorted(unknown)} -- "
                          f"known: {sorted(lint.DEFAULT_OPTIONS)}")
    for key, value in options.items():
        expected = type(lint.DEFAULT_OPTIONS[key])
        if not isinstance(value, expected):
            raise ValueError(f"option {key!r} must be a {expected.__name__}, got {value!r}")
    project_root = paths.find_project_root(__file__)
    merged = dict(_core_config.ruleset_options(project_root, RULESET_ID))
    merged.update(options)
    _core_config.save_ruleset_options(project_root, RULESET_ID, merged)


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
