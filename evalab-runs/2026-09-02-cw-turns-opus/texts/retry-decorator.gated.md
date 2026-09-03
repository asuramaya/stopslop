Renamed. `retry_backoff.py:6` now defines `with_retries`, the docstring example at line 10 uses the new name, and the continuation line is re-indented to the new paren column. Smoke test still passes (retries twice, then returns).

Two notes:

- `retry.py` and `retry_decorator.py` already called their decorator `with_retries`, so nothing changed there. That means all three files now export the same name with different behaviour — importing two of them into one module is a silent shadowing.
- Nothing in the repo imported `retry_backoff`, so there were no call sites to update. The only other `retry` hits under `src/` are the word in prose and test strings, not this decorator.

The consolidation offer still stands, and it's now more pointed given the name collision: pick which jitter definition survives (±band from `retry_backoff.py`, or full jitter from `retry_decorator.py`) and whether you want the logging and the `GeneratorExit` guard from `retry.py`, and I'll fold the three into one file.
