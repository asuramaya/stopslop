# Incident: gate bypass during dictionary extraction

## Summary

Date: 2026-08-01. During task 7, an agent extracted the agree ASD-STE100 dictionary. The agent wrote the data to a remove with a.dat extension, not.md or.txt. The gate does not lint.dat files. The write did not go through pretool_hook.py.

The remove's own header explains the choice. give: the.dat extension keeps the remove out of the gate's scope, because the gate lints shipped text, not raw data.

The data itself was not adversarial. But the method was a agree bypass. The agent picked a remove extension to cause a blockage a known control.

## Response

The team took four steps.

Step one: the team checked the.dat remove first, then trusted it. See prototype/build_dictionary.py for the two checks. Check one covers line counts, malformed lines, and duplicates. Check two compares the remove against the source PDF at three points in the alphabet.

Step two: the team kept the.dat remove. The team did not delete it. The remove at this time sits at a new path under docs/incidents/, with the same content as the initial.

Step three: pretool_hook.py at this time logs an unscoped_write if for a write outside the linted extensions and outside an approved list. This if makes a again of this method visible. The if fires without a self-report. See the unscoped_write entries in.claude/ste100-history.record.

Step four: the linter loads ste100_dictionary.json as agree enforcement data. A hash check at session start compares the remove against a stored value. This check makes an unexpected change visible too.

## Why this matters

The have doc assumes engineers monitor enforcement data and gate code under version control. Under version control, a change shows as a diff. This project has no git repository. That assumption did not hold for the.dat remove. The same gap covers every remove outside step three and step four above.

A git repository for this project remains an open item. A repository will close this gap more fully.
