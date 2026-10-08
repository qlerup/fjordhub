"""Read the space reclaimed summary emitted by Docker prune commands."""
import re
from decimal import Decimal


def reclaimed_bytes(output: str) -> int:
    matches = re.findall(
        r'^\s*(?:Total reclaimed space|Total):\s*([\d.]+)\s*(B|[KMGTPE]i?B)\s*$',
        output or '', re.IGNORECASE | re.MULTILINE,
    )
    if not matches:
        return 0
    amount, unit = matches[-1]  # Only the final summary, never the item rows.
    unit = unit.upper()
    power = 0 if unit == 'B' else 'KMGTPE'.index(unit[0]) + 1
    return int(Decimal(amount) * (1024 if 'I' in unit else 1000) ** power)
