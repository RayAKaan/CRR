from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from crr.domain.agreement import Agreement, AgreementStatus
from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.offer import Offer, OfferStatus
from crr.domain.quantity import Quantity

NOW = datetime(2026, 11, 3, 12, tzinfo=UTC)


def accepted_offer() -> Offer:
    return Offer(
        id="off_accepted",
        organization_id="org_a",
        opportunity_id="opp_a",
        opportunity_version=2,
        proposer_actor_id="act_seller",
        recipient_actor_id="act_buyer",
        quantity=Quantity(Decimal("10.250"), "t", "CRR-UNITS-0.1"),
        price=Decimal("125.50"),
        currency="SAR",
        delivery_terms={"incoterm": "DAP", "location_id": "loc_a"},
        timing_terms={"delivery_by": "2026-12-01"},
        route_assumptions={"route_id": "route_a", "version": 3},
        conditions={"inspection": "required"},
        valid_from=NOW,
        valid_until=datetime(2026, 12, 1, tzinfo=UTC),
        status=OfferStatus.ACCEPTED,
        version=3,
        created_by="act_seller",
        provenance={"source_type": "TEST"},
        created_at=NOW,
        updated_at=NOW,
    )


def make_agreement() -> Agreement:
    return Agreement.from_accepted_offer(
        accepted_offer(),
        agreement_id="agr_test",
        accepted_by="act_buyer",
        accepted_at=NOW,
        provenance='{"source_type":"TEST"}',
    )


def test_agreement_snapshots_accepted_offer_terms_and_provenance():
    agreement = make_agreement()
    assert agreement.status is AgreementStatus.ACTIVE
    assert agreement.offer_id == "off_accepted"
    assert agreement.offer_version == 3
    assert '"price":"125.50"' in agreement.terms_snapshot
    assert '"value":"10.250"' in agreement.terms_snapshot


def test_agreement_requires_accepted_offer():
    with pytest.raises(DomainError):
        Agreement.from_accepted_offer(
            replace(accepted_offer(), status=OfferStatus.OPEN),
            agreement_id="agr_invalid",
            accepted_by="act_buyer",
            accepted_at=NOW,
            provenance='{"source_type":"TEST"}',
        )


def test_only_recipient_can_accept_offer():
    with pytest.raises(DomainError):
        Agreement.from_accepted_offer(
            accepted_offer(),
            agreement_id="agr_invalid",
            accepted_by="act_seller",
            accepted_at=NOW,
            provenance='{"source_type":"TEST"}',
        )


def test_agreement_tenant_boundary_and_cancellation():
    agreement = make_agreement()
    with pytest.raises(TenantBoundaryError):
        agreement.validate_tenant("org_other")
    cancelled = agreement.cancel(actor_id="act_buyer", at=NOW)
    assert cancelled.status is AgreementStatus.CANCELLED
    assert cancelled.version == agreement.version + 1
    with pytest.raises(DomainError):
        cancelled.cancel(actor_id="act_buyer", at=NOW)


def test_non_party_cannot_cancel_agreement():
    with pytest.raises(DomainError):
        make_agreement().cancel(actor_id="act_other", at=NOW)


def test_agreement_expiry_is_explicit_and_versioned():
    agreement = make_agreement()
    expired = agreement.expire(at=datetime(2026, 12, 2, tzinfo=UTC))
    assert expired.status is AgreementStatus.EXPIRED
    assert expired.version == agreement.version + 1
    with pytest.raises(DomainError):
        expired.expire(at=datetime(2026, 12, 3, tzinfo=UTC))


def test_agreement_termination_requires_party_and_aware_time():
    agreement = make_agreement()
    terminated = agreement.terminate(
        actor_id="act_seller",
        at=datetime(2026, 11, 4, tzinfo=UTC),
    )
    assert terminated.status is AgreementStatus.TERMINATED
    with pytest.raises(DomainError):
        agreement.terminate(actor_id="act_outsider", at=NOW)
    with pytest.raises(DomainError):
        agreement.cancel(actor_id="act_buyer", at=datetime(2026, 11, 2, tzinfo=UTC))
