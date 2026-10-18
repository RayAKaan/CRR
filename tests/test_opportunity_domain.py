from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from crr.domain.errors import DomainError
from crr.domain.opportunity import Opportunity, OpportunityStatus
from crr.domain.quantity import Quantity

NOW = datetime(2026, 10, 18, 12, tzinfo=UTC)


def make_opportunity(status: OpportunityStatus = OpportunityStatus.DRAFT) -> Opportunity:
    return Opportunity(
        id="opp_1",
        organization_id="org_a",
        route_candidate_id="route_1",
        candidate_set_fingerprint="a" * 64,
        source_resource_state_id="rst_1",
        source_resource_state_version=1,
        target_demand_id="dem_1",
        target_demand_version=1,
        route_provenance={"source": "test"},
        advisory_provenance=None,
        economic_model_id=None,
        economic_model_version=None,
        commercial_perspective=None,
        currency=None,
        quantity=Quantity(Decimal("10.000"), "kg", "1"),
        valid_from=NOW,
        valid_until=datetime(2026, 10, 20, 12, tzinfo=UTC),
        status=status,
        version=1,
        created_by="act_a",
        provenance={"source_type": "TEST"},
        created_at=NOW,
        updated_at=NOW,
    )


def test_opportunity_lifecycle_is_explicit_and_versioned():
    item = make_opportunity()
    opened = item.transition(OpportunityStatus.OPEN)
    assert opened.status is OpportunityStatus.OPEN
    assert opened.version == 2

    with pytest.raises(DomainError):
        opened.transition(OpportunityStatus.DRAFT)


def test_terminal_opportunity_cannot_transition():
    item = make_opportunity(OpportunityStatus.CLOSED)
    with pytest.raises(DomainError):
        item.transition(OpportunityStatus.OPEN)


def test_opportunity_rejects_invalid_validity_window():
    with pytest.raises(DomainError):
        replace(make_opportunity(), valid_until=NOW)
