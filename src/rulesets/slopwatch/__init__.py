"""Contract surface for the slopwatch ruleset -- see lint.py for the actual
checks and the module docstring there for why this ruleset exists (proving
stopslop's plugin contract generalizes beyond ASD-STE100).

CAPABILITIES is deliberately empty: slopwatch has no closed vocabulary and
no glossary concept, so it implements none of the optional glossary/
word_lookup contract methods -- proof that the contract's optional-
capability design needs no stub methods for a ruleset that doesn't use them.
"""
from rulesets.slopwatch import lint

RULESET_ID = "slopwatch"
RULESET_NAME = "slopwatch"
CAPABILITIES = frozenset()

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


def lint_and_gate(text, *, context=None):
    return lint.lint_and_gate(text, context=context)


def blocking_semantic_flags(semantic_flags):
    return lint.blocking_semantic_flags(semantic_flags)


def apply_mechanical_fixes(text):
    return lint.apply_mechanical_fixes(text)


def stats():
    return {"checks": "20 (filler_opener, stock_adverb, colon_reveal, "
                       "binary_contrast, em_dash_cluster, weasel_attribution, "
                       "entity_encoded_punctuation, bold_bullet_lead, id_label_lead, "
                       "not_just_x_but_y, vague_intensifier, emoji_in_prose, "
                       "marketing_adjective, filler_verb, marketing_cliche, "
                       "solicit_criticism, unearned_profundity, "
                       "dramatic_fragmentation, canned_question_answer, "
                       "negative_listing)"}
