#!/usr/bin/env python3
"""Human technical prose, rebuilt from the local interpreter.

Every earlier round said a human baseline was the missing validation and
that no corpus was available offline. One was, sitting in the
interpreter: CPython's own stdlib module docstrings, written years before
any of this, by people, about software. Alongside them, whatever pre-LLM
`.rst`/`.md` package documentation the environment happens to hold.

The corpus is NOT committed. Those files are PSF, BSD and other
third-party licenses, and vendoring a few thousand words of someone
else's documentation to serve as a control would need a NOTICE entry per
package for no benefit. What is committed is this builder plus a
manifest: the exact sources, their word counts, and a hash of the text.
Rebuild locally and compare the manifest -- that is reproducibility
without redistribution.

Docstrings are read by parsing source with `ast`, never by importing.
Importing a few hundred stdlib modules to read their docstrings would
run their module-level code, which is a real cost and a real risk for
something this trivial.

The caveat that governs every number derived from this: stdlib
docstrings carry no markdown at all, so `bold_density`, `thematic_break`
and `title_case_heading` cannot fire there. For those three the markdown
corpus is the only fair comparison, and it is the smaller of the two.
"""
import ast
import hashlib
import os
import sys
import sysconfig

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Directories under the stdlib that are not prose worth measuring:
# tests, vendored third-party code, and generated data tables.
_SKIP_DIRS = frozenset({
    "test", "tests", "idlelib", "lib2to3", "site-packages", "dist-packages",
    "__pycache__", "encodings", "unicodedata",
})

MIN_DOCSTRING_WORDS = 30


def _walk_python(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in _SKIP_DIRS)
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                yield os.path.join(dirpath, filename)


def stdlib_docstrings(stdlib_dir=None, min_words=MIN_DOCSTRING_WORDS):
    """[(source_label, docstring)] for every substantial stdlib module.

    Sorted and deterministic, so two people on the same Python version
    build the same corpus and get the same manifest hash.
    """
    root = stdlib_dir or sysconfig.get_paths()["stdlib"]
    found = []
    for path in _walk_python(root):
        try:
            with open(path, encoding="utf-8") as f:
                tree = ast.parse(f.read())
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        doc = ast.get_docstring(tree)
        if not doc or len(doc.split()) < min_words:
            continue
        found.append((os.path.relpath(path, root), doc.strip()))
    return found


def package_docs(search_dirs=None, extensions=(".rst", ".md")):
    """Pre-LLM `.rst`/`.md` documentation from installed packages.

    Environment-dependent by nature, which is exactly why the manifest
    records every file that went in. A corpus whose contents cannot be
    named is not a control.
    """
    roots = search_dirs
    if roots is None:
        purelib = sysconfig.get_paths().get("purelib")
        roots = [purelib] if purelib and os.path.isdir(purelib) else []
    found = []
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames
                                  if d not in {"__pycache__", "tests", "test"})
            for filename in sorted(filenames):
                if not filename.endswith(extensions):
                    continue
                path = os.path.join(dirpath, filename)
                try:
                    with open(path, encoding="utf-8") as f:
                        text = f.read()
                except (OSError, UnicodeDecodeError):
                    continue
                if len(text.split()) < 100:
                    continue
                found.append((os.path.relpath(path, root), text.strip()))
    return found


def manifest(entries):
    """What a corpus is, in a form two machines can compare.

    Records each source and its word count, plus a hash over the text, so
    a rebuilt corpus can be shown to be the same one a published number
    came from -- without redistributing a word of it.
    """
    digest = hashlib.sha256()
    sources = []
    total = 0
    for label, text in entries:
        words = len(text.split())
        total += words
        sources.append({"source": label, "words": words})
        digest.update(label.encode("utf-8"))
        digest.update(text.encode("utf-8"))
    return {"documents": len(entries), "words": total,
            "sha256": digest.hexdigest(), "sources": sources}


def write_corpus(entries, out_dir):
    """One file per source, so `stopslop decay` can measure the corpus
    the same way it measures anything else."""
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for index, (label, text) in enumerate(entries):
        stem = label.replace(os.sep, "_").rsplit(".", 1)[0]
        path = os.path.join(out_dir, f"{index:04d}_{stem}.md")
        with open(path, "w") as f:
            f.write(text.rstrip() + "\n")
        written.append(path)
    return written


def build(out_dir, include_package_docs=True, wikipedia=False):
    """Build one control corpus into `out_dir`.

    `wikipedia=True` builds the NON-CODE control instead, from article
    revisions dated before 2022. Keep the genres in separate directories
    and compare a check against each: a check that fires equally on both
    is far harder to explain away than one that fires equally on either
    alone. Condemn a check only when every control agrees.
    """
    if wikipedia:
        from evalab import wikipedia_corpus
        entries = wikipedia_corpus.fetch()
    else:
        entries = [(f"stdlib/{label}", text)
                    for label, text in stdlib_docstrings()]
        if include_package_docs:
            entries += [(f"packages/{label}", text)
                         for label, text in package_docs()]
    write_corpus(entries, out_dir)
    return manifest(entries)


if __name__ == "__main__":
    import json

    argv = sys.argv[1:]
    wikipedia = "--wikipedia" in argv
    argv = [a for a in argv if not a.startswith("--")]
    target = argv[0] if argv else ("wikipedia-corpus" if wikipedia
                                     else "human-corpus")
    info = build(target, wikipedia=wikipedia)
    print(json.dumps({k: v for k, v in info.items() if k != "sources"},
                      indent=1))
    print(f"wrote {info['documents']} files to {target}/", file=sys.stderr)
