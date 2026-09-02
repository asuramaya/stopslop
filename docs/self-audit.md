# What this project's own documentation scores

Run on 2026-09-02 against the repository's own prose: the README, the
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
| **this repository's own docs** | **3.77** |
| generated, through the gate | 3.67 |
| human markdown documentation | 3.18 |
| pre-2022 Wikipedia prose | 0.52 |

The docs here sit level with human technical documentation and with the
gate's own output, and nowhere near ungated generation.

That is the claim this project makes, tested on itself, and it is worth
saying plainly what it does and does not show. It does not show that a
model wrote human-quality prose. Every one of these documents was
written by a model under this project's own gate, so the result is "the
gate's output scores like human documentation on the gate's own
metrics", which is close to circular. The Wikipedia row is there to keep
that honest: it is 0.52, six times below the human markdown corpus,
because stripped-markup encyclopedia text cannot trip a markdown check
at all. The human band is a range, not a target line.

## Where these docs are worse than human

`decay --against`, two control genres:

| check | these docs /1k | vs human markdown | verdict |
|---|---|---|---|
| bold_bullet_lead | 0.48 | fires nowhere in either control | discriminates |
| bold_density | 0.75 | 2.6x | discriminates |
| terminology | 0.22 | 22x vs Wikipedia | discriminates |
| colon_reveal | 1.99 | 1.0x | disputed |
| paragraph_uniformity | 0.48 | 1.7x | disputed |
| identifier_in_prose | 0.97 | 0.7x | disputed |

**Bold is the finding.** These documents use bold as a label at 2.6
times the rate of human markdown documentation, and `bold_bullet_lead`
-- a bolded word opening a list item as a per-item tag -- fires here and
in neither control corpus. That is the single habit this project's own
evaluation identified as the strongest signal of machine authorship, and
it is the one its own documentation still shows.

It is also a warn-level check with a threshold of 8, so nothing denied a
write. The gate did not fail; it was not asked.

## What the scan found

All 17 in-scope documents pass. Nothing would fail a live write. By
check, across every flag including non-blocking notes:

```
vocabulary: 117    colon_reveal: 37   identifier_in_prose: 18
bold_density: 14   paragraph_uniformity: 9   bold_bullet_lead: 9
terminology: 4     filler_verb: 2     thematic_break: 1
```

The 117 `vocabulary` flags are all `CONTRIBUTING.md`, which routes to
`ste100` -- a closed 875-word aerospace vocabulary reading software
prose. That check warns and never blocks, for exactly this reason.

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
