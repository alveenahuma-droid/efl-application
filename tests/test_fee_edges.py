"""Fee band edges (Annexe A): just above and at 500, 1,500 and 2,500."""
import pytest
from decimal import Decimal

import fees


@pytest.mark.parametrize("amount,expected", [
    ("500", "3.5"), ("500.01", "2.7"),
    ("1500", "2.7"), ("1500.01", "2.0"),
    ("2500", "2.0"), ("2500.01", "1.5"),
])
def test_fee_band_edges(amount, expected):
    assert str(fees.conversion_fee_percent(Decimal(amount))) == expected
