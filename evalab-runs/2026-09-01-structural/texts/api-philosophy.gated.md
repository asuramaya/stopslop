Written for stopslop's own public API — the ruleset plugin contract and the config surface around it. Say the word if you meant a different API.

## Design philosophy

The gate knows nothing about English. It knows how to resolve a path to a ruleset, call the six members every ruleset declares, and act on the answer. Every opinion about writing lives inside a ruleset. That is why `slopwatch` and `ste100` can aim in opposite directions, one protecting a writer's voice and one erasing it on purpose, and still share the same routing, config, CLI, and dashboard.

Three rules follow.

Extension is a file, not a fork. A custom check is a Python file under `.claude/stopslop/custom_checks/`. A vocabulary pack is a word list that names its own source and license. Read them, edit them in vim, delete them outright. The gate picks up the change on the next write.

Removal is reversible. You cannot delete a built-in term, because it lives in a ruleset's source. Removing one records a suppression you can lift later. Nothing here is one-way.

A check blocks a defect and warns on a tell. `except: pass` is wrong whatever surrounds it, so it blocks. A stalling opener is only a symptom of empty writing, and blocking symptoms hands a writer a loop to iterate against until the checker goes quiet.
