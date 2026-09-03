```python
import csv
from typing import Any


def read_csv_dicts(
    path: str,
    fill: Any = None,
    encoding: str = "utf-8",
) -> list[dict[str, Any]]:
    """Read a CSV file into a list of dicts keyed by the header row.

    Short rows are padded with `fill`; extra fields land under the None key
    (same convention as csv.DictReader). A missing trailing newline, a UTF-8
    BOM, and fully blank lines are all tolerated.
    """
    with open(path, newline="", encoding=encoding) as fh:
        reader = csv.reader(fh)

        header: list[str] | None = None
        for row in reader:
            if any(cell.strip() for cell in row):
                header = [cell.strip() for cell in row]
                break
        if header is None:
            return []
        if header and header[0].startswith("\ufeff"):
            header[0] = header[0][1:]

        width = len(header)
        rows: list[dict[str, Any]] = []
        for row in reader:
            if not any(cell.strip() for cell in row):
                continue
            record: dict[str, Any] = dict(zip(header, row))
            if len(row) < width:
                for key in header[len(row):]:
                    record[key] = fill
            elif len(row) > width:
                record[None] = row[width:]
            rows.append(record)

    return rows
```

Notes on the edge cases you named:

- **Missing trailing newline** — `csv.reader` yields the last row regardless; opening with `newline=""` is what keeps embedded newlines inside quoted fields intact, which is the failure mode people actually hit here.
- **Too few columns** — padded to the header width with `fill` (default `None`; pass `""` if you'd rather have empty strings).
- Duplicate header names collapse to the last occurrence, since the record is a plain dict. If you need those preserved, say so and I'll switch the keys to `(index, name)` pairs or de-duplicate with a suffix.
