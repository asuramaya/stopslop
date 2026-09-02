## Design philosophy

The gate knows nothing about your ruleset. It hands you text and a path, and you hand back a verdict.

Three functions, three attributes, no base class to inherit and no registry to sign into -- if the module is under `src/rulesets/` and exports the names, it loads. That narrowness is deliberate. Every field we could have put in the contract is a field some future ruleset would have to fake. STE100 blocks twelve of its thirteen checks; slopwatch blocks none of thirty-one. Neither had to argue with an interface about it.

We also keep the boring half separate from the interesting half. `apply_mechanical_fixes` handles what a script can settle -- straight quotes, doubled spaces. `blocking_semantic_flags` handles what needs a judgment call, and it is allowed to be wrong, because a warning costs a reader one second and a false denial costs them the write.

The API does not promise your checks are worth running. That is what `evalab-runs/` is for. Ship a ruleset, then measure it against a blind-rewrite control, and be ready for the answer that five of your checks never fire. Ours didn't.
