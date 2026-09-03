"""Read a CSV into dicts, tolerating ragged rows."""

import csv
from typing import Any


def read_csv_dicts(
    path: str,
    fill: Any = None,
    extras_key: str = "_extra",
    encoding: str = "utf-8",
) -> list[dict[str, Any]]:
    """Read `path` and return one dict per data row, keyed by the header row.

    A row with fewer fields than the header gets `fill` for the missing keys;
    a row with more fields keeps the surplus under `extras_key` as a list.
    Rows that are entirely empty are skipped, so a file with or without a
    trailing newline yields the same result. An empty file yields [].
    """
    # newline="" lets the csv module handle embedded newlines and \r\n itself.
    with open(path, "r", newline="", encoding=encoding) as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration:
            return []

        # Strip a UTF-8 BOM that survives when the caller picks plain utf-8.
        if header and header[0].startswith("﻿"):
            header[0] = header[0][1:]

        width = len(header)
        rows: list[dict[str, Any]] = []
        for fields in reader:
            if not any(field.strip() for field in fields):
                continue
            row = dict(zip(header, fields))
            for name in header[len(fields):]:
                row[name] = fill
            if len(fields) > width:
                row[extras_key] = fields[width:]
            rows.append(row)
    return rows
