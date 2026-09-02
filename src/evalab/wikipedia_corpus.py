#!/usr/bin/env python3
"""A second human control, in a genre that is not code documentation.

The first control -- CPython docstrings and package documentation -- is
code documentation, and the discrimination command said so in its own
output: that corpus is full of identifiers and colons whatever wrote it.
Condemning `colon_reveal` or `identifier_in_prose` on that evidence
alone would be cutting a real check because of a confound.

This builds a second control from Wikipedia article text at revisions
dated BEFORE 2022, which is expository human prose with none of code
documentation's habits. The date bound is the point: an article's
current text may well have been edited by a model.

Two controls do not make a confound disappear. They make it VISIBLE. A
check that fires equally on both genres is far harder to explain away
than one that fires equally on either alone, and the rule this enables
is the honest one: condemn a check only when every control agrees.

Wikipedia text is CC BY-SA. Nothing is vendored here for exactly the
reason the stdlib corpus is not: what ships is the builder and a
manifest -- titles, revision ids, word counts, a hash -- so a rebuilt
corpus can be shown to be the one a published number came from, with
attribution intact and no redistribution.

Needs network. Offline, build the stdlib corpus and say which control
the numbers came from.
"""
import html.parser
import json
import re
import urllib.parse
import urllib.request

API = "https://en.wikipedia.org/w/api.php"
USER_AGENT = ("stopslop-evalab/1.0 (evaluation control corpus; "
               "https://github.com/asuramaya/stopslop)")
BEFORE = "2022-01-01T00:00:00Z"

# Expository articles with substantial prose, chosen to span registers
# rather than one subject area. Fixed and sorted so the corpus is
# reproducible rather than whatever a search happened to return.
DEFAULT_TITLES = (
    "Bicycle", "Cartography", "Coffee", "Dam", "Domestication",
    "Fermentation", "Glacier", "Harbor", "Irrigation", "Jazz",
    "Lighthouse", "Monsoon", "Papermaking", "Pottery", "Printing press",
    "Railway signalling", "Sailing", "Seismology", "Textile", "Typography",
    "Vaccination", "Watermill", "Weaving", "Windmill",
)


class _TextExtractor(html.parser.HTMLParser):
    """Paragraph text only. Wikipedia's rendered HTML carries tables,
    infoboxes, references and navigation that are not prose, and
    measuring them would be measuring MediaWiki rather than a writer."""

    SKIP = {"table", "style", "script", "sup", "figure", "figcaption"}

    def __init__(self):
        super().__init__()
        self._depth_skipped = 0
        self._in_paragraph = False
        self._buffer = []
        self.paragraphs = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._depth_skipped += 1
        elif tag == "p" and not self._depth_skipped:
            self._in_paragraph = True
            self._buffer = []

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._depth_skipped:
            self._depth_skipped -= 1
        elif tag == "p" and self._in_paragraph:
            self._in_paragraph = False
            text = re.sub(r"\s+", " ", "".join(self._buffer)).strip()
            if len(text.split()) >= 20:
                self.paragraphs.append(text)

    def handle_data(self, data):
        if self._in_paragraph and not self._depth_skipped:
            self._buffer.append(data)


def _get(params, timeout=30):
    url = f"{API}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def revision_before(title, before=BEFORE, timeout=30):
    """The newest revision id of `title` older than `before`, or None."""
    data = _get({"action": "query", "prop": "revisions", "titles": title,
                  "rvlimit": 1, "rvstart": before, "rvdir": "older",
                  "rvprop": "ids|timestamp", "format": "json",
                  "formatversion": 2}, timeout=timeout)
    pages = data.get("query", {}).get("pages", [])
    for page in pages:
        for revision in page.get("revisions", []):
            return revision["revid"], revision["timestamp"]
    return None


def article_text(revid, timeout=30):
    data = _get({"action": "parse", "oldid": revid, "prop": "text",
                  "format": "json", "formatversion": 2}, timeout=timeout)
    parser = _TextExtractor()
    parser.feed(data.get("parse", {}).get("text", ""))
    return "\n\n".join(parser.paragraphs)


def fetch(titles=DEFAULT_TITLES, before=BEFORE, min_words=300, timeout=30):
    """[(label, text)] for each title at its newest pre-`before` revision.

    The label carries the revision id, so a manifest names not just which
    articles were used but exactly which text.
    """
    entries = []
    for title in sorted(titles):
        found = revision_before(title, before=before, timeout=timeout)
        if not found:
            continue
        revid, timestamp = found
        text = article_text(revid, timeout=timeout)
        if len(text.split()) < min_words:
            continue
        entries.append((f"wikipedia/{title}@{revid} ({timestamp})", text))
    return entries
