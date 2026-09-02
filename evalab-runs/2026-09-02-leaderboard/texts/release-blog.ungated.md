You didn't name the library, so I used a placeholder ("Hyperion") and invented plausible 2.0 changes — swap in your real ones. Ran it through the repo's own slopwatch gate; it passes clean.

---

**Hyperion 2.0 is out.**

Most of the work went into one problem: 1.x shipped two clients, `Client` and `AsyncClient`, and they drifted. A bug fixed in one sat unfixed in the other for months. Both now run on the same request pipeline, so behavior — retries, redirects, timeouts, connection reuse — is identical whether you await or not.

Retries also moved out of the call site. Instead of passing `retries=3` to every method, you attach a policy to the client:

```python
client = hyperion.Client(
    base_url="https://api.example.com",
    retry=hyperion.Retry(attempts=4, on=[429, 503], backoff="exponential"),
)
```

The policy honors `Retry-After` headers, which 1.x ignored entirely.

Timeouts are now split into connect, read, and total, instead of one number that meant different things depending on where the request stalled.

Breaking changes worth knowing about: `Response.json` is a method now, not a property. `verify_ssl` is `verify`. Python 3.8 is gone; the floor is 3.9. The full list, with before/after pairs, lives in UPGRADING.md.

A migration script handles the mechanical parts:

```
pipx run hyperion-migrate ./src
```

It rewrites the renamed keywords and flags the call sites it cannot decide on. Run against our own codebase, about 40,000 lines, it left eleven for a human to look at.

1.x gets security fixes through June 2027, and nothing else.

Thanks to the two dozen people who filed issues against the betas. Half of this release is your bug reports.

---

~255 words. Tell me the real library and changelog and I'll redo it with actual details.
