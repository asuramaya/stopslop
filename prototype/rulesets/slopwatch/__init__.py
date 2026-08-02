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
}


def lint_and_gate(text, *, context=None):
    return lint.lint_and_gate(text, context=context)


def blocking_semantic_flags(semantic_flags):
    return lint.blocking_semantic_flags(semantic_flags)


def apply_mechanical_fixes(text):
    return lint.apply_mechanical_fixes(text)


def stats():
    return {"checks": "6 (filler_opener, stock_adverb, colon_reveal, "
                       "binary_contrast, em_dash_cluster, weasel_attribution)"}
