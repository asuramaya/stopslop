```python
import csv
from pathlib import Path


def read_csv_rows(path, fieldnames=None, fill=""):
    """Read a CSV into a list of dicts.

    Short rows are padded with `fill`; extra columns land under a `None`
    key the same way csv.DictReader handles them, so the caller can spot
    malformed input. A missing trailing newline is handled by the reader
    itself.
    """
    rows = []
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)

        if fieldnames is None:
            try:
                header = next(reader)
            except StopIteration:
                return rows
            fieldnames = [name.strip() for name in header]

        width = len(fieldnames)
        for record in reader:
            if not record or (len(record) == 1 and not record[0].strip()):
                continue

            if len(record) < width:
                record = record + [fill] * (width - len(record))

            row = dict(zip(fieldnames, record))
            if len(record) > width:
                row[None] = record[width:]
            rows.append(row)

    return rows
```

Notes on the edge cases:

- A file whose last line lacks `\n` needs no special handling: `csv.reader` yields that line as a normal row. The one real trap is opening the file without `newline=""`, which breaks quoted fields containing embedded newlines.
- `utf-8-sig` strips a BOM, which otherwise corrupts the first column name.
- Blank lines are skipped rather than padded into a row of empty strings; drop that branch if you want them preserved.
- Rows that are too long keep their overflow under the `None` key instead of being silently truncated.
