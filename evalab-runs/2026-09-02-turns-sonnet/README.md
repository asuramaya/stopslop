# Multi-turn documents, sonnet

One leg of a three-model run. Six documents, each written and then
edited three times, every arm at every turn.

**The findings for all three models are in
[../2026-09-02-turns/FINDINGS.md](../2026-09-02-turns/FINDINGS.md).** Six
prompts on one model clears significance on nothing; the analysis pools
18 paired observations across the three legs and treats the model as a
blocking factor.

```
python3 src/evalab/run.py --replay evalab-runs/2026-09-02-turns-sonnet/recordings \
    --prompt-set evalab-prompts/edited.md --enforce structural \
    --complement --combine all
```
