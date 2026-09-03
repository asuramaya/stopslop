```python
import csv
from pathlib import Path


def read_csv_rows(path, encoding="utf-8", fill=""):
    """Read a CSV file into a list of dicts keyed by the header row.

    Rows shorter than the header are padded with ``fill``; rows longer than
    the header keep their surplus values under the ``extras`` key. A missing
    trailing newline on the last line is handled by the csv module itself,
    but an empty or whitespace-only final line is skipped.
    """
    rows = []
    with Path(path).open("r", encoding=encoding, newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            return rows

        header = [name.strip() for name in header]
        width = len(header)

        for line_number, values in enumerate(reader, start=2):
            if not values or all(not value.strip() for value in values):
                continue

            if len(values) < width:
                values = values + [fill] * (width - len(values))
                extras = []
            else:
                extras = values[width:]
                values = values[:width]

            record = dict(zip(header, values))
            if extras:
                record["extras"] = extras
            record["_line"] = line_number
            rows.append(record)

    return rows
```
