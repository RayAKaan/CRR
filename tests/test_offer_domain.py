from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.offer import Offer, OfferStatus
from crr.domain.quantity import Quantity

NOW = datetime(2026, 10, 18, 12, tzinfo=UTC)


def make_offer(status: OfferStatus = OfferStatus.DRAFT) -> Offer:
    return Offer(
        id="off_test",
        organization_id="org_a",
        opportunity_id="opp_a",
        opportunity_version=1,
        proposer_actor_id="act_proposer",
        recipient_actor_id="act_recipient",
        quantity=Quantity(Decimal("10.000"), "t", "CRR-UNITS-0.1"),
        price=Decimal("125.50"),
        currency="USD",
        delivery_terms={"incoterm": "DAP"},
        timing_terms={"window": "2026-11"},
        route_assumptions={"opportunity_version": 1},
        conditions={},
        valid_from=NOW,
        valid_until=datetime(2026, 12, 1, tzinfo=UTC),
        status=status,
        version=1,
        created_by="act_proposer",
        provenance={"source_type": "TEST"},
        created_at=NOW,
        updated_at=NOW,
    )


def test_offer_lifecycle_is_explicit_and_versioned():
    opened = make_offer().transition(OfferStatus.OPEN)
    assert opened.status is OfferStatus.OPEN
    assert opened.version == 2
    accepted = opened.transition(OfferStatus.ACCEPTED)
    assert accepted.version == 3
    with pytest.raises(DomainError):
        accepted.transition(OfferStatus.OPEN)


def test_offer_tenant_boundary_is_explicit():
    with pytest.raises(TenantBoundaryError):
        make_offer().validate_tenant("org_b")


def test_offer_rejects_invalid_window():
    with pytest.raises(DomainError):
        replace(make_offer(), valid_until=datetime(2026, 10, 18, 11, tzinfo=UTC))
