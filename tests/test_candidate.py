import unittest
from pathlib import Path

from models import Order, OrderEvent, Refund, Snapshot
from run import AS_OF, query_summary
from solution import reconcile_orders


QUERY = (Path(__file__).resolve().parents[1] / "analysis.sql").read_text(encoding="utf-8")


class TestCandidate(unittest.TestCase):
    """Add one Python test and one SQL test with small, hand-calculated examples."""
