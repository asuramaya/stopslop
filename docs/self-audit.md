# What this project's own documentation scores

Run on 2026-09-02 against the repository's own prose, then re-run after acting on it: the README, the
`docs/` guides, `SECURITY.md`, the incident report, and every
`FINDINGS.md`. 16 documents, 18571 words. Reproduce with:

```
python3 stopslop.py scan README.md SECURITY.md docs/*.md evalab-runs/**/FINDINGS.md
python3 stopslop.py decay --ruleset slopwatch <those files in a directory> \
    --against <human markdown corpus> --against <wikipedia corpus>
```

A tool that measures writing should be able to say what its own writing
scores. This is that number, including the part that is unflattering.

## The headline

Structural tells per 1000 words, counting the twelve formatting checks:

| corpus | tells / 1k |
|---|---|
| generated, ungated | 13.32 |
| generated, through the gate | 3.67 |
| this repository's own docs | 3.32 |
| human markdown documentation | 3.18 |
| pre-2022 Wikipedia prose | 0.52 |

The docs here sit level with human technical documentation, and below
the gate's own output.

It is worth saying plainly what that does and does not show. It does not
show that a model wrote human-quality prose. Every one of these
documents was written by a model under this project's own gate, so the
result is "the gate's output scores like human documentation on the
gate's own metrics", which is close to circular. The Wikipedia row keeps
that honest: it is 0.52, six times below the human markdown corpus,
because stripped-markup encyclopedia text cannot trip a markdown check
at all. The human band is a range, not a target line.

## Acting on the first run of this audit

The first version of this page reported 3.77, and named one habit:
these documents used bold as a label at 2.6x the human markdown rate,
with `bold_bullet_lead` -- a bolded word opening a list item as a
per-item tag -- firing here and in neither control corpus.

That was the single habit this project's own evaluation identified as
the strongest signal of machine authorship, present in its own
documentation. The README alone carried 49 bold spans and 20 bold-led
bullets against a threshold of 8.

It now carries 3 and none. `bold_bullet_lead` fires nowhere in these
docs, and the corpus moved 3.77 to 3.32.

### The audit also found a false positive in the check

Every evaluation write-up in `evalab-runs/` tripped `bold_density`, and
every span was a TABLE CELL -- the winning number in a comparison table,
emphasised. That is ordinary human documentation practice, and counting
it as body emphasis makes a results file look like a document written in
bold labels.

`bold_density` now excludes markdown table rows. The habit it is
actually for -- bold opening a paragraph or a list item as a running
label -- lives outside tables, and `bold_bullet_lead` catches the
list-item form separately.

Which is the argument for pointing a checker at your own writing rather
than only at the text it was built to catch. The false positive was
invisible until the tool read prose full of result tables.

## What the scan found

All 17 in-scope documents pass, and `CONTRIBUTING.md` is now clean.
Nothing would fail a live write.

That file routes to `ste100` and used to carry 117 `vocabulary` flags --
a closed 875-word aerospace vocabulary reading software prose. Those are
warnings, never denials, and they were pure noise: this project's own
evaluation found `vocabulary` is 92% of every flag `ste100` produces and
that the gate drives it UP rather than down. A per-rule exemption now
turns that one check off for that one path, and `ste100`'s structural
checks -- sentence length, `-ing` forms, passive voice -- still run.

```
python3 stopslop.py rule-checks --glob CONTRIBUTING.md --disable vocabulary
```

That is the mechanism the tool has for "this check does not apply in
this context", used on its own repository rather than described in a
document.

## A gap this audit found

`.claude/*` is out of scope by default, which is correct for settings
and logs. It also meant **the skill file this project ships was never
gated by this project's own tool.** A rule now routes
`.claude/skills/*/SKILL.md` to `slopwatch`, above the blanket exemption.
Both shipped skills pass.

That is the kind of thing only a self-audit finds: the exemption was
right, its blast radius was not, and nothing would ever have reported it
because an out-of-scope file produces no output.

## What is not measured here

Whether any of this reads well. Every number counts flags. A document
that dodges all 31 checks and says nothing scores perfectly.
