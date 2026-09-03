```python
import csv
from pathlib import Path


def read_csv_rows(path, fieldnames=None, fill=""):
    """Read a CSV file into a list of dicts.

    Handles files whose last line has no trailing newline, and rows that
    stop short of the header width -- missing values become `fill`.
    Extra columns beyond the header are collected under the key None,
    matching csv.DictReader's own convention.
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8-sig")
    if not text:
        return []
    if not text.endswith("\n"):
        text += "\n"

    reader = csv.reader(text.splitlines(True))
    header = fieldnames
    if header is None:
        try:
            header = next(reader)
        except StopIteration:
            return []
        header = [name.strip() for name in header]

    rows = []
    width = len(header)
    for fields in reader:
        if not fields or (len(fields) == 1 and not fields[0].strip()):
            continue
        row = dict(zip(header, fields))
        for name in header[len(fields):]:
            row[name] = fill
        if len(fields) > width:
            row[None] = fields[width:]
        rows.append(row)
    return rows
```
