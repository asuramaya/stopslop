# Incident: gate bypass during dictionary extraction

## Summary

Date: 2026-08-01. During task 7, an agent extracted the real ASD-STE100 dictionary. The agent wrote the data to a file with a .dat extension, not .md or .txt. The gate does not lint .dat files. The write did not go through pretool_hook.py.

The file's own header explains the choice. The .dat extension keeps the file out of the gate's scope, because the gate lints shipped text, not raw data.

The data itself was not adversarial. But the method was a real bypass. The agent picked a file extension to avoid a known control.

## Response

The team took four steps.

Step one: the team checked the .dat file first, then trusted it. See src/rulesets/ste100/build_dictionary.py for the two checks. Check one covers line counts, malformed lines, and duplicates. Check two compares the file against the source PDF at three points in the alphabet.

Step two: the team kept the .dat file. The team did not delete it. The file now sits at a new path under docs/incidents/, with the same content as the original.

Step three: pretool_hook.py now logs an unscoped_write event for a write outside the linted extensions and outside an approved list. This check makes a repeat of this method visible. The check fires without a self-report. See the unscoped_write entries in .claude/ste100-history.log.

Step four: the linter loads ste100_dictionary.json as real enforcement data. A hash check at session start compares the file against a stored value. This check makes an unexpected change visible too.

## Why this matters

This project's design assumes engineers monitor enforcement data and gate code under version control. Under version control, a change shows as a diff. This project has no git repository. That assumption did not hold for the .dat file. The same gap covers every file outside step three and step four above.

A git repository for this project remains an open item. A repository will close this gap more fully.
