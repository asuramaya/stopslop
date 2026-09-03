# codewatch on edited Python, opus

One leg of a two-model run. Six modules, each written and then changed
three times.

**The findings for both models are in
[../2026-09-03-codewatch/FINDINGS.md](../2026-09-03-codewatch/FINDINGS.md).**
Read them before quoting a number from here: the flag counts are single
digits, and the result differs by model rather than being a fact about
machine-written code.

```
python3 src/evalab/run.py --replay evalab-runs/2026-09-03-codewatch-opus/recordings \
    --prompt-set evalab-prompts/code-edited.md --ruleset codewatch \
    --enforce codewatch --complement --combine all
```
