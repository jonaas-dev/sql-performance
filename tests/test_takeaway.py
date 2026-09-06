"""A benchmark that shows numbers without stating what they mean is a quiz,
not a lesson. Every benchmark must close with a conclusion, and that
conclusion has to be derived from the run it just did."""
import pytest

from benchmarks.base import CostCentre, Takeaway


def test_takeaway_names_where_the_cost_is_actually_paid():
    t = Takeaway(
        verdict="Fetching 16 columns cost 5.2x more.",
        cost_centre=CostCentre.CLIENT,
        points=["98% of the gap is outside PostgreSQL"],
    )

    assert t.cost_centre is CostCentre.CLIENT
    assert "driver" in t.cost_centre.description.lower()


def test_cost_centre_distinguishes_the_database_from_the_client():
    assert CostCentre.DATABASE is not CostCentre.CLIENT
    assert "postgresql" in CostCentre.DATABASE.description.lower()


def test_takeaway_requires_at_least_one_piece_of_evidence():
    with pytest.raises(ValueError, match="evidence"):
        Takeaway(verdict="Trust me.", cost_centre=CostCentre.CLIENT, points=[])


def test_takeaway_verdict_must_not_be_empty():
    with pytest.raises(ValueError, match="verdict"):
        Takeaway(verdict="   ", cost_centre=CostCentre.CLIENT, points=["x"])
