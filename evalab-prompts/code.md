## retry-decorator
Write a Python decorator `retry` that re-runs a function on exception, with a maximum attempt count and exponential backoff. Include a docstring. Around 40 lines.

## config-loader
Write a Python module that loads a JSON config file from disk, falls back to defaults when the file is missing, and validates that a `port` key is an integer between 1024 and 65535. Around 50 lines.

## lru-cache
Write a small LRU cache class in Python with `get` and `put`, backed by an OrderedDict, with a configurable maximum size. Around 45 lines.

## csv-parser
Write a Python function that reads a CSV file and returns a list of dicts, tolerating a missing trailing newline and rows with too few columns. Around 40 lines.

## rate-limiter
Write a token-bucket rate limiter class in Python, thread-safe, with a `try_acquire` method. Around 50 lines.

## path-walker
Write a Python function that walks a directory tree and returns every file matching a glob, skipping hidden directories and symlinks. Around 40 lines.

## http-client
Write a small Python wrapper around urllib that does a GET with a timeout, retries once on a 5xx, and returns parsed JSON. Around 45 lines.

## diff-summary
Write a Python function that takes two lists of strings and returns a summary of added, removed and unchanged lines. Around 40 lines.

## queue-worker
Write a Python worker that pulls items off a queue.Queue in a thread, processes each with a callback, and shuts down cleanly on a sentinel. Around 50 lines.

## schema-check
Write a Python function that validates a dict against a simple schema of {key: type}, reporting every problem rather than the first. Around 40 lines.
